#!/usr/bin/env python3
"""vendor/pstack(Cursor 版、無改造)から Claude Code 用プラグイン pstack-cc/plugin/ を生成する。

使い方:
  python3 pstack-cc/build.py          生成して plugin/ を置き換える
  python3 pstack-cc/build.py --check  生成結果が plugin/ と一致するか確かめる(CI 用)
"""

import filecmp
import hashlib
import json
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
VENDOR = ROOT / "vendor" / "pstack"
OUT = HERE / "plugin"
OVERRIDES = HERE / "overrides"
ADAPTER = HERE / "claude-code.md"

# 上流から持ってくるもの。automations/ と docs/ は Cursor 専用か記事なので入れない。
COPY = ["skills", "agents", "LICENSE"]
TEXT_SUFFIXES = {".md", ".sh", ".ts", ".mjs", ".js", ".json"}

# Cursor 専用で Claude Code では意味を持たない frontmatter のキー
DROP_SKILL_KEYS = {"mode", "icon", "color", "reminder"}
DROP_AGENT_KEYS = {"is_background"}

# 上流は人が送ったときだけ動く (disable-model-invocation: true) が、ここでは Claude からも呼べるようにするスキル。
# create-verification-skill: Project のスレッドが仕事の最初に自分の検証スキルを作るため (Laiken 2026-10-12)。
# correct と recall は Laiken が送ったときだけ動かすので入れない。
MODEL_INVOCABLE = {"create-verification-skill"}


@dataclass
class Rule:
    pattern: str
    repl: str
    only_file: str | None = None
    regex: bool = False


TRANSCRIPTS_NOTE = "`claude-code.md` explains where Claude Code keeps it"

