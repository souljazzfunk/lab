# pstack スキル地図

[English](skill-map.en.md)

Cursor 用プラグイン pstack を Claude Code 向けに変換したもの(`pstack-cc/plugin/`)にある、スキル 58 個・エージェント 2 個の関係と、各スキルがサブエージェントをどう動かすかの図。

## 1. 全体像

入口は `/poteto-mode`。仕事の種類で playbook を選び、各ステップから why / architect などのワークフロースキルを呼ぶ。どのスキルも最初に `claude-code.md`(Cursor → Claude Code 対応表)を読み、モデル選択は `~/.claude/pstack-models.md` に従う。

```mermaid
flowchart LR
  U([ユーザー]) --> PM["/poteto-mode<br/>(poteto-agent 経由も可)"]
  PM --> PB{"playbook を選ぶ<br/>23 種"}
  PM -. 大規模・当てはまる型なし .-> FIO["figure-it-out"]
  PB --> WF["ワークフロースキル<br/>why / architect / arena<br/>interrogate / swarm / tdd"]
  PB --> Q["仕上げスキル<br/>unslop / technical-writing<br/>no-comments / show-me-your-work"]
  PM --> PR["principle-* 24 個<br/>(判断の根拠)"]
  WF --> SA[["サブエージェント群<br/>(並列・worktree)"]]
  SP["/setup-pstack"] -->|書く| CFG[("~/.claude/pstack-models.md")]
  CFG -.読む.-> WF
  CC[("claude-code.md")] -.全スキルが最初に読む.-> PM
```

## 2. スキル同士の参照関係

SKILL.md 内で他スキルを名指ししている箇所を抜き出した。矢印は「呼ぶ/参照する」。principle-* は poteto-mode から全部参照されるので、ここでは他スキルからの参照だけ描いた。

色: 緑 = 入口、紫 = ワークフロー(サブエージェントを使う)、橙 = 文章・品質、灰 = 設定・その他。六角形はエージェント定義(`plugin/agents/`)。

```mermaid
flowchart TB
  classDef entry fill:#e0f1ec,stroke:#0f7a63,color:#18221f
  classDef wf fill:#ebe8f8,stroke:#5b4bb5,color:#18221f
  classDef q fill:#fbeadf,stroke:#b4581d,color:#18221f
  classDef etc fill:#eef1f0,stroke:#5b6964,color:#18221f
  classDef ag fill:#ffffff,stroke:#5b4bb5,stroke-dasharray:4 3,color:#18221f

  PM[poteto-mode]:::entry
  FIO[figure-it-out]:::entry
  AG{{poteto-agent}}:::ag
  AG --> PM
  PH[poteto-help]:::entry --> PM
  PH --> SP

  PM --> WHY[why]:::wf
  PM --> ARC[architect]:::wf
  PM --> ARN[arena]:::wf
  PM --> INT[interrogate]:::wf
  PM --> SW[swarm]:::wf
  PM --> TDD[tdd]:::wf
  PM --> REF[reflect]:::wf
  PM --> FIO
  PM --> NC[no-comments]:::q
  PM --> UN[unslop]:::q
  PM --> TW[technical-writing]:::q
  PM --> SMW[show-me-your-work]:::q
  PM --> BC[benchmark-checklist]:::q

  FIO --> ARC
  FIO --> ARN
  FIO --> SMW
  ARC --> ARN
  ARC --> INT
  ARC --> WHY
  TEACH[teach]:::wf --> HOW[how]:::wf
  TEACH --> WHY
  TEACH --> UN
  BR[blast-radius]:::wf --> HOW
  BR --> WHY
  BR --> ARN
  BR --> UN
  RC[recall]:::wf --> UN
  RC --> AM[automate-me]:::etc
  AM --> PM
  AM --> UN

  NC --> CS{{comment-sicko}}:::ag
  CS -. 疑わしい注釈を調べる .-> WHY
  TW --> UN
  SMW --> UN

  SP[setup-pstack]:::etc --> CVS[create-verification-skill]:::etc
  CVS <--> MVS[maintain-verification-skill]:::etc
  SP --> CFVS[create-formal-verification-skill]:::etc
  CFVS <--> MFVS[maintain-formal-verification-skill]:::etc
  PTS[principle-type-system-discipline]:::etc --> TS[typescript-best-practices]:::etc
  PEN[principle-explain-the-number]:::etc --> BC
```

poteto-help は質問に応じてほぼ全スキルを案内するので、図では poteto-mode と setup-pstack への矢印だけ描いた。bro、make-bot-ui、correct、ketchup、ketchup-video、sharpen、in-your-own-words を参照しているのは poteto-help だけ。

## 3. 各ワークフローのエージェントの流れ

括弧内は `pstack-models.md` の役割の既定モデル。どれも `run_in_background: true` で並列に起動し、親が結果をまとめる。

### how(仕組みの説明)

読み取り専用のサブエージェント 1 体が、探索と説明を一度に済ませる。poteto-mode からは呼ばれず、人が `/how` と送ったときと teach から使う。

