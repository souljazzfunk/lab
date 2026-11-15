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

If `~/.claude/pstack-models.md` exists, read it and treat its role values as the current choices. Otherwise start from the defaults in step 4. Drop any line whose role is not in step 4, such as `how explorer` or `why investigators` (retired roles), and tell the user.

A file without the `# defaults: 2` line comes from an older setup. That setup wrote a line for every role, so some of its values are old defaults, not choices. Before step 3, replace these values:

- `sonnet` in `feature, refactoring`, `bug-fix`, `perf-issue`, `hillclimb`, `reflect tooling`, or `swarm workers` takes the role's step 4 default.
- `opus` in `hardest tasks` takes the role's step 4 default.
- In a panel role (`arena runners`, `arena cross-judge pool`, `architect runners`, `interrogate reviewers`), a list of exactly `opus` and `sonnet`, in either order, takes the role's step 4 list.

Every other value is the user's choice and stays, including every `inherit-parent` or `auto` value. Tell the user which values you replaced.

### 3. Show the roles and confirm

Show every role with its model. Ask with AskUserQuestion whether to accept as-is, switch everything to `inherit-parent` (cheapest to reason about: every subagent uses the parent model), or change specific roles. For panel roles (arena runners, architect runners, interrogate reviewers) the value is a list, and one subagent runs per entry, so the list length sets the count. Prefer distinct aliases within a panel so the candidates differ.

### 4. Write the file

Overwrite the whole file so re-runs stay idempotent. Always write the `# defaults: 2` line. If `fable` is not in the step 1 list, write `opus` wherever the shape below has `fable`. Shape:

```
# pstack model configuration (Claude Code). One line per role. Delete a line to fall back to the skill default.
# `inherit-parent`: omit the Agent tool's `model`, so the role runs on the parent model.
# defaults: 2
feature, refactoring: opus
bug-fix: opus
perf-issue: opus
hillclimb: opus
judgment and prose: opus
hardest tasks: fable
reflect tooling: opus
reflect judgment, divergent, synthesizer: opus
arena runners: fable, opus, sonnet
arena cross-judge pool: fable, opus, sonnet
swarm workers: opus
architect runners: fable, opus, sonnet
interrogate reviewers: fable, opus, sonnet
```

### 5. Confirm

Tell the user the file was written. Skills read it each time they run, so it applies right away.

### 6. Offer a verification skill (optional)

Check whether the project has a way to drive the real app for proof (a `verify-*` skill, or an existing harness). If not, offer once: "want a project-local verification skill, so agents can drive the app the way a user does and prove changes work? I can generate one with /create-verification-skill." On yes, invoke `/create-verification-skill`. On no, move on without pushing.

### 7. Offer a formal verification skill (optional)

Check whether the project already has a formal verification skill (a project skill that runs a model checker, a proof, or another verifier against the code). If not, offer once: "want a formal verification skill, so agents can prove a key property of your code holds in every case in scope, not only the cases tests reach? I can generate one with /create-formal-verification-skill." On yes, invoke `/create-formal-verification-skill`. On no, move on without pushing.