RULES = [
    Rule(
        "Transcripts live at `~/.cursor/projects/<slug>/agent-transcripts/<uuid>/<uuid>.jsonl`, "
        'where `<slug>` is the workspace path with the leading slash dropped and each "/" turned into "-" '
        "(so `/Users/you/proj` becomes `Users-you-proj`). Every line is one chat message.",
        "Transcripts live at `~/.claude/projects/<slug>/<session-id>.jsonl`, "
        'where `<slug>` is the workspace path with each "/" (and any other non-alphanumeric character) turned into "-" '
        "(so `/Users/you/proj` becomes `-Users-you-proj`). Every line is one JSON event; chat messages have "
        '`"type":"user"` or `"type":"assistant"`.',
        only_file="skills/recall/SKILL.md",
    ),
    # 上流は会話ログの場所を Cursor の system prompt 任せにしている。Claude Code の置き場所を示す
    Rule(
        "Read the whole transcript.",
        "Read this conversation's whole transcript, in the active project's transcript directory "
        "`~/.claude/projects/<slug>/` (`claude-code.md` at the plugin root explains the slug).",
        only_file="skills/reflect/SKILL.md",
    ),
    # 上流の公式 Claude Code 版の入れ方を案内しているので、この変換版の入れ方と対応表に差し替える
    Rule(
        "pstack is built for Cursor, and it also installs in Claude Code with `/plugin marketplace add cursor/plugins`, "
        "then `/plugin install pstack@cursor-plugins`. There, each command takes a `pstack:` prefix, such as "
        "`/pstack:poteto-mode`. The [Claude Code adapter](../../docs/harness/claude-code.md) maps the Cursor names, "
        "and a step that needs a Cursor-only feature, such as Bugbot or Automations, is skipped with a one-line note.",
        "pstack is built for Cursor. This copy is the Claude Code conversion installed with `/plugin install pstack@lab`. "
        "There, each command takes a `pstack:` prefix, such as `/pstack:poteto-mode`. "
        "`claude-code.md` at the plugin root maps the Cursor names.",
        only_file="skills/poteto-help/SKILL.md",
    ),
    Rule(
        "# Transcripts dir: ~/.cursor/projects/<slugified-repo-path>/agent-transcripts.\n"
        "slug=$(printf '%s' \"$main_wt\" | sed 's#^/##; s#/#-#g')\n"
        'transcripts="$HOME/.cursor/projects/$slug/agent-transcripts"',
        "# Transcripts dir: ~/.claude/projects/<slugified-repo-path> (Claude Code).\n"
        "slug=$(printf '%s' \"$main_wt\" | sed 's#[^A-Za-z0-9]#-#g')\n"
        'transcripts="$HOME/.claude/projects/$slug"',
        only_file="skills/poteto-mode/scripts/worktree-audit.sh",
    ),
    Rule(
        'Spawn all N workers in one message with `subagent_type: generalPurpose`, `environment: "cloud"`, '
        "`run_in_background: true`, and the step 3 model, left unset for `auto` or `inherit-parent`. "
        'Use `environment: "local"` only when the worker needs access to something on the user\'s computer.',
        "Spawn all N workers in one message with `subagent_type: general-purpose`, `isolation: \"worktree\"`, "
        "`run_in_background: true`, and the step 3 model, left unset for `auto` or `inherit-parent`. "
        "Omit `isolation` only when the worker must see the parent's working tree. Workers run on this machine "
        "(Claude Code has no Cursor cloud), so start at most about 5 at once and queue the rest.",
        only_file="skills/swarm/SKILL.md",
    ),
    Rule(
        "When a worker must start from a non-default pushed branch, pass `cloud_base_branch`.",
        "When a worker must start from a non-default pushed branch, name it in the brief and have the worker "
        "check it out in its worktree first.",
        only_file="skills/swarm/SKILL.md",
    ),
    # 上流は tick のたびに playbook を trunk から読み直す。プラグインに trunk は無いので、入れたファイルを cat する。
    # autopilot-full / autopilot-stack で文言が分かれた (旧: 両方とも `git show origin/main:pstack/skills/...`)。
    Rule(
        "re-reads this playbook from trunk",
        "re-reads this playbook with `cat <pstack plugin root>/skills/poteto-mode/playbooks/autopilot-full.md`",
        only_file="skills/poteto-mode/playbooks/autopilot-full.md",
    ),
    Rule("~/.cursor/rules/pstack-models.mdc", "~/.claude/pstack-models.md"),
    Rule("`agent-transcripts/` directory", "transcript directory"),
    Rule(r"the system prompt names (?:the|this) path", TRANSCRIPTS_NOTE, regex=True),
    Rule("~/.cursor/projects/*/", "~/.claude/projects/*/"),
    Rule("~/.cursor/skills/", "~/.claude/skills/"),
    Rule("~/.cursor/plugins/", "~/.claude/plugins/"),
    Rule(".cursor/skills/", ".claude/skills/"),
    Rule(".cursor/worktrees", ".claude/worktrees"),
    Rule("Task tool", "Agent tool"),
    Rule(r"\bTask subagent", "Agent-tool subagent", regex=True),
    Rule("`Task`", "`Agent`"),
    Rule("generalPurpose", "general-purpose"),
    Rule(r"\bAskQuestion\b", "AskUserQuestion", regex=True),
    Rule("Comment Sicko", "comment-sicko"),
    Rule(
        r"\]\(\.\./\.\./(docs/guide/[^)]+|README\.md)\)",
        r"](https://github.com/cursor/plugins/blob/main/pstack/\1)",
        only_file="skills/poteto-help/SKILL.md",
        regex=True,
    ),
    # 上流は既定のモデルをよく替えるので、版や努力度によらず系統名に落とす。
    # gemini の枠は sonnet にして、パネルを 3 つの別モデルに保つ
    Rule(r"claude-(fable|opus|sonnet|haiku)-\d+(?:-\d+)?(?:-(?:max|xhigh|high|medium|low|fast))*", r"\1", regex=True),
    Rule(r"gemini-\d+(?:\.\d+)?(?:-[a-z]+)*-(?:max|xhigh|high|medium|low)\b", "sonnet", regex=True),
]

CURSOR_ONLY_PATTERNS = [
    r"\.cursor/", r"pstack-models\.mdc", r"generalPurpose", r"agent-transcripts", r"cursor-plugins",
    r"environment: \"cloud\"", r"cloud_base_branch", r"\bTask (?:tool|subagent)\b", r"`Task`", r"\bAskQuestion\b",
    r"Comment Sicko", r"claude-(?:fable|opus|sonnet|haiku)-\d", r"gemini-\d", r"(?:grok|gpt)-\d[\w.]*-(?:max|xhigh|high|medium|low)",
    r"origin/main:pstack/", r"`pstack/skills/", r"re-reads? (?:this|both) playbooks? from trunk",
    r"\]\(\.\./\.\./(?:docs/guide/|README\.md)",
]