```mermaid
flowchart LR
  A[問いを受け取る] --> E["explainer 1 体<br/>(読み取り専用)"]
  E --> P[提示]
```

### why(経緯・理由の調査)

コードではなく記録から答える。対象を入れたコミットと PR の議論、その後の変更を読み、足りなければ他の情報源も見る。サブエージェントは使わない。

```mermaid
flowchart LR
  A[対象を特定] --> B["記録を読む<br/>コミット / PR の議論"]
  B -->|記録が薄い| C[他の情報源]
  B --> D["提示<br/>引用・推測の明示・記録に無いこと"]
  C --> D
```

### arena(案の競作)

同じ課題を複数モデルに解かせ、土台を選んで他案の良い所を移植。

```mermaid
flowchart LR
  A[課題と採点基準を決める] --> B["候補 ×N<br/>(fable / opus / sonnet)<br/>各自の worktree"]
  B --> C["cross-judge<br/>(別モデル)"]
  C --> D[土台を選ぶ]
  D --> E[負けた案から移植]
  E --> F[検証]
```

### architect(実装前の設計)

変更が触るシステムをすべて追い、違う形の案を 2 つ描いて、状態の持ち主が 1 つに決まる方を選ぶ。大きい設計や意見が割れる設計は arena に回す。回避策が繰り返し出たら、継ぎはぎせずに設計し直す。

```mermaid
flowchart LR
  A[影響するシステムを追う] --> B["案を 2 つ描く<br/>(大きければ arena)"]
  B --> C[単純な方を選ぶ]
  C -->|回避策が繰り返す| B
```

### interrogate(敵対的レビュー)

別々の観点のレビュアーが同時に突っ込み、最後に親が判断。

```mermaid
flowchart LR
  A[範囲と意図を明示] --> B["reviewer ×3<br/>(fable / opus / sonnet)"]
  B --> C[統合]
  C --> D["親の判断<br/>Act On / Consider / Dismissed"]
```

### swarm(並列ワーカー)

分担・競争・混合の 3 形。Cursor のクラウドの代わりに手元の worktree で、同時 5 体程度。

```mermaid
flowchart LR
  A["枠組み<br/>完了条件・形・N"] --> B["worker ×N (opus)<br/>isolation: worktree"]
  B --> C["集約<br/>PASS / ISSUES / BLOCKED"]
  C --> D[報告 1 本]
```

### reflect(振り返り)

会話ログ全体を読み、長く通用する学びを既存スキルの修正に落とす。

```mermaid
flowchart LR
  A[会話ログを読む] --> B[長く通用する学びを残す]
  B --> C{検査で縛れるか}
  C -->|はい| D[Backlog]
  C -->|いいえ| E[承認後にスキルを修正]
```

### no-comments(コメント削除)

comment-sicko は報告だけ。修正は親がする。

```mermaid
flowchart LR
  A[差分・範囲] --> B{{comment-sicko}}
  B -->|怪しい理由付け| H[コードを追う / why で確認]
  B --> R["報告<br/>削除数・MUST KILL"]
  R --> F[親が修正]
```

## 4. 例: Feature playbook の一周

poteto-mode が「新機能」と判定したときの手順(`plugin/skills/poteto-mode/playbooks/feature.md`)。スキルがどの順で連鎖するかが一番よく見える。

```mermaid
flowchart LR
  S1["1. 影響範囲を<br/>追って把握"] --> S2["2. architect<br/>(内部で arena)"]
  S2 --> S3["3. 進捗チェック<br/>ポイントを書く"]
  S3 --> S4["4. 実装を委譲<br/>poteto-agent (opus)"]
  S4 --> S5["5. 実物で検証"]
  S5 --> S6["6. 小さな<br/>コミットに整理"]
  S6 --> S7["7. 設計に異論<br/>→ interrogate"]
  S7 --> S8["8. Opening a PR<br/>(no-comments・<br/>technical-writing)"]
```

| playbook(一部) | 主に呼ぶスキル |
|---|---|
| Investigation | why |
| Bug fix | why → architect → tdd |
| Feature / Refactoring | architect → interrogate |
| Autonomous run / Orchestrate | swarm, show-me-your-work |
| 当てはまる型なし・大規模 | figure-it-out(architect, arena, show-me-your-work) |

## 5. このプラグインの作られ方

```mermaid
flowchart LR
  UP["cursor/plugins<br/>pstack"] -->|sync-upstream.sh| V["vendor/pstack/<br/>無改造"]
  V --> B["build.py<br/>パス・Task→Agent・<br/>モデル名を置換"]
  O["overrides/<br/>setup-pstack"] --> B
  B -->|Cursor 固有の記述が残らないか検査| P["pstack-cc/plugin/<br/>生成物"]
  P --> M["/plugin install<br/>pstack@lab"]
```

Cursor 固有の記述(`.cursor/` のパスや Cursor のモデル名など)が変換されずに残ると build が失敗する。上流が文を言い換えただけなら止まらない。

---

2 の参照関係は SKILL.md 内の名指しを grep で拾ったもので、本文で間接的に触れているだけの参照は漏れている可能性がある。
