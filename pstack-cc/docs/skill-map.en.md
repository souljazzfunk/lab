# pstack skill map

[日本語](skill-map.ja.md)

Diagrams of how the 47 skills and 2 agents in `pstack-cc/plugin/` (the Claude Code build of the Cursor plugin pstack) relate to each other, and how each skill drives its subagents.

## 1. Overview

The entry point is `/poteto-mode`. It picks a playbook for the kind of work, and each playbook step calls workflow skills such as how and architect. Every skill reads `claude-code.md` (the Cursor → Claude Code mapping) first, and picks models from `~/.claude/pstack-models.md`.

```mermaid
flowchart LR
  U([User]) --> PM["/poteto-mode<br/>(or via poteto-agent)"]
  PM --> PB{"Pick a playbook<br/>23 kinds"}
  PM -. large or no matching playbook .-> FIO["figure-it-out"]
  PB --> WF["Workflow skills<br/>how / why / architect / arena<br/>interrogate / swarm / tdd"]
  PB --> Q["Finishing skills<br/>unslop / technical-writing<br/>no-comments / show-me-your-work"]
  PM --> PR["24 principle-* skills<br/>(grounds for decisions)"]
  WF --> SA[["Subagents<br/>(parallel, worktrees)"]]
  SP["/setup-pstack"] -->|writes| CFG[("~/.claude/pstack-models.md")]
  CFG -.read by.-> WF
  CC[("claude-code.md")] -.read first by every skill.-> PM
```

## 2. How skills reference each other

Extracted from places where a SKILL.md names another skill. An arrow means "calls or refers to". poteto-mode refers to every principle-* skill, so only references from other skills are drawn.

Colors: green = entry points, purple = workflows (use subagents), orange = writing and quality, grey = setup and other. Hexagons are agent definitions (`plugin/agents/`).

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
  CS -. checks doubtful comments .-> HOW
  CS -.-> WHY
  TW --> UN
  SMW --> UN

  SP[setup-pstack]:::etc --> CVS[create-verification-skill]:::etc
  CVS <--> MVS[maintain-verification-skill]:::etc
  PTS[principle-type-system-discipline]:::etc --> TS[typescript-best-practices]:::etc
```

bro and make-bot-ui stand alone with no references.

## 3. Agent flow in each workflow

Models in parentheses are the role defaults from `pstack-models.md`. Every workflow launches its agents in parallel with `run_in_background: true`, and the parent merges the results.

### how (explaining how something works)

A simple question gets one explainer. A complex one is explored from 2 to 4 angles first, then merged.

```mermaid
flowchart LR
  A[Assess complexity] -->|simple| E1["explainer<br/>(opus)"]
  A -->|complex| X1["explorer x2-4<br/>(sonnet, parallel)"]
  X1 --> E2["explainer merges<br/>(opus)"]
  E1 --> P[Present]
  E2 --> P
```

### why (history and rationale)

Checks which MCPs are available and starts one investigator per kind of evidence.

```mermaid
flowchart LR
  A[Pin down target and question] --> B[Find the code anchor]
  B --> C["investigator xN (sonnet)<br/>git / tickets / docs / chat / observability"]
  C --> D["synthesizer (opus)"]
  D --> E[Present]
```

### arena (competing candidates)

Several models solve the same task. Pick a base, then graft the best parts of the others into it.

```mermaid
flowchart LR
  A[Set task and rubric] --> B["candidate xN<br/>(opus / fable / sonnet)<br/>own worktree each"]
  B --> C["cross-judge<br/>(different model)"]
  C --> D[Pick a base]
  D --> E[Graft from the losers]
  E --> F[Verify]
```

### architect (design before code)

Calls arena for the design sketch. If implementation breaks down, start over from how.

```mermaid
flowchart LR
  A[Ground the problem] --> B["Sketch = arena<br/>(architect runners)"]
  B --> C[Agree, optional]
  C --> D[Implement against the sketch]
  D -->|same friction keeps repeating| E[Scrap the sketch]
  E -->|re-ground with how| B
```

### interrogate (adversarial review)

Reviewers attack from separate angles at once, and the parent makes the final call.

```mermaid
flowchart LR
  A[State scope and intent] --> B["reviewer x3<br/>(opus / fable / sonnet)"]
  B --> C[Synthesize]
  C --> D["Lead judgment<br/>Act On / Consider / Dismissed"]
```

### swarm (parallel workers)

Three shapes: partition, race, or both. Runs in local worktrees instead of Cursor's cloud, about 5 at a time.

```mermaid
flowchart LR
  A["Frame<br/>done predicate, shape, N"] --> B["worker xN (sonnet)<br/>isolation: worktree"]
  B --> C["Aggregate<br/>PASS / ISSUES / BLOCKED"]
  C --> D[One report]
```

### reflect (retrospective)

Reads the transcript through three lenses and turns each learning into an edit to an existing skill.

```mermaid
flowchart LR
  A[Locate transcript JSONL] --> B["Judgment (opus)<br/>Tooling (fable)<br/>Divergent (opus)"]
  B --> C["synthesizer (opus)"]
  C --> D[Can structure enforce it?]
  D --> E[Edit the skill]
```

### no-comments (comment removal)

comment-sicko only reports. The parent makes the fixes.

```mermaid
flowchart LR
  A[Diff or scope] --> B{{comment-sicko}}
  B -->|doubtful justification| H[Check with how / why]
  B --> R["Report<br/>deletions, MUST KILL flags"]
  R --> F[Parent fixes]
```

## 4. Example: one pass through the Feature playbook

The steps poteto-mode follows for a new feature (`plugin/skills/poteto-mode/playbooks/feature.md`). This shows most clearly the order in which skills chain.

```mermaid
flowchart LR
  S1["1. how<br/>map the affected area"] --> S2["2. architect<br/>(arena inside)"]
  S2 --> S3["3. write the<br/>throughput checkpoint"]
  S3 --> S4["4. delegate code<br/>poteto-agent (sonnet)"]
  S4 --> S5["5. verify on the<br/>real surface"]
  S5 --> S6["6. split into<br/>small commits"]
  S6 --> S7["7. contested design<br/>→ interrogate"]
  S7 --> S8["8. Opening a PR<br/>(no-comments,<br/>technical-writing)"]
```

| Playbook (selection) | Main skills called |
|---|---|
| Investigation | how, why |
| Bug fix | how, why → architect → tdd |
| Feature / Refactoring | how → architect → interrogate |
| Autonomous run / Orchestrate | swarm, show-me-your-work |
| No matching playbook, or large | figure-it-out (architect, arena, show-me-your-work) |

## 5. How this plugin is built

```mermaid
flowchart LR
  UP["cursor/plugins<br/>pstack"] -->|sync-upstream.sh| V["vendor/pstack/<br/>unmodified"]
  V --> B["build.py<br/>rewrites paths,<br/>Task→Agent, model names"]
  O["overrides/<br/>setup-pstack"] --> B
  B -->|checks hit counts| P["pstack-cc/plugin/<br/>generated"]
  P --> M["/plugin install<br/>pstack@lab"]
```

If upstream wording changes so a rewrite rule stops matching, the build fails.

---

The references in section 2 were collected by grepping SKILL.md files for skill names, so references that only mention a skill indirectly may be missing.