SKILL_NOTICE = (
    "> **Claude Code:** converted from the Cursor version of pstack. Before running this skill, read "
    "`claude-code.md` at the plugin root (two directories above this skill's base directory). It maps "
    "Cursor tools, models and paths to Claude Code.\n\n"
)
AGENT_NOTICE = (
    "> **Claude Code:** converted from the Cursor version of pstack. `claude-code.md` at the plugin root "
    "maps Cursor tools, models and paths to Claude Code.\n\n"
)

HAND_WRITTEN_MODEL_SLUG = re.compile(r"\b(?:claude-(?:fable|opus|sonnet|haiku)|gemini|grok|gpt)-\d[\w.-]*")

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def split_frontmatter(text: str, path: Path) -> tuple[list[str], str]:
    m = FRONTMATTER.match(text)
    if not m:
        sys.exit(f"frontmatter がありません: {path}")
    return m.group(1).split("\n"), text[m.end():]


def set_key(lines: list[str], key: str, value: str) -> list[str]:
    out = [f"{key}: {value}" if ln.startswith(f"{key}:") else ln for ln in lines]
    if not any(ln.startswith(f"{key}:") for ln in lines):
        out.insert(0, f"{key}: {value}")
    return out


def drop_keys(lines: list[str], keys: set[str]) -> list[str]:
    return [ln for ln in lines if ln.split(":", 1)[0] not in keys]


def join_frontmatter(lines: list[str], notice: str, body: str) -> str:
    return "---\n" + "\n".join(lines) + "\n---\n\n" + notice + body.lstrip("\n")


def normalize_skill(path: Path) -> None:
    lines, body = split_frontmatter(path.read_text(), path)
    # Claude Code のスキル名は小文字とハイフンだけ。ディレクトリ名に揃える("Poteto Mode" → poteto-mode)
    lines = set_key(drop_keys(lines, DROP_SKILL_KEYS), "name", path.parent.name)
    if path.parent.name in MODEL_INVOCABLE:
        if "disable-model-invocation: true" not in lines:
            sys.exit(f"上流で disable-model-invocation が変わりました。MODEL_INVOCABLE を見直す: {path.parent.name}")
        lines = drop_keys(lines, {"disable-model-invocation"})
    path.write_text(join_frontmatter(lines, SKILL_NOTICE, body))


def normalize_agent(path: Path) -> None:
    lines, body = split_frontmatter(path.read_text(), path)
    lines = set_key(drop_keys(lines, DROP_AGENT_KEYS), "name", path.stem)
    path.write_text(join_frontmatter(lines, AGENT_NOTICE, body))


def apply_rules(out: Path) -> None:
    files = [p for p in sorted(out.rglob("*")) if p.is_file() and p.suffix in TEXT_SUFFIXES]
    hits = [0] * len(RULES)
    for path in files:
        rel = path.relative_to(out).as_posix()
        text = orig = path.read_text()
        for i, r in enumerate(RULES):
            if r.only_file and r.only_file != rel:
                continue
            if r.regex:
                text, n = re.subn(r.pattern, r.repl, text)
            else:
                n = text.count(r.pattern)
                text = text.replace(r.pattern, r.repl)
            hits[i] += n
        if text != orig:
            path.write_text(text)

    unused = [r for r, n in zip(RULES, hits) if n == 0]
    if unused:
        print("警告: 上流のどこにも当たらなくなったルールがあります。消してよいか確かめてください:", file=sys.stderr)
        for r in unused:
            where = f" ({r.only_file})" if r.only_file else ""
            print(f"  {r.pattern[:90]!r}{where}", file=sys.stderr)

    leftovers = [
        f"  {p.relative_to(out)}:{text.count(chr(10), 0, m.start()) + 1}: {m.group(0)!r}"
        for p in files
        for text in [p.read_text()]
        for w in CURSOR_ONLY_PATTERNS
        for m in re.finditer(w, text)
    ]
    if leftovers:
        print("Cursor 固有の記述が変換されずに残りました。RULES に置き換えを足すか、既存のルールを上流の新しい文に合わせてください:", file=sys.stderr)
        print("\n".join(leftovers), file=sys.stderr)
        sys.exit(1)


