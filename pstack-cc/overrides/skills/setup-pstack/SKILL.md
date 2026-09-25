---
name: setup-pstack
description: Configure which models pstack uses per role. Writes ~/.claude/pstack-models.md, which the other pstack skills read to override their defaults. Use for /setup-pstack, "configure pstack models", or changing pstack's model choices.
---

# Setup pstack (Claude Code)

Write `~/.claude/pstack-models.md`, the file the other pstack skills read for their per-role model.

This replaces upstream's Cursor version, which writes an always-applied `.mdc` rule and tunes reasoning effort per slug. Claude Code has neither, so this version only picks a model alias per role.

## Steps

### 1. Detect available models

List the values the Agent tool's `model` parameter accepts in this session (typically `opus`, `sonnet`, `haiku`, and on some plans `fable`). Only write values from that list, plus `inherit-parent`, which means "omit `model` so the subagent runs on the parent's model".

### 2. Load current state

If `~/.claude/pstack-models.md` exists, read it and treat its role values as the current choices. Otherwise start from the defaults in step 4. Drop any line whose role is not in step 4 and tell the user.

### 3. Show the roles and confirm

Show every role with its model. Ask with AskUserQuestion whether to accept as-is, switch everything to `inherit-parent` (cheapest to reason about: every subagent uses the parent model), or change specific roles. For panel roles (arena runners, architect runners, interrogate reviewers) the value is a list, and one subagent runs per entry, so the list length sets the count. Prefer distinct aliases within a panel so the candidates differ.

### 4. Write the file

Overwrite the whole file so re-runs stay idempotent. Shape:

```
# pstack model configuration (Claude Code). One line per role. Delete a line to fall back to the skill default.
# `inherit-parent`: omit the Agent tool's `model`, so the role runs on the parent model.
feature, refactoring: sonnet
bug-fix: sonnet
perf-issue: sonnet
hillclimb: sonnet
judgment and prose: opus
hardest tasks: opus
how explorer: sonnet
how explainer: opus
why investigators: sonnet
why synthesizer: opus
reflect tooling: fable
reflect judgment, divergent, synthesizer: opus
arena runners: opus, fable, sonnet
arena cross-judge pool: opus, fable, sonnet
swarm workers: sonnet
architect runners: opus, fable, sonnet
interrogate reviewers: opus, fable, sonnet
```

### 5. Confirm

Tell the user the file was written. Skills read it each time they run, so it applies right away.

### 6. Offer a verification skill (optional)

Check whether the project has a way to drive the real app for proof (a `verify-*` skill, or an existing harness). If not, offer once: "want a project-local verification skill, so agents can drive the app the way a user does and prove changes work? I can generate one with /create-verification-skill." On yes, invoke `/create-verification-skill`. On no, move on without pushing.
