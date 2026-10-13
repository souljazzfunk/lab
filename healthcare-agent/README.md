# ヘルスケア医師案内エージェント（CLI）

患者・ご家族からのメッセージ／音声（文字起こし済みテキスト）を受け、`sample_doctors.json` から最適な医師と空き枠を案内する CLI エージェント。

## アーキテクチャ（API キー不要）
```
自然言語の問い合わせ ─▶ Claude Code + doctor-finder スキル（言葉の理解・返答文）
                          │  Bash で同梱の CLI を呼ぶ（JSON で受け渡し）
                          ├▶ open   : Ticket 発行 + 緊急判定(ルール・必ず最初) + 抽出ヒント
                          ├▶ search / doctor : レガシー JSON をメモリに索引して検索
                          └▶ close / rate    : Ticket 記録(JST, PII マスク) ─▶ metrics
```
- **API キー不要**: LLM の役割は Claude Code 本体が受け持つ。Claude Code のセッションに `/doctor-finder` か自然文で頼むだけで動く。
- **検索はローカル**: Claude はツール結果の医師・空き枠しか案内しない（SKILL.md で禁止を明記）。
- **安全**: 緊急ワードの判定は `open` の時点でルールが行い、`emergency: true` なら検索せずに 119 を案内する。
- **LLM なしでも動く**: `chat` / `ask` / `batch` はルールだけで即答する（デモや大量処理向け）。

## データの扱い（実 JSON に対応）
- `aliases`（ENT / Pedia / Heart doctor）と医師ごとの `keywords` を辞書に取り込む
- 症状（頭痛→Neurology など）と日本語の診療科名（耳鼻科→Otolaryngology など）を英語の `expertise` に対応づける
- 「田中先生」→ `Dr. Aiko Tanaka`（日本語の姓 → ローマ字）
- 絞り込み: 性別・言語・地域・日付・曜日・午前／午後（`available_slots` から判定）
- 「優しい先生」→ `personality`（kind / gentle / empathetic）を加点
- 同点のときは 医師評価 → 病院評価（`hospitals.rating`）→ `score` の順で並べる

## KPI への効き方
| KPI | 施策 |
|---|---|
| CSAT | 症状から診療科を推定／希望条件で 0 件なら条件を緩めて理由も伝える／性格の希望を順位に反映／相手と同じ言語で返答（スキル）／会話の終わりに 1〜5 で評価を取る |
| SLA | 検索はローカルなのでミリ秒単位。スキル経由でも検索はローカル。SLA 目標はチャネル別・エンジン別（ルール: voice 1 秒 / message 3 秒、スキル: 10 秒 / 30 秒）に対する達成率を記録 |
| 処理 Ticket 数 | 全件チケット化し、`batch` で一括処理できる。対象外の用件は受付番号つきで即エスカレーション。聞き返しは 1 回だけで、文脈を引き継ぐ |
| Voice | 医師 1 名・1〜2 文・読み上げやすい文で案内 |

## 使い方
### スキル（自然言語）
このリポジトリで Claude Code を開くと `.claude/skills/doctor-finder` が読み込まれる。リポジトリの外では、マーケットプレイス `lab` から `doctor-finder` プラグインを入れる。
```
/doctor-finder 5歳の娘が熱を出しました。東京で、午前中に優しい女性の先生に診てほしい
/doctor-finder (電話) 頭痛とめまいがひどい。水曜に行きたい
/doctor-finder 田中先生の空き枠は？
/doctor-finder KPI を見せて
```

### CLI（ルールのみ・LLM なし）
```bash
python3 agent.py chat --channel voice           # 対話（終了時に CSAT）
python3 agent.py ask "Looking for an ENT doctor in Yokohama"
python3 agent.py batch samples/inquiries.jsonl  # 一括処理
python3 agent.py metrics                        # Ticket 数 / 自動解決率 / SLA / CSAT / エンジン別
```
スキルが使う JSON の API: `open` / `search` / `doctor` / `close` / `rate`（`python3 agent.py -h`）。
環境変数: `HC_DOCTORS_JSON`（医師データ）、`HC_AGENT_HOME`（Ticket ログ。既定は `~/.healthcare-agent`）。

## 構成
- `core.py`: 意図判定・条件の抽出、医師インデックスとスコアリング、PII マスク
- `agent.py`: CLI（ルールモード + スキル用の JSON API）、Ticket 管理、KPI 集計（JST）
- `skill-src/SKILL.md`: スキル本体（受付の流れ・返答ルール）
- `build.sh`: 上の 3 つから `plugin/`（配布用）を組み立てる。ソースを直したら実行する
