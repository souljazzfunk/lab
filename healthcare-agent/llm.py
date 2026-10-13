"""Claude-powered conversation layer. Search still runs locally over the JSON (tool use)."""
from __future__ import annotations

import json
import os

from core import SPECIALTY_JA, DoctorIndex, Query, mask_pii

MODEL = os.environ.get("HC_AGENT_MODEL", "claude-opus-5-5")

SYSTEM = """あなたはヘルスケア施設の受付エージェントです。患者やご家族の話から最適な医師を案内します。
- 医師の情報は必ず search_doctors / get_doctor ツールで確認し、ツール結果にない医師や空き枠を作らないこと。
- 診断・治療の助言はしない。症状から診療科を選ぶところまでにする。
- 情報が足りないときは、症状・地域・希望日時のうち一番効くものを 1 つだけ聞く。
- 医師案内以外の用件（請求・予約変更など）や、適任がいない場合は handoff_to_staff を使う。
- 返答は相手と同じ言語で書く。内部番号やスコアは伝えない。
- channel=voice のときは読み上げ前提で 1〜2 文・医師は 1 名・記号や箇条書きなし。
- channel=message のときは最大 3 名を簡潔な箇条書きで。最後に次のアクション（予約の確認）を 1 文で。"""


def build_tools(index: DoctorIndex) -> list[dict]:
    return [
        {
            "name": "search_doctors",
            "description": "院内の医師データ(JSON)を検索する。条件が厳しすぎて0件の場合は自動で緩め、notesで知らせる。",
            "strict": True,
            "input_schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "specialties": {"type": "array", "items": {"type": "string", "enum": index.specialties},
                                    "description": "優先度順の診療科。子どもの場合は Pediatrics を先頭に。"},
                    "gender": {"type": ["string", "null"], "enum": ["female", "male", None]},
                    "language": {"type": ["string", "null"], "enum": ["English", "Chinese", None]},
                    "region": {"type": ["string", "null"], "enum": sorted({d["region"] for d in index.doctors}) + [None]},
                    "weekday": {"type": ["integer", "null"], "description": "0=月 ... 6=日"},
                    "date": {"type": ["string", "null"], "description": "MM-DD"},
                    "ampm": {"type": ["string", "null"], "enum": ["am", "pm", None]},
                    "personalities": {"type": "array", "items": {"type": "string",
                                      "enum": sorted({d.get("personality", "") for d in index.doctors} - {""})}},
                },
                "required": ["specialties", "gender", "language", "region", "weekday", "date", "ampm", "personalities"],
            },
        },
        {
            "name": "get_doctor",
            "description": "医師名（ローマ字の姓など）で医師の詳細と空き枠を取得する。",
            "strict": True,
            "input_schema": {"type": "object", "additionalProperties": False,
                             "properties": {"name": {"type": "string"}}, "required": ["name"]},
        },
        {
            "name": "handoff_to_staff",
            "description": "人間のスタッフに引き継ぐ。医師案内の対象外の用件や、適任がいない場合に使う。",
            "strict": True,
            "input_schema": {"type": "object", "additionalProperties": False,
                             "properties": {"reason": {"type": "string"}}, "required": ["reason"]},
        },
    ]


def doctor_view(d: dict, slots=None) -> dict:
    return {
        "name": d["name"], "specialty": d["specialty"], "specialty_ja": SPECIALTY_JA.get(d["specialty"]),
        "gender": d.get("gender"), "languages": d["languages"], "hospital": d.get("hospital"),
        "region": d.get("region"), "rating": d.get("rating"), "personality": d.get("personality"),
        "available_slots": [s.strftime("%Y-%m-%d %H:%M") for s in (slots if slots is not None else d["slots"])][:4],
    }


class ClaudeAgent:
    def __init__(self, index: DoctorIndex):
        import anthropic  # 遅延 import: ルールベースモードでは SDK 不要

        self.anthropic = anthropic
        self.client = anthropic.Anthropic()
        self.index = index
        self.tools = build_tools(index)

    def run_tool(self, name: str, args: dict, state: dict) -> str:
        if name == "search_doctors":
            q = Query(text="", **args)
            ranked, notes = self.index.search(q, limit=3)
            state["intent"] = "search"
            return json.dumps({"notes": notes, "doctors": [doctor_view(d, s) for _, d, s in ranked]}, ensure_ascii=False)
        if name == "get_doctor":
            hits = self.index.find_by_name(args["name"])
            state["intent"] = "doctor_info"
            return json.dumps({"doctors": [doctor_view(d) for d in hits]}, ensure_ascii=False)
        if name == "handoff_to_staff":
            state["intent"], state["escalated"] = "out_of_scope", True
            return json.dumps({"ok": True, "ticket_id": state["ticket_id"]}, ensure_ascii=False)
        raise ValueError(name)

    def reply(self, messages: list, text: str, channel: str, ticket_id: str) -> tuple[str, dict]:
        """Append one user turn, run the tool loop, return (reply_text, state)."""
        state = {"ticket_id": ticket_id, "intent": None, "escalated": False}
        # Claude に送る前にも PII はマスク（必要最小限の情報だけ外に出す）
        messages.append({"role": "user", "content": f"[channel={channel}] {mask_pii(text)}"})
        for _ in range(6):
            resp = self.client.beta.messages.create(
                model=MODEL,
                max_tokens=16000,
                system=SYSTEM,
                tools=self.tools,
                messages=messages,
                output_config={"effort": "low"},  # 受付対話は低 effort で十分、レイテンシ優先（SLA）
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
            if resp.stop_reason == "refusal":
                raise RuntimeError("refusal")
            messages.append({"role": "assistant", "content": resp.content})
            if resp.stop_reason != "tool_use":
                out = "".join(b.text for b in resp.content if b.type == "text").strip()
                return out, state
            results = []
            for b in resp.content:
                if b.type == "tool_use":
                    try:
                        results.append({"type": "tool_result", "tool_use_id": b.id,
                                        "content": self.run_tool(b.name, b.input, state)})
                    except Exception as e:  # noqa: BLE001
                        results.append({"type": "tool_result", "tool_use_id": b.id,
                                        "content": f"error: {e}", "is_error": True})
            messages.append({"role": "user", "content": results})
        raise RuntimeError("tool loop limit")
