# Tutorial: add a small feature with pstack

[日本語](tutorial.ja.md)

In this tutorial, we install pstack in Claude Code and add a `--stats` option to this repository's `pstack-cc/build.py`. `--stats` prints a table that shows how many times each replacement rule matched.

Along the way we use the main pstack skills in order. We ask `/pstack:how` how the code works and `/pstack:why` why it was built that way. Then we hand the change to `/pstack:poteto-mode`, and finish by having `/pstack:teach` explain its choices. The whole tutorial takes about 40 minutes.

## Before you start

You need these:

- Claude Code (`claude --version` prints 2.1 or later)
- `git` and Python 3.11 or later
- A GitHub account that can clone `souljazzfunk/lab`

Agent output changes a little on every run. So each "you should see" in this tutorial lists what the output contains, not its exact words.

## 1. Set up a practice repository

First, clone the repository and create a practice branch.

```bash
git clone https://github.com/souljazzfunk/lab.git pstack-tutorial
cd pstack-tutorial
git switch -c tutorial/build-stats
python3 pstack-cc/build.py --check
```

The last command prints one line:

```
pstack-cc/plugin/ は最新です。
```

The line means "pstack-cc/plugin/ is up to date". The generated plugin matches its sources. We run the same command later to check that our change did not break it.

## 2. Install pstack

Start Claude Code in the same directory.

```bash
claude
```

Inside Claude Code, run these two commands in order:

```
/plugin marketplace add souljazzfunk/lab
/plugin install pstack@lab
```

When the install finishes, restart Claude Code. Type `/pstack:` and the completion list shows `/pstack:poteto-mode`, `/pstack:how`, `/pstack:why`, and more.

## 3. Choose the models

Next, we choose which models pstack gives its subagents.

```
/pstack:setup-pstack
```

Claude Code lists each role with its model and asks whether to keep them. Pick the option that keeps them as they are.

The skill writes `~/.claude/pstack-models.md`. Open it from another terminal and you see lines like `how explorer: sonnet`.

```bash
cat ~/.claude/pstack-models.md
```

If your plan does not include `fable`, the skills skip that model and run the role on the parent model. You don't need to change anything here.

## 4. Ask `/pstack:how` how the code works

Before we ask for a change, we have the agent explain the code we are about to change.

```
/pstack:how how does pstack-cc/build.py turn vendor/pstack into pstack-cc/plugin?
```

The agent first judges how complex the question is. If it needs more than one angle, it starts two to four explorer subagents in parallel.

After a few minutes, you get an explanation with these headings (it drops any that do not apply):

- Overview
- Key Concepts
- How It Works
- Where Things Live
- Gotchas

Check that the explanation mentions `RULES`, `min_hits`, and `apply_rules`. These three are what `--stats` builds on.

## 5. Ask `/pstack:why` for the reason

Code shows what happens, but rarely why. That is the job of `/pstack:why`.

```
/pstack:why why does build.py give each replacement rule a min_hits value?
```

The agent searches the git history, the README, and the code in parallel. Its answer cites the commits and files it used.

Check that the answer says, in some form, that the build fails when upstream text changes and a rule stops matching. `--stats` makes those match counts visible to people too.

## 6. Have `/pstack:poteto-mode` build it

Now we ask for the change.

```
/pstack:poteto-mode add a --stats option to pstack-cc/build.py. it prints a table with each replacement rule, how many times it matched, and its min_hits. it must not rewrite pstack-cc/plugin/. show me the real output of python3 pstack-cc/build.py --stats and a passing --check as proof
```

The agent picks a playbook from the kind of work. This time it is **Feature**. It opens a todo list, and the first items are the Feature playbook steps:

- `how` over the affected subsystem.
- `architect` for parallel design exploration.
- The throughput checkpoint, the delegated implementation, verification, commits, and the PR.

A step the agent skips stays in the list as `skip: <reason>`. This change is small, so expect a few steps skipped with a reason.

When the work is done, the reply contains these:

- What it built, which data shape it chose, and why.
- The principles behind its decisions, by name (for example, Laziness Protocol and Prove It Works).
- The real output of `python3 pstack-cc/build.py --stats`.
- The output of a passing `python3 pstack-cc/build.py --check`.

Finally, run the same commands yourself. In Claude Code, a line that starts with `!` runs as a shell command.

```
!python3 pstack-cc/build.py --stats
!python3 pstack-cc/build.py --check
```

The first prints a table with one row per rule. The second prints the same "up to date" line as in step 1. Also run `git status` and check that nothing under `pstack-cc/plugin/` changed.

If the agent starts to open a PR, stop it. This is a practice branch, so there is nothing to push.

## 7. Have `/pstack:teach` explain it

Last, we ask the agent to explain the choices it made.

```
/pstack:teach me why you implemented --stats this way. what other shapes did you consider, and what did you compare to decide?
```

`/pstack:teach` runs `how` and `why` and merges what they find into one explanation. The explanation compares the shape the agent chose with the ones it rejected. If a point does not convince you, keep asking.

## 8. Clean up

Delete the practice directory.

```bash
cd ..
rm -rf pstack-tutorial
```

`~/.claude/pstack-models.md` and the installed plugin stay. You can use them in your own repositories.

## What we did

We installed pstack and chose its models. We used `how` and `why` to understand the code before changing it. Then `poteto-mode` built the feature and proved it worked with real command output. Last, `teach` turned the agent's decisions into an explanation we can check.

## Next steps

- Run `/pstack:create-verification-skill` in your own repository. It gives agents a way to drive your app and prove their changes work. pstack's author calls this the most important skill to have.
- When you correct an agent, find the place that stops the same mistake next time. In a talk on this topic, the author suggests checking these in order. Make the mistake impossible through the code's structure, catch it with lint or CI, and write it into rules or skills. A reviewer who only leaves comments cannot keep up with the number of PRs.
- The [skill map](skill-map.en.md) shows how the skills call each other.
- [`claude-code.md`](../claude-code.md) lists the differences between Cursor and Claude Code.
- The author, Lauren Tan (poteto), explains pstack in [The Complete Guide to pstack Pt. 1](https://x.com/poteto/status/2094457600259842065) and [Pt. 2](https://x.com/poteto/status/2097732320606507506).
