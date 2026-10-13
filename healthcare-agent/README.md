# ヘルスケア医師案内エージェント（CLI）

患者・ご家族からのメッセージ／音声（文字起こし済みテキスト）を受け、`sample_doctors.json` から最適な医師と空き枠を案内する CLI エージェント。

## アーキテクチャ
```
入力(voice/message) ─▶ 緊急判定(ルール・常に先) ─▶ 119 / #7119 案内
                     └▶ Claude（会話・意図理解） ──tool use──▶ ローカル検索(JSON をメモリに索引)
                        └ 障害時・認証なし ─▶ ルールベースのエンジンで即応答
                     ─▶ Ticket 記録(JST, PII マスク) ─▶ metrics
```
- **検索はローカル**: レガシー JSON を起動時に 1 回読み込んで索引を作る（検索 API 不要）。Claude は `search_doctors` / `get_doctor` / `handoff_to_staff` ツール経由でしか医師情報に触れないので、存在しない医師や空き枠を作らない。
- **安全**: 緊急ワードの判定は LLM に任せず、ルールで先に行う。診断はしない（診療科の選択まで）。
- **データの最小化**: Claude へ送る前に電話番号・メール・日付・患者 ID をマスクする。ログもマスク済み。
- **可用性**: Claude の API エラーや拒否が起きたら、ルールベースのエンジンに自動で切り替えて応答する。

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
| CSAT | 症状から診療科を推定／希望条件で 0 件なら条件を緩めて理由も伝える／性格の希望を順位に反映／相手と同じ言語で返答（Claude モード）／会話の終わりに 1〜5 で評価を取る |
| SLA | 検索はローカルなのでミリ秒単位。Claude は effort=low で待ち時間を抑える。API 障害時はルールで即応答。チャネル別の SLA 目標（voice 1 秒 / message 3 秒）に対する達成率を記録 |
| 処理 Ticket 数 | 全件チケット化し、`batch` で一括処理できる。対象外の用件は受付番号つきで即エスカレーション。聞き返しは 1 回だけで、文脈を引き継ぐ |
| Voice | 医師 1 名・1〜2 文・読み上げやすい文で案内 |

## 使い方
```bash
pip install -r requirements.txt                 # Claude モードを使う場合のみ
export ANTHROPIC_API_KEY=...                    # 未設定ならルールモードで動く
python3 agent.py chat --channel voice           # 対話（終了時に CSAT）
python3 agent.py ask "Looking for an ENT doctor in Yokohama"
python3 agent.py batch samples/inquiries.jsonl  # 一括処理
python3 agent.py metrics                        # Ticket 数 / 自動解決率 / SLA / CSAT / エンジン別
python3 agent.py --engine rules batch samples/inquiries.jsonl   # ルールモードを強制
```
モデルは `claude-opus-5-5`（環境変数 `HC_AGENT_MODEL` で変更可）。拒否されたときのためにサーバー側フォールバックを有効にしている。

## 構成
- `core.py`: 意図判定・条件の抽出、医師インデックスとスコアリング、PII マスク
- `llm.py`: Claude のツール呼び出しループ（ツールの中身はローカル検索）
- `agent.py`: CLI、チケット管理、ルールでの応答、KPI 集計（JST）
