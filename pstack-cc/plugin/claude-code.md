# pstack on Claude Code

pstack was written for Cursor. This plugin is an automatic conversion of it (see `pstack-cc/` in the source repo). Paths, tool names and model names were rewritten where the change is mechanical. For everything else, read a Cursor term in a skill as the Claude Code equivalent below.

## Tools

| Cursor (in the skills) | Claude Code |
|---|---|
| `Task` tool (any mention the build missed) | The Agent tool. |
| `subagent_type: "poteto-agent"`, `"comment-sicko"` | Agents shipped by this plugin. The Agent tool may list them with a `pstack:` prefix (`pstack:poteto-agent`). Use the name exactly as the tool lists it. |
| `readonly: true` | No such flag. Use the `Explore` agent type when the job is read-only search, or tell the subagent in its prompt that it must not edit files. |
| `readonly: false` / "agent mode" | The default. Nothing to set. |
| `run_in_background: true` | Same parameter. You are notified when the agent finishes, so there is no `Await` step. |
| `environment: "cloud"` | No Cursor cloud. Run the worker locally with `isolation: "worktree"` and `run_in_background: true`. Keep the fan-out small (about 3–5 at once) because every worker uses this machine. |
| `environment: "local"` | Omit `isolation`. |
| `cloud_base_branch` | Put the branch in the brief and have the worker check it out in its worktree first. |
| `Shell` | The Bash tool. |

## Models

The build replaced Cursor model slugs with Claude Code aliases:

| Cursor default | Here |
|---|---|
| `claude-opus-5-5-xhigh` / `-max` / `-medium` | `opus` |
| `grok-4.7-xhigh-fast` | `sonnet` |

- Pass the alias as the Agent tool's `model`.
- If the tool rejects an alias, omit `model` for that subagent so it runs on the parent model, and say so once.
- Upstream's reasoning budgets (`unlimited`, `large`, `medium`, `small`, and effort suffixes such as `-xhigh`) have no Claude Code equivalent. Ignore them.
- A skill that talks about model families or slug prefixes means these aliases. Each alias counts as its own family.
- Panels (arena, architect, interrogate) were designed for different vendors. Here they are different Claude models, so candidates will be less diverse. The rest of each workflow is unchanged.

Per-role overrides live in `~/.claude/pstack-models.md`, written by `/setup-pstack`. A value of `inherit-parent` or `auto` means omit `model`.

## Transcripts

Claude Code stores chat history as JSONL:

```
~/.claude/projects/<slug>/<session-id>.jsonl
~/.claude/projects/<slug>/<session-id>/subagents/*.jsonl
```

`<slug>` is the project's absolute path with every `/` (and any other character that is not a letter or digit) turned into `-`. For example, `/home/you/proj` becomes `-home-you-proj`. Run `ls ~/.claude/projects/` to confirm. Stay inside the current project's directory unless the user asks otherwise.

To find the current session's transcript, take the most recently modified `*.jsonl` in that directory and check that one of its first `"type":"user"` lines holds the conversation's opening prompt.

## Paths to pstack's own files

Upstream runs from inside the pstack repository, so it names pstack files by repository path (`pstack/skills/swarm/SKILL.md`) and re-reads them from trunk with `git show origin/main:pstack/...`. Here pstack is an installed plugin, and the build rewrote those paths to `<pstack plugin root>/skills/...`.

`<pstack plugin root>` is the directory two levels above any pstack skill's base directory, where this file lives. Read files there with the Read tool or `cat`. The installed copy is the current version, so there is no trunk to re-read. A `git show origin/main:` path that does not start with `pstack/` points into the user's own repository and works as written.

## Other Cursor mentions left in the text

| The skill says | In Claude Code |
|---|---|
| Cursor's built-in `create-skill` skill | Use the `skill-creator` skill if it is installed. Otherwise write the `SKILL.md` directly, following the playbook's rules. |
| Cursor's `/loop` command | Claude Code has `/loop` too. |
| Cursor's built-in `babysit` skill | Does not exist here. Just follow the pstack playbook. |
| "list the available MCPs from the Cursor environment" / the `mcps/` directory | MCP tools show up as `mcp__<server>__<tool>` in your tool list. Use that list. |
| "a Cursor restart" | A Claude Code restart or `/clear`. Background agents do not survive it. |
| `/add-plugin pstack`, or installing from Customize in the sidebar (`/poteto-help`) | `/plugin marketplace add souljazzfunk/lab`, then `/plugin install pstack@lab`. |
| Links to `https://github.com/cursor/plugins/blob/main/pstack/docs/guide/...` (`/poteto-help`) | Upstream's guide is not shipped in this plugin. Read it at that URL with a web fetch tool if you have one, and remember it describes Cursor. |

## Not converted

These rely on Cursor features that Claude Code does not have. The text is kept but will not work as written:

- **Cursor automations and routines** (the `make-bot-ui` webhook URL, and upstream's `automations/`, which is not shipped here).
- **Custom Modes.** `/poteto-mode` cannot be pinned. Invoke it again when you start a new task. Ignore `/poteto-help`'s advice about Option+Enter, Alt+Enter, and Use as Mode.
- **`cursor-team-kit` skills** (`control-ui`, `control-cli`) named by some playbooks. Use your project's own verification skill (`/create-verification-skill`).
- **Cursor cloud agents** at scale. Local worktrees stand in, as above.
