# pstack スキル地図

[English](skill-map.en.md)

Cursor 用プラグイン pstack を Claude Code 向けに変換したもの(`pstack-cc/plugin/`)にある、スキル 47 個・エージェント 2 個の関係と、各スキルがサブエージェントをどう動かすかの図。

## 1. 全体像

入口は `/poteto-mode`。仕事の種類で playbook を選び、各ステップから how / architect などのワークフロースキルを呼ぶ。どのスキルも最初に `claude-code.md`(Cursor → Claude Code 対応表)を読み、モデル選択は `~/.claude/pstack-models.md` に従う。

```mermaid
flowchart LR
  U([ユーザー]) --> PM["/poteto-mode<br/>(poteto-agent 経由も可)"]
  PM --> PB{"playbook を選ぶ<br/>23 種"}
  PM -. 大規模・当てはまる型なし .-> FIO["figure-it-out"]
  PB --> WF["ワークフロースキル<br/>how / why / architect / arena<br/>interrogate / swarm / tdd"]
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

  PM --> HOW[how]:::wf
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

  FIO --> ARC
  FIO --> ARN
  FIO --> SMW
  ARC --> ARN
  ARC --> HOW
  ARC --> INT
  ARC --> WHY
  WHY --> HOW
  TEACH[teach]:::wf --> HOW
  TEACH --> WHY
  TEACH --> UN
  BR[blast-radius]:::wf --> HOW
  BR --> WHY
  BR --> ARN
  BR --> UN
  RC[recall]:::wf --> WHY
  RC --> UN
  RC --> AM[automate-me]:::etc
  AM --> PM
  AM --> UN

  NC --> CS{{comment-sicko}}:::ag
  CS -. 疑わしい注釈を調べる .-> HOW
  CS -.-> WHY
  TW --> UN
  SMW --> UN

  SP[setup-pstack]:::etc --> CVS[create-verification-skill]:::etc
  CVS <--> MVS[maintain-verification-skill]:::etc
  PTS[principle-type-system-discipline]:::etc --> TS[typescript-best-practices]:::etc
```

参照のない単独スキルは bro、make-bot-ui。

## 3. 各ワークフローのエージェントの流れ

括弧内は `pstack-models.md` の役割の既定モデル。どれも `run_in_background: true` で並列に起動し、親が結果をまとめる。

### how(仕組みの説明)

単純な質問は explainer 1 体だけ。複雑なら 2〜4 観点で探索してから統合。

```mermaid
flowchart LR
  A[複雑さを判定] -->|単純| E1["explainer<br/>(opus)"]
  A -->|複雑| X1["explorer ×2〜4<br/>(sonnet, 並列)"]
  X1 --> E2["explainer が統合<br/>(opus)"]
  E1 --> P[提示]
  E2 --> P
```

### why(経緯・理由の調査)

使える MCP を調べ、証拠の種類ごとに調査役を 1 体ずつ立てる。

```mermaid
flowchart LR
  A[対象と問いを確定] --> B[コード上の起点を特定]
  B --> C["investigator ×N (sonnet)<br/>git / チケット / 文書 / チャット / 監視"]
  C --> D["synthesizer (opus)"]
  D --> E[提示]
```

### arena(案の競作)

同じ課題を複数モデルに解かせ、土台を選んで他案の良い所を移植。

```mermaid
flowchart LR
  A[課題と採点基準を決める] --> B["候補 ×N<br/>(opus / fable / sonnet)<br/>各自の worktree"]
  B --> C["cross-judge<br/>(別モデル)"]
  C --> D[土台を選ぶ]
  D --> E[負けた案から移植]
  E --> F[検証]
```

### architect(実装前の設計)

設計スケッチの段階で arena を呼ぶ。実装が破綻したら how からやり直し。

```mermaid
flowchart LR
  A[問題を把握] --> B["スケッチ = arena<br/>(architect runners)"]
  B --> C[合意 任意]
  C --> D[スケッチに沿って実装]
  D -->|同じ歪みが繰り返す| E[スケッチを捨てる]
  E -->|how で再把握| B
```

### interrogate(敵対的レビュー)

別々の観点のレビュアーが同時に突っ込み、最後に親が判断。

```mermaid
flowchart LR
  A[範囲と意図を明示] --> B["reviewer ×3<br/>(opus / fable / sonnet)"]
  B --> C[統合]
  C --> D["親の判断<br/>Act On / Consider / Dismissed"]
```

### swarm(並列ワーカー)

分担・競争・混合の 3 形。Cursor のクラウドの代わりに手元の worktree で、同時 5 体程度。

```mermaid
flowchart LR
  A["枠組み<br/>完了条件・形・N"] --> B["worker ×N (sonnet)<br/>isolation: worktree"]
  B --> C["集約<br/>PASS / ISSUES / BLOCKED"]
  C --> D[報告 1 本]
```

### reflect(振り返り)

会話ログを 3 つの観点で読み、学びを既存スキルの修正に落とす。

```mermaid
flowchart LR
  A[会話ログ JSONL を特定] --> B["Judgment (opus)<br/>Tooling (fable)<br/>Divergent (opus)"]
  B --> C["synthesizer (opus)"]
  C --> D[構造で縛れるか確認]
  D --> E[スキルを修正]
```

### no-comments(コメント削除)

comment-sicko は報告だけ。修正は親がする。

```mermaid
flowchart LR
  A[差分・範囲] --> B{{comment-sicko}}
  B -->|怪しい理由付け| H[how / why で確認]
  B --> R["報告<br/>削除数・MUST KILL"]
  R --> F[親が修正]
```

## 4. 例: Feature playbook の一周

poteto-mode が「新機能」と判定したときの手順(`plugin/skills/poteto-mode/playbooks/feature.md`)。スキルがどの順で連鎖するかが一番よく見える。

```mermaid
flowchart LR
  S1["1. how<br/>影響範囲を把握"] --> S2["2. architect<br/>(内部で arena)"]
  S2 --> S3["3. 進捗チェック<br/>ポイントを書く"]
  S3 --> S4["4. 実装を委譲<br/>poteto-agent (sonnet)"]
  S4 --> S5["5. 実物で検証"]
  S5 --> S6["6. 小さな<br/>コミットに整理"]
  S6 --> S7["7. 設計に異論<br/>→ interrogate"]
  S7 --> S8["8. Opening a PR<br/>(no-comments・<br/>technical-writing)"]
```

| playbook(一部) | 主に呼ぶスキル |
|---|---|
| Investigation | how, why |
| Bug fix | how, why → architect → tdd |
| Feature / Refactoring | how → architect → interrogate |
| Autonomous run / Orchestrate | swarm, show-me-your-work |
| 当てはまる型なし・大規模 | figure-it-out(architect, arena, show-me-your-work) |

## 5. このプラグインの作られ方

```mermaid
flowchart LR
  UP["cursor/plugins<br/>pstack"] -->|sync-upstream.sh| V["vendor/pstack/<br/>無改造"]
  V --> B["build.py<br/>パス・Task→Agent・<br/>モデル名を置換"]
  O["overrides/<br/>setup-pstack"] --> B
  B -->|当たり回数を検査| P["pstack-cc/plugin/<br/>生成物"]
  P --> M["/plugin install<br/>pstack@lab"]
```

置換ルールが上流の文章変更で当たらなくなると build が失敗する。

---

2 の参照関係は SKILL.md 内の名指しを grep で拾ったもので、本文で間接的に触れているだけの参照は漏れている可能性がある。
