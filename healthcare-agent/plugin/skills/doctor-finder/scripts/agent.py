#!/usr/bin/env python3
"""Healthcare doctor-finder CLI agent (closed / offline).

Rules mode (no LLM):
  python agent.py chat  [--channel message|voice]   # 対話モード（終了時に CSAT 取得）
  python agent.py ask   "頭痛がする" [--channel voice]
  python agent.py batch samples/inquiries.jsonl      # 一括処理（Ticket 処理数を稼ぐ）
  python agent.py metrics                            # CSAT / SLA / Ticket 数

Skill mode (Claude Code の doctor-finder スキルが呼ぶ JSON API):
  python agent.py open "<問い合わせ原文>" --channel voice   # Ticket 発行 + 緊急判定 + 抽出ヒント
  python agent.py search --specialty Pediatrics --region Tokyo --ampm am
  python agent.py doctor "Tanaka"
  python agent.py close <ticket_id> --intent search --outcome resolved [--csat 5]
  python agent.py rate  <ticket_id> 5
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core import REGION_JA, SPECIALTY_JA, DoctorIndex, Query, doctor_view, mask_pii, parse

JST = timezone(timedelta(hours=9))
HERE = Path(__file__).parent
DEFAULT_DATA = Path(os.environ.get("HC_DOCTORS_JSON", HERE / "sample_doctors.json"))
STATE_DIR = Path(os.environ.get("HC_AGENT_HOME", Path.home() / ".healthcare-agent"))
TICKET_LOG = STATE_DIR / "tickets.jsonl"
OPEN_DIR = STATE_DIR / "open"
# 一次応答の SLA 目標。rules はローカル即答、skill は LLM の思考時間込み
SLA_MS = {"rules": {"voice": 1000, "message": 3000}, "skill": {"voice": 10000, "message": 30000}}
HANDOFF = "担当スタッフにおつなぎします。受付番号 {tid} をお伝えください。"
EMERGENCY_REPLY = ("緊急の可能性があります。すぐに 119 番に電話してください。"
                   "迷う場合は救急安心センター #7119 へ。")


def now_jst() -> str:
    return datetime.now(JST).isoformat(timespec="seconds")


WD = "月火水木金土日"


def fmt_slot(s) -> str:
    return f"{s.month}/{s.day}({WD[s.weekday()]}) {s:%H:%M}"


def render(q: Query, index: DoctorIndex, channel: str, tid: str) -> tuple[str, str]:
    """Rule-based reply. Return (reply, outcome). outcome: resolved | escalated | clarify."""
    voice = channel == "voice"
    if q.intent == "emergency":
        return (EMERGENCY_REPLY, "escalated")
    if q.intent == "out_of_scope":
        return ("医師のご案内以外のご用件ですね。" + HANDOFF.format(tid=tid), "escalated")
    if q.intent == "unclear":
        return ("どのような症状でお困りですか？（例：頭痛、子どもの発熱、膝の痛み）"
                "地域・希望日時・先生の性別や言語のご希望もあればお知らせください。", "clarify")
    if q.intent == "doctor_info":
        lines = []
        for d in (x for x in index.doctors if x["id"] in q.doctor_ids):
            slots = "、".join(fmt_slot(s) for s in d["slots"][:3])
            lines.append(f"{d['name']}（{SPECIALTY_JA.get(d['specialty'], d['specialty'])}／{d.get('hospital')}）"
                         f"の空き枠: {slots}")
        return ("\n".join(lines), "resolved")

    ranked, notes = index.search(q, limit=1 if voice else 3)
    if not ranked:
        return ("ご希望に合う医師が見つかりませんでした。" + HANDOFF.format(tid=tid), "escalated")
    lines = list(notes)
    for _, d, slots in ranked:
        spec = SPECIALTY_JA.get(d["specialty"], d["specialty"])
        first = fmt_slot(slots[0]) if slots else "要確認"
        if voice:  # 音声: 1名・1文で短く（通話時間短縮 = SLA 改善）
            lines.append(f"{REGION_JA.get(d['region'], d['region'])}の{d.get('hospital')}、{spec}の"
                         f"{d['name']}をおすすめします。最短の空きは{first}です。")
        else:
            lines.append(f"- {d['name']}｜{spec}｜{d.get('hospital')}（{REGION_JA.get(d['region'], d['region'])}）"
                         f"｜評価 {d.get('rating')}｜対応言語: {'/'.join(d['languages'])}"
                         f"｜空き: {'、'.join(fmt_slot(s) for s in slots[:2]) or '要確認'}")
    lines.append("この枠でご予約を進めますか？" if voice else f"ご予約の際は受付番号 {tid} をお伝えください。")
    return ("\n".join(lines), "resolved")


class Ticket:
    def __init__(self, channel: str, engine: str = "rules"):
        self.engine = engine
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
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        rec = {
            "id": self.id, "channel": self.channel, "created_at": self.created_at, "closed_at": now_jst(),
            "intent": self.intent, "engine": self.engine, "outcome": self.outcome, "turns": len(self.turns),
            "first_response_ms": round(self.first_response_ms or 0, 2),
            "sla_met": (self.first_response_ms or 0) <= SLA_MS[self.engine][self.channel],
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
    skill = [r for r in recs if r.get("engine") == "skill"]
    if skill:
        hm = sorted(r["first_response_ms"] for r in skill)
        print(f"skill 処理時間     : p50 {hm[len(hm) // 2] / 1000:.1f}s (LLM 込み)")
    eng = {}
    for r in recs:
        eng[r.get("engine", "rules")] = eng.get(r.get("engine", "rules"), 0) + 1
    print("エンジン別         : " + ", ".join(f"{k}={v}" for k, v in eng.items()))
    print("意図別内訳         : " + ", ".join(f"{k}={v}" for k, v in sorted(by.items(), key=lambda x: -x[1])))


def emit(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=1))


def cmd_open(args, index):
    """Skill mode: issue a ticket, run deterministic triage, return extraction hints."""
    tk = Ticket(args.channel, engine="skill")
    q = parse(args.text, index)
    OPEN_DIR.mkdir(parents=True, exist_ok=True)
    (OPEN_DIR / f"{tk.id}.json").write_text(json.dumps({
        "id": tk.id, "channel": tk.channel, "created_at": tk.created_at, "t0": time.time(),
        "text": mask_pii(args.text)}, ensure_ascii=False), encoding="utf-8")
    out = {"ticket_id": tk.id, "channel": tk.channel, "emergency": q.intent == "emergency",
           "rule_hints": {k: v for k, v in vars(q).items() if k != "text" and v not in (None, [])},
           "available_specialties": index.specialties,
           "available_regions": sorted({d["region"] for d in index.doctors})}
    if q.intent == "emergency":
        out["emergency_reply"] = EMERGENCY_REPLY
    emit(out)


def cmd_search(args, index):
    bad = [s for s in args.specialty if s not in index.specialties]
    if bad:
        emit({"error": f"unknown specialty: {bad}", "available_specialties": index.specialties})
        return 2
    wd = args.weekday
    q = Query(text="", specialties=args.specialty, gender=args.gender, language=args.language,
              region=args.region, date=args.date, ampm=args.ampm, personalities=args.personality,
              weekday=None if wd is None else (WD.index(wd) if wd in WD else int(wd)))
    ranked, notes = index.search(q, limit=args.limit)
    emit({"notes": notes, "doctors": [doctor_view(d, s) for _, d, s in ranked]})


def cmd_doctor(args, index):
    emit({"doctors": [doctor_view(d) for d in index.find_by_name(args.name)]})


def cmd_close(args, index):
    f = OPEN_DIR / f"{args.ticket_id}.json"
    if not f.exists():
        emit({"error": f"open ticket not found: {args.ticket_id}"})
        return 2
    st = json.loads(f.read_text(encoding="utf-8"))
    tk = Ticket(st["channel"], engine="skill")
    tk.id, tk.created_at = st["id"], st["created_at"]
    tk.first_response_ms = (time.time() - st["t0"]) * 1000
    tk.intent, tk.outcome, tk.csat = args.intent, args.outcome, args.csat
    tk.turns = [{"user": st["text"]}] + [{"user": "(follow-up)"}] * (args.turns - 1)
    tk.close()
    f.unlink()
    emit({"closed": tk.id, "handle_ms": round(tk.first_response_ms),
          "sla_met": tk.first_response_ms <= SLA_MS["skill"][tk.channel]})


def cmd_rate(args, index):
    recs = [json.loads(l) for l in TICKET_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
    hit = [r for r in recs if r["id"] == args.ticket_id]
    for r in hit:
        r["csat"] = args.score
    TICKET_LOG.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs), encoding="utf-8")
    emit({"rated": args.ticket_id, "csat": args.score, "found": bool(hit)})


def main(argv=None):
    p = argparse.ArgumentParser(description="ヘルスケア医師案内エージェント（クローズド構成）")
    p.add_argument("--data", default=str(DEFAULT_DATA), help="医師データ JSON")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("chat"); c.add_argument("--channel", choices=["message", "voice"], default="message")
    a = sub.add_parser("ask"); a.add_argument("text"); a.add_argument("--channel", choices=["message", "voice"], default="message")
    b = sub.add_parser("batch"); b.add_argument("file")
    sub.add_parser("metrics")
    o = sub.add_parser("open"); o.add_argument("text"); o.add_argument("--channel", choices=["message", "voice"], default="message")
    s = sub.add_parser("search")
    s.add_argument("--specialty", action="append", default=[], help="expertise（英語）。優先度順に複数可")
    s.add_argument("--gender", choices=["female", "male"])
    s.add_argument("--language", help="English / Chinese など")
    s.add_argument("--region")
    s.add_argument("--weekday", help="月..日 または 0(月)..6(日)")
    s.add_argument("--date", help="MM-DD")
    s.add_argument("--ampm", choices=["am", "pm"])
    s.add_argument("--personality", action="append", default=[])
    s.add_argument("--limit", type=int, default=3)
    d = sub.add_parser("doctor"); d.add_argument("name")
    cl = sub.add_parser("close"); cl.add_argument("ticket_id")
    cl.add_argument("--intent", required=True, choices=["search", "doctor_info", "emergency", "out_of_scope", "unclear"])
    cl.add_argument("--outcome", required=True, choices=["resolved", "escalated", "clarify"])
    cl.add_argument("--csat", type=int, choices=range(1, 6))
    cl.add_argument("--turns", type=int, default=1)
    r = sub.add_parser("rate"); r.add_argument("ticket_id"); r.add_argument("score", type=int, choices=range(1, 6))
    args = p.parse_args(argv)
    index = DoctorIndex(args.data)
    cmds = {"chat": cmd_chat, "ask": cmd_ask, "batch": cmd_batch, "metrics": cmd_metrics, "open": cmd_open,
            "search": cmd_search, "doctor": cmd_doctor, "close": cmd_close, "rate": cmd_rate}
    return cmds[args.cmd](args, index)


if __name__ == "__main__":
    sys.exit(main())
