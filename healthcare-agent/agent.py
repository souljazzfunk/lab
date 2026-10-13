#!/usr/bin/env python3
"""Healthcare doctor-finder CLI agent (closed / offline).

Usage:
  python agent.py chat  [--channel message|voice]   # 対話モード（終了時に CSAT 取得）
  python agent.py ask   "頭痛がする" [--channel voice]
  python agent.py batch samples/inquiries.jsonl      # 一括処理（Ticket 処理数を稼ぐ）
  python agent.py metrics                            # CSAT / SLA / Ticket 数
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core import DoctorIndex, Query, mask_pii, parse

JST = timezone(timedelta(hours=9))
HERE = Path(__file__).parent
DEFAULT_DATA = HERE / "sample_doctors.json"
TICKET_LOG = HERE / "data" / "tickets.jsonl"
SLA_MS = {"voice": 1000, "message": 3000}  # 一次応答の SLA 目標
HANDOFF = "担当スタッフにおつなぎします。受付番号 {tid} をお伝えください。"


def now_jst() -> str:
    return datetime.now(JST).isoformat(timespec="seconds")


def render(q: Query, index: DoctorIndex, channel: str, tid: str) -> tuple[str, str]:
    """Return (reply, outcome). outcome: resolved | escalated | clarify."""
    voice = channel == "voice"
    if q.intent == "emergency":
        return ("緊急の可能性があります。すぐに 119 番に電話してください。"
                "迷う場合は救急安心センター #7119 へ。", "escalated")
    if q.intent == "out_of_scope":
        return ("医師のご案内以外のご用件ですね。" + HANDOFF.format(tid=tid), "escalated")
    if q.intent == "unclear":
        return ("どのような症状でお困りですか？（例：頭痛、子どもの発熱、膝の痛み）"
                "診療科・性別・曜日・言語のご希望もあればお知らせください。", "clarify")
    if q.intent == "doctor_info":
        d = next(x for x in index.doctors if x["id"] == q.name)
        days = "・".join(d.get("available_days", []))
        return (f"{d['name']}先生（{d['specialty']}）は {days}曜日 に {d.get('location', '')} で診察しています。"
                + ("" if d.get("accepting_new_patients", True) else "現在、新患の受付は停止中です。"), "resolved")

    ranked, notes = index.search(q, limit=1 if voice else 3)
    if not ranked:
        return ("ご希望に合う医師が見つかりませんでした。" + HANDOFF.format(tid=tid), "escalated")
    lines = list(notes)
    for score, d in ranked:
        days = "・".join(d.get("available_days", []))
        if voice:  # 音声: 1名・1文で短く（通話時間短縮 = AHT/SLA 改善）
            lines.append(f"{d['specialty']}の{d['name']}先生をおすすめします。{days}曜日に診察しています。")
        else:
            extra = []
            if d.get("telehealth"):
                extra.append("オンライン可")
            if d.get("accepting_new_patients") is False:
                extra.append("新患受付停止中")
            extra.append("対応言語: " + "/".join(d.get("languages", [])))
            lines.append(f"- {d['name']}先生｜{d['specialty']}（{'・'.join(d.get('sub_specialties', []))}）"
                         f"｜{days}曜｜{d.get('location', '')}｜{'、'.join(extra)}")
    lines.append("この先生でご予約を進めますか？" if voice else "ご予約の際は受付番号 " + tid + " をお伝えください。")
    return ("\n".join(lines), "resolved")


class Ticket:
    def __init__(self, channel: str):
        self.id = "T" + datetime.now(JST).strftime("%m%d") + "-" + uuid.uuid4().hex[:6].upper()
        self.channel = channel
        self.created_at = now_jst()
        self.turns: list[dict] = []
        self.first_response_ms: float | None = None
        self.outcome = "open"
        self.intent = None
        self.csat: int | None = None

    def handle(self, text: str, index: DoctorIndex) -> str:
        t0 = time.perf_counter()
        # clarify の後は直前の文脈と結合して再解析（聞き直しの往復を減らす）
        ctx = " ".join([x["user"] for x in self.turns if x.get("outcome") == "clarify"] + [text])
        q = parse(ctx, index)
        reply, outcome = render(q, index, self.channel, self.id)
        ms = (time.perf_counter() - t0) * 1000
        if self.first_response_ms is None:
            self.first_response_ms = ms
        self.intent, self.outcome = q.intent, outcome
        self.turns.append({"user": text, "outcome": outcome, "at": now_jst()})
        return reply

    def close(self) -> None:
        TICKET_LOG.parent.mkdir(exist_ok=True)
        rec = {
            "id": self.id, "channel": self.channel, "created_at": self.created_at, "closed_at": now_jst(),
            "intent": self.intent, "outcome": self.outcome, "turns": len(self.turns),
            "first_response_ms": round(self.first_response_ms or 0, 2),
            "sla_met": (self.first_response_ms or 0) <= SLA_MS[self.channel],
            "csat": self.csat,
            # ローカル保存のみ。PII はマスクしてから書き込む
            "transcript": [mask_pii(x["user"]) for x in self.turns],
        }
        with TICKET_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def cmd_chat(args, index):
    tk = Ticket(args.channel)
    print(f"[{tk.id}] こんにちは。症状やご希望の先生を教えてください（終了: exit）")
    while True:
        try:
            text = input("> ").strip()
        except EOFError:
            break
        if text in {"exit", "quit", "終了"}:
            break
        if text:
            print(tk.handle(text, index))
            if tk.outcome in {"resolved", "escalated"} and tk.intent == "emergency":
                break
    if tk.turns:
        try:
            s = input("今回の対応はいかがでしたか？ 1〜5 で評価してください（Enter でスキップ）: ").strip()
            tk.csat = int(s) if s in {"1", "2", "3", "4", "5"} else None
        except EOFError:
            pass
        tk.close()


def cmd_ask(args, index):
    tk = Ticket(args.channel)
    print(tk.handle(args.text, index))
    tk.close()


def cmd_batch(args, index):
    n = 0
    for line in Path(args.file).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        tk = Ticket(item.get("channel", "message"))
        reply = tk.handle(item["text"], index)
        tk.close()
        n += 1
        print(f"--- [{tk.id}] ({tk.channel}/{tk.intent}/{tk.outcome}, {tk.first_response_ms:.1f}ms)\n"
              f"Q: {item['text']}\nA: {reply}")
    print(f"\n{n} 件処理しました")


def cmd_metrics(args, index):
    if not TICKET_LOG.exists():
        print("チケットがまだありません")
        return
    recs = [json.loads(l) for l in TICKET_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
    n = len(recs)
    resolved = sum(r["outcome"] == "resolved" for r in recs)
    escalated = sum(r["outcome"] == "escalated" for r in recs)
    sla = sum(r["sla_met"] for r in recs)
    csats = [r["csat"] for r in recs if r["csat"]]
    frt = sorted(r["first_response_ms"] for r in recs)
    print(f"集計時刻 (JST): {now_jst()}")
    print(f"処理 Ticket 数     : {n}")
    print(f"自動解決率         : {resolved / n:.0%}  (エスカレーション {escalated} 件)")
    print(f"SLA 達成率         : {sla / n:.0%}  (一次応答 p50 {frt[n // 2]:.1f}ms / max {frt[-1]:.1f}ms)")
    print(f"CSAT               : " + (f"{sum(csats) / len(csats):.2f} / 5  (回答 {len(csats)} 件)" if csats else "回答なし"))
    by = {}
    for r in recs:
        by[r["intent"]] = by.get(r["intent"], 0) + 1
    print("意図別内訳         : " + ", ".join(f"{k}={v}" for k, v in sorted(by.items(), key=lambda x: -x[1])))


def main(argv=None):
    p = argparse.ArgumentParser(description="ヘルスケア医師案内エージェント（クローズド構成）")
    p.add_argument("--data", default=str(DEFAULT_DATA), help="医師データ JSON")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("chat"); c.add_argument("--channel", choices=["message", "voice"], default="message")
    a = sub.add_parser("ask"); a.add_argument("text"); a.add_argument("--channel", choices=["message", "voice"], default="message")
    b = sub.add_parser("batch"); b.add_argument("file")
    sub.add_parser("metrics")
    args = p.parse_args(argv)
    index = DoctorIndex(args.data)
    {"chat": cmd_chat, "ask": cmd_ask, "batch": cmd_batch, "metrics": cmd_metrics}[args.cmd](args, index)


if __name__ == "__main__":
    sys.exit(main())
