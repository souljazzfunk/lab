"""Closed (offline) NLU + doctor search. No network calls, no external services."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# 緊急ワード: 検索より先に判定して 119 案内（安全 > 自動化）
EMERGENCY = ["胸が締め付け", "息ができない", "呼吸ができない", "意識がない", "けいれん", "大量に出血",
             "血が止まらない", "ろれつが回らない", "顔の片側", "自殺", "死にたい",
             "can't breathe", "cannot breathe", "chest pain", "unconscious", "suicide"]

# JSON の expertise（英語）に対する日本語表示名と、日本語・英語の呼び方
SPECIALTY_JA = {
    "Pediatrics": "小児科", "Dermatology": "皮膚科", "Cardiology": "循環器内科",
    "Otolaryngology": "耳鼻咽喉科", "Orthopedics": "整形外科", "Neurology": "神経内科",
    "Psychiatry": "精神科", "General Practice": "総合診療（内科）", "Gastroenterology": "消化器内科",
    "Obstetrics and Gynecology": "産婦人科", "Ophthalmology": "眼科",
}
SPECIALTY_WORDS = {
    "Pediatrics": ["小児", "pediatric"], "Dermatology": ["皮膚", "dermatolog", "skin"],
    "Cardiology": ["循環器", "心臓", "cardio", "heart"], "Otolaryngology": ["耳鼻", "otolaryng"],
    "Orthopedics": ["整形", "orthop"], "Neurology": ["神経内科", "脳神経", "neuro"],
    "Psychiatry": ["精神", "心療内科", "メンタル", "psychiat", "mental"],
    "General Practice": ["内科", "かかりつけ", "general"], "Gastroenterology": ["消化器", "胃腸", "gastro"],
    "Obstetrics and Gynecology": ["産婦人科", "婦人科", "産科", "gyneco", "obstet"],
    "Ophthalmology": ["眼科", "ophthalm", "eye doctor"],
}
# 症状 → 診療科（JSON に症状情報がないので辞書で補う）
SYMPTOM_TO_SPECIALTY = {
    "頭痛": "Neurology", "めまい": "Neurology", "しびれ": "Neurology", "物忘れ": "Neurology", "headache": "Neurology",
    "動悸": "Cardiology", "胸の痛み": "Cardiology", "胸が痛": "Cardiology", "息切れ": "Cardiology",
    "血圧": "Cardiology", "むくみ": "Cardiology", "palpitation": "Cardiology",
    "膝": "Orthopedics", "腰": "Orthopedics", "捻": "Orthopedics", "骨折": "Orthopedics", "肩": "Orthopedics",
    "関節": "Orthopedics", "knee": "Orthopedics", "back pain": "Orthopedics",
    "湿疹": "Dermatology", "かゆ": "Dermatology", "ニキビ": "Dermatology", "肌": "Dermatology",
    "アトピー": "Dermatology", "rash": "Dermatology",
    "妊娠": "Obstetrics and Gynecology", "生理": "Obstetrics and Gynecology",
    "更年期": "Obstetrics and Gynecology", "pregnan": "Obstetrics and Gynecology",
    "腹痛": "Gastroenterology", "お腹": "Gastroenterology", "胃": "Gastroenterology", "下痢": "Gastroenterology",
    "便秘": "Gastroenterology", "胸やけ": "Gastroenterology", "stomach": "Gastroenterology",
    "眠れ": "Psychiatry", "不眠": "Psychiatry", "落ち込": "Psychiatry", "不安": "Psychiatry",
    "ストレス": "Psychiatry", "うつ": "Psychiatry", "insomnia": "Psychiatry", "anxiety": "Psychiatry",
    "鼻": "Otolaryngology", "花粉": "Otolaryngology", "喉": "Otolaryngology", "のど": "Otolaryngology",
    "耳": "Otolaryngology", "throat": "Otolaryngology",
    "目": "Ophthalmology", "視力": "Ophthalmology", "eye": "Ophthalmology",
    "熱": "General Practice", "咳": "General Practice", "風邪": "General Practice", "だる": "General Practice",
    "fever": "General Practice", "cough": "General Practice", "cold": "General Practice",
}
CHILD_WORDS = ["子ども", "子供", "こども", "息子", "娘", "赤ちゃん", "小学生", "乳児", "幼児", "child", "kid", "baby"]
REGION_WORDS = {"Tokyo": ["東京", "tokyo"], "Osaka": ["大阪", "osaka"],
                "Yokohama": ["横浜", "yokohama"], "Sapporo": ["札幌", "sapporo"]}
REGION_JA = {"Tokyo": "東京", "Osaka": "大阪", "Yokohama": "横浜", "Sapporo": "札幌"}
LANG_WORDS = {"English": ["英語", "english"], "Chinese": ["中国語", "chinese", "中文"]}
PERSONALITY_WORDS = {  # CSAT 向け: 「優しい先生がいい」などの希望を順位に反映
    "kind": ["優し", "やさし", "親切", "kind"], "gentle": ["優し", "やさし", "穏やか", "gentle"],
    "empathetic": ["寄り添", "話を聞", "共感", "優し"], "calm": ["落ち着", "穏やか", "calm"],
    "friendly": ["気さく", "話しやす", "friendly"], "humor": ["明る", "面白", "楽し", "humor", "funny"],
    "professional": ["ベテラン", "専門的", "しっかり", "経験豊富", "professional"],
}
# 日本語の姓 → JSON 上のローマ字姓（「田中先生」で引けるように）
SURNAME_JA = {"田中": "Tanaka", "佐藤": "Sato", "中村": "Nakamura", "山本": "Yamamoto", "鈴木": "Suzuki",
              "小林": "Kobayashi", "伊藤": "Ito", "森": "Mori", "藤田": "Fujita", "渡辺": "Watanabe",
              "加藤": "Kato", "石川": "Ishikawa", "林": "Hayashi", "青木": "Aoki", "井上": "Inoue"}
WEEKDAY_JA = "月火水木金土日"
OUT_OF_SCOPE = ["請求", "支払", "領収書", "駐車場", "面会", "診断書", "保険証", "キャンセル", "予約の変更",
                "invoice", "billing", "parking"]


@dataclass
class Query:
    text: str
    intent: str = "search"          # search | doctor_info | emergency | out_of_scope | unclear
    specialties: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    doctor_ids: list[str] = field(default_factory=list)
    gender: str | None = None
    language: str | None = None
    region: str | None = None
    weekday: int | None = None      # 0=Mon
    date: str | None = None         # MM-DD
    ampm: str | None = None         # am | pm
    personalities: list[str] = field(default_factory=list)


class DoctorIndex:
    """Load the single legacy JSON once and keep an in-memory index (no search API needed)."""

    def __init__(self, path: str | Path):
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        self.hospitals = {h["name"]: h for h in raw.get("hospitals", [])}
        self.doctors: list[dict] = [self._normalize(d) for d in raw["doctors"]]
        self.specialties = sorted({d["specialty"] for d in self.doctors})
        # JSON の aliases（ENT, Pedia, Heart doctor）と医師ごとの keywords を辞書に取り込む
        self.aliases: dict[str, str] = {}
        for a in raw.get("aliases", []):
            self.aliases[a["alias"].lower()] = a["keyword"]
        for d in self.doctors:
            for kw in d.get("keywords", []):
                self.aliases.setdefault(kw.lower(), d["specialty"])

    def _normalize(self, d: dict) -> dict:
        n = dict(d)
        n["id"] = d.get("internal_number") or d["name"]
        n["specialty"] = d.get("expertise", "")
        lang = d.get("language", "")
        n["languages"] = [x.strip() for x in lang.split(",")] if isinstance(lang, str) else list(lang)
        n["slots"] = []
        for s in d.get("available_slots", []):
            try:
                n["slots"].append(datetime.strptime(s, "%Y-%m-%d %H:%M"))
            except ValueError:
                pass
        n["slots"].sort()
        n["hospital_rating"] = self.hospitals.get(d.get("hospital"), {}).get("rating", 0)
        return n

    def find_by_name(self, text: str) -> list[dict]:
        low = text.lower()
        hits = []
        for d in self.doctors:
            surname = d["name"].split()[-1]
            if surname.lower() in low or d["name"].lower() in low:
                hits.append(d)
        for ja in sorted(SURNAME_JA, key=len, reverse=True):
            if re.search(ja + r"\s*(先生|医師|ドクター|さん)", text):
                hits += [d for d in self.doctors if d["name"].split()[-1] == SURNAME_JA[ja] and d not in hits]
                text = text.replace(ja, "")  # 「小林先生」が「林先生」にも当たらないように
        return hits

    def slot_ok(self, s: datetime, q: Query) -> bool:
        if q.weekday is not None and s.weekday() != q.weekday:
            return False
        if q.date and s.strftime("%m-%d") != q.date:
            return False
        if q.ampm == "am" and s.hour >= 12:
            return False
        if q.ampm == "pm" and s.hour < 12:
            return False
        return True

    def search(self, q: Query, limit: int = 3) -> tuple[list[tuple[float, dict, list[datetime]]], list[str]]:
        """Return ranked (score, doctor, matching_slots) and notes about relaxed constraints."""
        notes: list[str] = []
        filters = [("性別", "gender"), ("言語", "language"), ("地域", "region"), ("日時", "slot")]
        active = [f for f in filters if (f[1] != "slot" and getattr(q, f[1])) or
                  (f[1] == "slot" and (q.weekday is not None or q.date or q.ampm))]
        while True:
            ranked = []
            for d in self.doctors:
                slots = [s for s in d["slots"] if self.slot_ok(s, q)] if ("日時", "slot") in active else d["slots"]
                if not self._passes(d, q, active, slots):
                    continue
                score = self._score(d, q)
                if score > 0:
                    ranked.append((score, d, slots))
            if ranked or not active:
                break
            dropped = active.pop()  # 条件を緩めてゼロ件回答を避ける（再問い合わせ＝チケット増を防ぐ）
            notes.append(f"ご希望の{dropped[0]}に合う医師がいないため、その条件を外して探しました。")
        ranked.sort(key=lambda r: -r[0])
        return ranked[:limit], notes

    @staticmethod
    def _passes(d: dict, q: Query, active, slots) -> bool:
        keys = {k for _, k in active}
        if "gender" in keys and d.get("gender") != q.gender:
            return False
        if "language" in keys and q.language not in d["languages"]:
            return False
        if "region" in keys and d.get("region") != q.region:
            return False
        if "slot" in keys and not slots:
            return False
        return True

    @staticmethod
    def _score(d: dict, q: Query) -> float:
        if q.specialties and d["specialty"] not in q.specialties:
            return 0.0
        s = 5.0
        if q.specialties:  # 先に挙がった診療科ほど優先（小児 > 症状からの推定）
            s += (len(q.specialties) - q.specialties.index(d["specialty"]))
        if d.get("personality") in q.personalities:
            s += 1.5
        # 同点は 医師評価 > 病院評価 > 内部スコア の順で決める
        return s + d.get("rating", 0) / 5 + d.get("hospital_rating", 0) / 10 + d.get("score", 0) / 1000


def doctor_view(d: dict, slots=None) -> dict:
    """Patient-facing doctor info (internal number / score are not exposed)."""
    return {
        "name": d["name"], "specialty": d["specialty"], "specialty_ja": SPECIALTY_JA.get(d["specialty"]),
        "gender": d.get("gender"), "languages": d["languages"], "hospital": d.get("hospital"),
        "region": d.get("region"), "rating": d.get("rating"), "personality": d.get("personality"),
        "available_slots": [s.strftime("%Y-%m-%d %H:%M") for s in (slots if slots is not None else d["slots"])][:4],
    }


def _has(text: str, low: str, words) -> bool:
    return any(w in text or w in low for w in words)


def parse(text: str, index: DoctorIndex) -> Query:
    q = Query(text=text)
    t = text.strip()
    low = t.lower()

    if _has(t, low, EMERGENCY):
        q.intent = "emergency"
        return q

    named = index.find_by_name(t)
    if named:
        q.intent, q.doctor_ids = "doctor_info", [d["id"] for d in named]
        return q

    if _has(t, low, OUT_OF_SCOPE):
        q.intent = "out_of_scope"
        return q

    def add(spec):
        if spec in index.specialties and spec not in q.specialties:
            q.specialties.append(spec)

    if _has(t, low, CHILD_WORDS) or re.search(r"\d+\s*[歳才]", t):
        add("Pediatrics")
    for alias, spec in index.aliases.items():
        if re.search(r"\b" + re.escape(alias) + r"\b", low):
            add(spec)
    for spec, words in SPECIALTY_WORDS.items():
        if _has(t, low, words) or spec.lower() in low:
            add(spec)
    for sym, spec in SYMPTOM_TO_SPECIALTY.items():
        if sym in t or sym in low:
            q.keywords.append(sym)
            add(spec)

    if _has(t, low, ["女性", "女の先生", "female", "woman"]):
        q.gender = "female"
    elif _has(t, low, ["男性", "男の先生", "male"]):
        q.gender = "male"
    for lang, words in LANG_WORDS.items():
        if _has(t, low, words):
            q.language = lang
    for region, words in REGION_WORDS.items():
        if _has(t, low, words):
            q.region = region
    m = re.search(r"([月火水木金土日])曜", t)
    if m:
        q.weekday = WEEKDAY_JA.index(m.group(1))
    m = re.search(r"(\d{1,2})\s*[月/]\s*(\d{1,2})\s*日?", t)
    if m:
        q.date = f"{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    if _has(t, low, ["午前", "朝", "morning"]):
        q.ampm = "am"
    elif _has(t, low, ["午後", "夕方", "afternoon", "evening"]):
        q.ampm = "pm"
    q.personalities = [p for p, words in PERSONALITY_WORDS.items() if _has(t, low, words)]

    if not q.specialties:
        q.intent = "unclear"
    return q


PII_PATTERNS = [
    (re.compile(r"0\d{1,4}-?\d{1,4}-?\d{3,4}"), "<TEL>"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "<EMAIL>"),
    (re.compile(r"(19|20)\d{2}[/-]\d{1,2}[/-]\d{1,2}"), "<DATE>"),
    (re.compile(r"(診察券|患者)(番号|ID)?\s*[:：]?\s*\d+"), "<PATIENT_ID>"),
]


def mask_pii(text: str) -> str:
    for pat, rep in PII_PATTERNS:
        text = pat.sub(rep, text)
    return text