def upstream_info() -> dict[str, str]:
    info = {}
    for line in (HERE / "UPSTREAM").read_text().splitlines():
        k, _, v = line.partition(": ")
        info[k] = v
    return info


def content_hash(out: Path) -> str:
    """生成した中身の短いハッシュ。上流が同じでもこちらの変換を変えたら版が変わり、配布先が更新に気づく。"""
    h = hashlib.sha256()
    for p in sorted(out.rglob("*")):
        if p.is_file():
            h.update(p.relative_to(out).as_posix().encode() + b"\0" + p.read_bytes() + b"\0")
    return h.hexdigest()[:7]


def write_manifest(out: Path) -> None:
    up = json.loads((VENDOR / ".cursor-plugin" / "plugin.json").read_text())
    info = upstream_info()
    manifest = {
        "name": up["name"],
        "version": f"{up['version']}-cc.{info['commit'][:7]}.{content_hash(out)}",
        "description": up["description"] + " (Claude Code conversion of the Cursor plugin.)",
        "author": up["author"],
        "homepage": up["homepage"],
        "repository": up["repository"],
        "license": up["license"],
        "keywords": up["keywords"],
    }
    (out / ".claude-plugin").mkdir()
    (out / ".claude-plugin" / "plugin.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")


def write_readme(out: Path) -> None:
    info = upstream_info()
    (out / "README.md").write_text(
        "# pstack (Claude Code)\n\n"
        "**Generated. Do not edit.** Built by `pstack-cc/build.py` from `vendor/pstack`.\n\n"
        f"- Upstream: {info['repo']} (`{info['path']}/` at `{info['commit']}`, {info['date']})\n"
        "- What changed for Claude Code: see `claude-code.md`\n"
        "- License: MIT, see `LICENSE` (upstream author: Lauren Tan)\n"
    )


def check_hand_written(paths: list[Path]) -> None:
    found = [
        f"  {p.name}:{text.count(chr(10), 0, m.start()) + 1}: {m.group(0)}"
        for p in paths
        for text in [p.read_text()]
        for m in HAND_WRITTEN_MODEL_SLUG.finditer(text)
    ]
    if found:
        print("手書きの文書に上流のモデル名がそのまま書いてあります。上流が名前を替えると古くなるので、"
              "`claude-opus-<version>-<effort>` のように版と努力度を伏せた形で書いてください:", file=sys.stderr)
        print("\n".join(found), file=sys.stderr)
        sys.exit(1)


def build(out: Path) -> None:
    check_hand_written([ADAPTER, HERE / "README.md", *sorted((HERE / "docs").glob("*.md"))])
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for name in COPY:
        src = VENDOR / name
        if src.is_dir():
            shutil.copytree(src, out / name)
        else:
            shutil.copy2(src, out / name)
    for src in sorted(OVERRIDES.rglob("*")):
        if src.is_file():
            dest = out / src.relative_to(OVERRIDES)
            if not dest.exists():
                sys.exit(f"override の差し替え先が上流にありません: {dest.relative_to(out)}")
            shutil.copy2(src, dest)

    apply_rules(out)
    for skill in sorted((out / "skills").glob("*/SKILL.md")):
        normalize_skill(skill)
    for agent in sorted((out / "agents").glob("*.md")):
        normalize_agent(agent)

    shutil.copy2(ADAPTER, out / "claude-code.md")
    write_manifest(out)
    write_readme(out)


def same_tree(a: Path, b: Path) -> bool:
    cmp = filecmp.dircmp(a, b)
    if cmp.left_only or cmp.right_only or cmp.funny_files:
        return False
    _, mismatch, errors = filecmp.cmpfiles(a, b, cmp.common_files, shallow=False)
    if mismatch or errors:
        return False
    return all(same_tree(a / d, b / d) for d in cmp.common_dirs)


def main() -> None:
    if "--check" in sys.argv[1:]:
        with tempfile.TemporaryDirectory() as tmp:
            fresh = Path(tmp) / "plugin"
            build(fresh)
            if not OUT.exists() or not same_tree(fresh, OUT):
                sys.exit("pstack-cc/plugin/ が古いです。python3 pstack-cc/build.py を実行してコミットしてください。")
        print("pstack-cc/plugin/ は最新です。")
        return
    build(OUT)
    print(f"生成しました: {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
