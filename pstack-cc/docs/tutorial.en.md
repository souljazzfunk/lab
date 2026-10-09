# Tutorial: learn pstack by running it

[日本語](tutorial.ja.md)

Lauren Tan (poteto), the author of pstack, explains how to use it in three sources:

- The post [The Complete Guide to pstack Pt. 1](https://x.com/poteto/status/2094457600259842065), about verification skills.
- The post [The Complete Guide to pstack Pt. 2](https://x.com/poteto/status/2097732320606507506), about research, planning, prototyping, and architecture.
- A talk about building an environment where you can trust your agents.

In this tutorial, we run the workflows from those sources one by one in your own repository. At the end you have a verification skill for your app and one change built with it.

The tutorial has three parts. Part 1 follows Pt. 1, part 2 follows Pt. 2, and part 3 follows the talk. Each part takes about an hour, and you can do the parts on different days.

## Notation

This tutorial writes skills in short form, such as `/how`. The full name is `/pstack:how`. Type `/how` and the completion list shows `/pstack:how`.

`/verify-<app>` is the verification skill we create in part 1, where `<app>` is the name of your app. It is the same thing as `/control-app` in the posts.

Replace `<feature>`, `<subsystem>`, and other placeholders in the prompts with names from your repository.

## Get ready

1. Pick the repository of an app you work on. A browser app, an Electron app, a CLI, or an API all work. You must be able to start it locally.
2. Create a practice branch.

    ```bash
    cd <your repository>
    git switch -c pstack-tutorial
    ```

3. Pick one small task. A feature that takes about 30 minutes, or a bug with known repro steps, works well.
4. Start Claude Code and install pstack.

    ```
    /plugin marketplace add souljazzfunk/lab
    /plugin install pstack@lab
    ```

5. Restart Claude Code. Type `/poteto`. If the completion list shows `/pstack:poteto-mode`, you are ready.

pstack runs on its default models. Run `/setup-pstack` only when you want to change them.

## Part 1: let agents check their own work

Pt. 1 makes one point. If an agent cannot check its own work, you become the checker and spend your day watching it. In part 1 we build the tool that does the checking.

### 1. Create a verification skill

```
/create-verification-skill
```

The agent first reads the repository. It works out how to start the app, how to drive it, and how to capture evidence from the code and the README. It asks you only what the code does not show.

When it finishes, you have these files:

- `.claude/skills/verify-<app>/SKILL.md`, with the sections Launch, Doctor, Drive, Evidence, and Cleanup.
- `.claude/skills/verify-<app>/features/README.md` and three to five files, one per feature. This is the Feature Map.

The agent has already run the new skill once from start to end. It launched the app, ran `doctor`, drove one feature, saved evidence, and cleaned up. Check that the reply names where the screenshots or logs were saved.

Restart Claude Code, and `/verify-<app>` shows up in the completion list.

### 2. Read the Feature Map

Open `features/README.md`. It lists the main features of the app and links to one file per feature.

Open one feature file. It has these four headings:

- `Sub-features`
- `How to get to it (user POV)`
- `Driving it with <harness>`
- `Gotchas`

The author calls this "materialized memory". It records how a user reaches each feature, so agents do not have to feel their way around the app. Fix anything wrong now. The Feature Map lives in the repository, and the whole team shares it.

### 3. Try the verification CLI

The pstack principle "Build the Lever" says to give agents tools rather than markdown. For a verification skill, the tool is a small CLI that drives the app.

```
use /verify-<app> to start the app, run doctor, and take a screenshot of the first screen
```

The agent runs the CLI that ships with the skill instead of writing a new script each time. The reply names the commands it ran and where it saved the screenshot.

If the CLI is missing a command, have the agent add it. Pt. 1 asks for these properties in an agent-friendly CLI:

```
/poteto-mode add a command for <missing action> to the verify-<app> CLI. give it rich --help text and JSON output. add --dry-run if it has destructive side effects. make error messages say what to do instead
```

### 4. Build a feature with verification

Now we build the task you picked. We use the prompt from Pt. 1 as is.

```
/poteto-mode build <description of feature, any useful context>. use /verify-<app> to verify your changes and show me a video and screenshots as proof
```

The agent picks a playbook from the kind of work, **Feature** for a new feature and **Bug fix** for a bug. It opens a todo list, and the first items are the playbook steps. A step it skips stays in the list as `skip: <reason>`.

When it finishes, the reply contains these:

- What it built and which data shape it chose.
- The principles behind its decisions, by name (for example, Prove It Works).
- Where the evidence from `/verify-<app>` is saved.

Look at the evidence yourself. If a screenshot does not show the change, say so and have the agent try again.

If you picked a bug, use the prompt from example 4 in Pt. 2:

```
/poteto-mode repro this with /verify-<app>. if it repros on main, fix it and show me a video as proof
```

### 5. Check in parallel with `/swarm`

`/swarm` splits one check across many agents. Here we use the Feature Map to check that the change did not break other features.

```
/swarm 4 workers. use /verify-<app> to check the features in features/, split between you. report PASS, ISSUES, or BLOCKED for anything this branch broke
```

The agent runs the workers in parallel, each in its own worktree. At the end you get one table with a result per feature.

The perf example from Pt. 1 has the same shape:

```
/poteto-mode improve the initial loading time of our app. first use /verify-<app> to take a trace of the status quo, and identify opportunities for improvement. then do a targeted fix and use /verify-<app> + a /swarm to confirm the win
```

In the posts, `/swarm` runs on Cursor's cloud. The Claude Code version runs on your machine, so keep it to five workers at once.

### 6. Maintain the verification skill

The Feature Map goes stale as soon as the app changes.

```
/maintain-verification-skill
```

The agent reads the source for each feature, drives the real app, and looks for places where the Feature Map is wrong. The result is `clean`, `changed`, or `blocked`. For `changed`, the fixes come as one PR.

The author recommends running this at least once a day. Pt. 1 treats the verification skill as critical infrastructure, important enough to give it an on-call rotation.

## Part 2: understand first, and plan with code

Pt. 2 makes two points. The better the context you give an agent, the better its work. And you plan with code, not with abstract documents.

### 7. Have the agent restate the problem

If you state your own guess first, the agent follows it. So we have the agent restate the problem first. Use a bug report, an issue, or a Slack thread your team received.

```
/poteto-mode read this issue. restate in your own words and in plain english what you think the underlying issue is
```

Read the restatement. If the agent fixed on a red herring, correct it now, before it writes any code.

### 8. Ask `/how` and `/why`

```
/how is <subsystem> implemented?
```

The agent judges how complex the question is. For a complex one, it runs two to four explorers in parallel and merges their findings into one explanation. The headings are Overview, Key Concepts, How It Works, Where Things Live, and Gotchas.

```
/why are we still stuck on <an old dependency or an odd implementation>?
```

`/why` reads git history and PRs, plus the MCP servers connected to Claude Code, such as Slack, Linear, Notion, and Sentry. It skips sources that are not connected and says so in the answer. The answer cites the commits and PRs it used.

### 9. Have `/teach` explain

Ask the agent to explain the choices behind the change from part 1.

```
/teach me why you implemented step 4 this way and not another way. what were the tradeoffs you made and why?
```

`/teach` runs `/how` and `/why`. The answer starts short and goes deeper as you ask. If a point does not convince you, keep asking. The author notes that explaining also corrects the agent's own understanding.

### 10. Bring back context with `/recall`

Quit Claude Code and start a new conversation. The new conversation does not know what the old one did.

```
/recall the work i did yesterday on <feature>
```

The agent reads your past chats in `~/.claude/projects/` and checks the related PRs and issues. The reply has this shape:

- **Capsule.** Where things stand, in five bullets or fewer.
- **Threads.** One line per thread of work, each with a status tag such as `[open PR #N]` or `[in flight <branch>]`.
- **Problems.** The problems that keep coming back.
- **Next move.** The one most useful next action.

### 11. Compare options with prototypes

Pt. 2 warns against taking the agent's first design.

```
/poteto-mode prototype a few options for <feature>. use /verify-<app> and take videos/screenshots for me to review and choose from
```

The agent follows the **Prototype** playbook. It builds throwaway sketches in a scratch directory, apart from production code. For UI, it puts the options behind one switcher so you can compare them.

The reply lists the options it tried, the evidence for each, the tradeoffs, and a recommendation. It also says plainly that the prototype is throwaway. For the real build, ask for it as a Feature, as in step 4.

### 12. Design with `/architect`

For a change that crosses function boundaries, design before you build. This is example 2 from Pt. 2:

```
/poteto-mode we need to add <feature>. /architect this first, and answer any open questions with prototypes. let me review before proceeding.
```

`/architect` runs in five phases:

1. **Ground.** It runs `/how` and `/why` over the systems involved.
2. **Sketch.** Several models (opus and sonnet) each draft a design on their own. A design is a usage sketch, types, function signatures, and a rationale. It needs at least two designs with different structures.
3. **Agree.** The prompt ends with "let me review before proceeding", so it stops here and shows you the design.
4. **Implement.** When you approve, it fills in the sketch.
5. **Scrap.** If the same kind of workaround keeps appearing, or the types need `any` or casts, it throws the sketch away and designs again.

In the Claude Code version, every designer is a Claude model. The Cursor version mixes models from different vendors, so expect less variety here.

### 13. Write the README first

For code that other people will use, writing the usage doc before the code shows its shape. The author started the in-house framework Dune by writing its tutorial, and built `/technical-writing` for that job.

```
/technical-writing write a tutorial for people who will use <feature>. do not implement anything yet
```

The doc you get is written in one Diátaxis mode, tutorial. Each step says what the reader should see. The doc becomes a target the agent can check its implementation against. This tutorial was written with the same skill.

### 14. Turn the design into a plan

Once the design is settled, turn it into a plan to execute.

```
/poteto-mode turn this design into a plan
```

The agent follows the **Multi-phase plan** playbook. The plan file has one section per PR, and every checkbox names the evidence that checks it. Every PR includes steps that drive the real app. The playbook's rule is that passing tests alone do not count as verified.

When the plan is written, the agent stops. It starts executing only when you tell it to go.

## Part 3: build an environment you can trust

The talk argues that the number of agents you can run at once depends on how much you trust their work. More agents without trust means more low-quality PRs and more bugs.

### 15. Encode each correction in structure

By now you have corrected the agent at least once. Make sure the same mistake cannot happen again.

```
/poteto-mode make sure the <mistake> i just corrected cannot happen again. first check whether the code's structure can make it impossible. if not, catch it with lint or CI. write it into rules or skills only as a last resort
```

The talk lists four places to stop a repeat mistake, strongest first:

1. The code's structure and data structures, so the mistake cannot be written.
2. Static analysis, such as lint, the compiler, and CI.
3. Rules and skills, which agents sometimes skip.
4. The style guide, which only human review enforces.

Agents copy the patterns they see in the code. One workaround left in place spreads across the repository in a few weeks. So stop a mistake with structure as soon as you see it.

### 16. Question the comments

The talk describes agents using code comments as an excuse to keep a workaround. The author's framework Dune bans comments for that reason.

```
/no-comments
```

The `comment-sicko` agent checks each comment in this branch's diff. It deletes the comments that should go and fixes the root cause of any workaround a comment was covering. Each comment it keeps comes with a reason.

## Prompts to take with you

These are the examples from the end of Pt. 2, ready to use.

Research an ambiguous bug:

```
/poteto-mode investigate why background workers periodically fail with timeout errors. give me a breakdown of what we know, what data you used, and your best hypotheses.
```

Design a new service boundary:

```
/poteto-mode we need to add rate limiting for external webhooks. /architect this first, and answer any open questions with prototypes. let me review before proceeding.
```

Split a large migration into small PRs:

```
/poteto-mode create a plan to migrate our entire UI library to StyleX. break the migration into small, verifiable PRs. each PR must have its visual regression tests and live verification steps. i want the final result to be 100% identical compared to the original - bugs included
```

Fix a problem reported on Slack:

```
/poteto-mode repro this with /verify-<app>. if it repros on main, fix it and show me a video as proof
```

Most of the time `/poteto-mode` alone is enough. It calls `/how`, `/architect`, and the other skills on its own when the work needs them.

## Clean up

Delete the practice branch. To keep the verification skill, move `.claude/skills/verify-<app>/` alone to a new branch and open a PR for it.

```bash
git switch main
git branch -D pstack-tutorial
```

## How this differs from Cursor

The posts describe pstack in Cursor and Grok Bot. The Claude Code version differs in these ways:

- `/poteto-mode` cannot be pinned the way a Cursor Custom Mode can. Add it each time you start a new task.
- There are no cloud agents. `/swarm` and other parallel work run in local worktrees.
- There are no Grok Bot routines or Cursor Automations. Set up scheduled runs another way.

[`claude-code.md`](../claude-code.md) has the details. The [skill map](skill-map.en.md) shows how the skills call each other.
