"""Closed (offline) NLU + doctor search. No network calls, no external services."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# 緊急ワード: 検索より先に判定して 119 案内（安全 > 自動化）
EMERGENCY = ["胸が締め付け", "息ができない", "呼吸ができない", "意識がない", "意識が", "けいれん",
             "大量に出血", "血が止まらない", "ろれつが回らない", "顔の片側", "自殺", "死にたい"]

# 症状 → 診療科（レガシー JSON に診療科しかなくても症状から引けるようにする辞書）
SYMPTOM_TO_SPECIALTY = {
    "頭痛": "神経内科", "めまい": "神経内科", "しびれ": "神経内科", "物忘れ": "神経内科",
    "動悸": "循環器内科", "胸の痛み": "循環器内科", "息切れ": "循環器内科", "高血圧": "循環器内科", "むくみ": "循環器内科",
    "膝": "整形外科", "腰": "整形外科", "捻": "整形外科", "骨折": "整形外科", "肩": "整形外科",
    "湿疹": "皮膚科", "かゆ": "皮膚科", "ニキビ": "皮膚科", "肌": "皮膚科", "アトピー": "皮膚科",
    "妊娠": "産婦人科", "生理": "産婦人科", "更年期": "産婦人科",
    "腹痛": "消化器内科", "お腹": "消化器内科", "胃": "消化器内科", "下痢": "消化器内科", "便秘": "消化器内科", "胸やけ": "消化器内科",
    "眠れ": "精神科", "不眠": "精神科", "落ち込": "精神科", "不安": "精神科", "ストレス": "精神科",
    "鼻": "耳鼻咽喉科", "花粉": "耳鼻咽喉科", "喉": "耳鼻咽喉科", "耳": "耳鼻咽喉科",
    "目": "眼科", "視力": "眼科",
    "熱": "内科", "咳": "内科", "風邪": "内科", "だる": "内科", "糖尿": "内科",
}
CHILD_WORDS = ["子ども", "子供", "息子", "娘", "赤ちゃん", "歳の", "才の", "小学生", "乳児"]
SPECIALTY_ALIASES = {"循環器": "循環器内科", "心臓": "循環器内科", "小児": "小児科", "整形": "整形外科",
                     "神経": "神経内科", "婦人科": "産婦人科", "産科": "産婦人科", "消化器": "消化器内科",
                     "心療内科": "精神科", "メンタル": "精神科", "耳鼻科": "耳鼻咽喉科"}
LANG_WORDS = {"英語": "英語", "english": "英語", "中国語": "中国語", "韓国語": "韓国語"}
DAYS = ["月", "火", "水", "木", "金", "土", "日"]
OUT_OF_SCOPE = ["請求", "支払", "領収書", "駐車場", "面会", "診断書", "保険証", "キャンセル", "予約の変更"]


@dataclass
class Query:
    text: str
    intent: str = "search"          # search | doctor_info | emergency | out_of_scope | unclear
    specialties: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    name: str | None = None
    gender: str | None = None
    language: str | None = None
    day: str | None = None
    telehealth: bool | None = None
    new_patient: bool = True


class DoctorIndex:
    """Load the single legacy JSON once and keep an in-memory index (no search API needed)."""

    def __init__(self, path: str | Path):
        self.doctors: list[dict] = json.loads(Path(path).read_text(encoding="utf-8"))
        self.specialties = sorted({d.get("specialty", "") for d in self.doctors} - {""})
        self._text = {d["id"]: self._flatten(d).lower() for d in self.doctors}

    @staticmethod
    def _flatten(obj) -> str:
        if isinstance(obj, dict):
            return " ".join(DoctorIndex._flatten(v) for v in obj.values())
        if isinstance(obj, list):
            return " ".join(DoctorIndex._flatten(v) for v in obj)
        return str(obj)

    def surnames(self) -> dict[str, dict]:
        out = {}
        for d in self.doctors:
            out[d["name"].replace(" ", "")] = d
            out[d["name"].split()[0]] = d
            if d.get("name_en"):
                out[d["name_en"].lower()] = d
                out[d["name_en"].split()[-1].lower()] = d
        return out

    def search(self, q: Query, limit: int = 3) -> tuple[list[tuple[float, dict]], list[str]]:
        """Return ranked doctors and notes about relaxed constraints."""
        notes: list[str] = []
        filters = [("gender", q.gender), ("language", q.language), ("day", q.day), ("telehealth", q.telehealth)]
        active = [f for f in filters if f[1] is not None]
        while True:
            ranked = [(self._score(d, q), d) for d in self.doctors if self._passes(d, active)]
            ranked = [r for r in ranked if r[0] > 0]
            if ranked or not active:
                break
            dropped = active.pop()  # 条件を緩めてゼロ件回答を避ける（再問い合わせ＝チケット増を防ぐ）
            notes.append(f"条件「{dropped[1]}」に合う医師がいないため、その条件を外して検索しました")
        ranked.sort(key=lambda r: (-r[0], -r[1].get("rating", 0)))
        return ranked[:limit], notes

    @staticmethod
    def _passes(d: dict, active) -> bool:
        for key, val in active:
            if key == "gender" and d.get("gender") != val:
                return False
            if key == "language" and val not in d.get("languages", []):
                return False
            if key == "day" and val not in d.get("available_days", []):
                return False
            if key == "telehealth" and bool(d.get("telehealth")) != val:
                return False
        return True

    def _score(self, d: dict, q: Query) -> float:
        s = 0.0
        if d.get("specialty") in q.specialties:
            s += 5
        text = self._text[d["id"]]
        for kw in q.keywords:
            if kw.lower() in text:
                s += 2
        if s > 0:
            s += d.get("rating", 0) / 5  # tie-break by rating
            if q.new_patient and d.get("accepting_new_patients") is False:
                s -= 3
        return s


def parse(text: str, index: DoctorIndex) -> Query:
    q = Query(text=text)
    t = text.strip()
    low = t.lower()

    if any(w in t for w in EMERGENCY):
        q.intent = "emergency"
        return q

    for key, doc in index.surnames().items():
        if key and (key in t or key in low):
            q.intent, q.name = "doctor_info", doc["id"]
            return q

    if any(w in t for w in OUT_OF_SCOPE):
        q.intent = "out_of_scope"
        return q

    for alias, spec in SPECIALTY_ALIASES.items():
        if alias in t and spec not in q.specialties:
            q.specialties.append(spec)
    for spec in index.specialties:
        if spec in t and spec not in q.specialties:
            q.specialties.append(spec)
    for sym, spec in SYMPTOM_TO_SPECIALTY.items():
        if sym in t:
            q.keywords.append(sym)
            if spec not in q.specialties:
                q.specialties.append(spec)
    if any(w in t for w in CHILD_WORDS) or re.search(r"\d+\s*[歳才]", t):
        q.specialties.insert(0, "小児科")

    if "女性" in t or "女の先生" in t:
        q.gender = "女性"
    elif "男性" in t or "男の先生" in t:
        q.gender = "男性"
    for w, lang in LANG_WORDS.items():
        if w in low:
            q.language = lang
    m = re.search(r"([月火水木金土日])曜", t)
    if m:
        q.day = m.group(1)
    if any(w in t for w in ["オンライン", "リモート", "電話で診", "ビデオ"]):
        q.telehealth = True

    if not q.specialties and not q.keywords:
        q.intent = "unclear"
    return q


PII_PATTERNS = [
    (re.compile(r"0\d{1,4}-?\d{1,4}-?\d{3,4}"), "<TEL>"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "<EMAIL>"),
    (re.compile(r"\d{4}[/-]\d{1,2}[/-]\d{1,2}"), "<DATE>"),
    (re.compile(r"(診察券|患者)(番号|ID)?\s*[:：]?\s*\d+"), "<PATIENT_ID>"),
]


def mask_pii(text: str) -> str:
    for pat, rep in PII_PATTERNS:
        text = pat.sub(rep, text)
    return text
