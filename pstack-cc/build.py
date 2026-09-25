#!/usr/bin/env python3
"""vendor/pstack(Cursor 版、無改造)から Claude Code 用プラグイン pstack-cc/plugin/ を生成する。

使い方:
  python3 pstack-cc/build.py          生成して plugin/ を置き換える
  python3 pstack-cc/build.py --check  生成結果が plugin/ と一致するか確かめる(CI 用)

置き換えルールは RULES にまとめてある。ルールごとに「最低何回当たるはずか」を持たせ、
上流の文章が変わって当たらなくなったら build を失敗させる。気づかないまま変換が抜けるのを防ぐため。
"""

import filecmp
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


@dataclass
class Rule:
    pattern: str
    repl: str
    min_hits: int = 1
    only: str | None = None  # plugin/ からの相対パス。指定があればそのファイルだけ
    regex: bool = False


TRANSCRIPTS_NOTE = "`claude-code.md` explains where Claude Code keeps it"

RULES = [
    # --- 個別ファイルの書き換え(上流の文章が変わったら当たらなくなり、build が止まる) ---
    Rule(
        "Transcripts live at `~/.cursor/projects/<slug>/agent-transcripts/<uuid>/<uuid>.jsonl`, "
        'where `<slug>` is the workspace path with the leading slash dropped and each "/" turned into "-" '
        "(so `/Users/you/proj` becomes `Users-you-proj`). Every line is one chat message.",
        "Transcripts live at `~/.claude/projects/<slug>/<session-id>.jsonl`, "
        'where `<slug>` is the workspace path with each "/" (and any other non-alphanumeric character) turned into "-" '
        "(so `/Users/you/proj` becomes `-Users-you-proj`). Every line is one JSON event; chat messages have "
        '`"type":"user"` or `"type":"assistant"`.',
        only="skills/recall/SKILL.md",
    ),
    Rule(
        "The system prompt names the active workspace's `agent-transcripts/` directory. Use that path.",
        "Use the active project's transcript directory, `~/.claude/projects/<slug>/` "
        "(`claude-code.md` at the plugin root explains the slug).",
        only="skills/reflect/SKILL.md",
    ),
    Rule(
        "# Transcripts dir: ~/.cursor/projects/<slugified-repo-path>/agent-transcripts.\n"
        "slug=$(printf '%s' \"$main_wt\" | sed 's#^/##; s#/#-#g')\n"
        'transcripts="$HOME/.cursor/projects/$slug/agent-transcripts"',
        "# Transcripts dir: ~/.claude/projects/<slugified-repo-path> (Claude Code).\n"
        "slug=$(printf '%s' \"$main_wt\" | sed 's#[^A-Za-z0-9]#-#g')\n"
        'transcripts="$HOME/.claude/projects/$slug"',
        only="skills/poteto-mode/scripts/worktree-audit.sh",
    ),
    Rule(
        'Spawn all N workers in one message with `subagent_type: generalPurpose`, `environment: "cloud"`, '
        "`run_in_background: true`, and the step 4 model, left unset for `auto` or `inherit-parent`. "
        'Use `environment: "local"` only when the worker needs access to something on the user\'s computer.',
        "Spawn all N workers in one message with `subagent_type: general-purpose`, `isolation: \"worktree\"`, "
        "`run_in_background: true`, and the step 4 model, left unset for `auto` or `inherit-parent`. "
        "Omit `isolation` only when the worker must see the parent's working tree. Workers run on this machine "
        "(Claude Code has no Cursor cloud), so start at most about 5 at once and queue the rest.",
        only="skills/swarm/SKILL.md",
    ),
    Rule(
        "When a worker must start from a non-default pushed branch, pass `cloud_base_branch`.",
        "When a worker must start from a non-default pushed branch, name it in the brief and have the worker "
        "check it out in its worktree first.",
        only="skills/swarm/SKILL.md",
    ),
    # --- 全体の置き換え ---
    # モデル設定ファイル
    Rule("~/.cursor/rules/pstack-models.mdc", "~/.claude/pstack-models.md", min_hits=4),
    Rule("the `pstack-models.mdc` rule", "`~/.claude/pstack-models.md`", min_hits=3),
    # 会話ログの場所
    Rule("`agent-transcripts/` directory", "transcript directory", min_hits=4),
    Rule(r"the system prompt names (?:the|this) path", TRANSCRIPTS_NOTE, min_hits=3, regex=True),
    Rule("~/.cursor/projects/*/", "~/.claude/projects/*/", min_hits=4),
    # スキル・プラグイン・worktree の置き場所
    Rule("~/.cursor/skills/", "~/.claude/skills/", min_hits=2),
    Rule("~/.cursor/plugins/", "~/.claude/plugins/", min_hits=1),
    Rule(".cursor/skills/", ".claude/skills/", min_hits=5),
    Rule(".cursor/worktrees", ".claude/worktrees", min_hits=1),
    # ツール名
    Rule("Task tool", "Agent tool", min_hits=5),
    Rule(r"\bTask subagent", "Agent-tool subagent", min_hits=2, regex=True),
    Rule("`Task`", "`Agent`", min_hits=5),
    Rule("generalPurpose", "general-purpose", min_hits=5),
    Rule(r"\bAskQuestion\b", "AskUserQuestion", min_hits=3, regex=True),
    Rule("(Shell, Grep, MCP", "(Bash, Grep, MCP", min_hits=3),
    Rule("Comment Sicko", "comment-sicko", min_hits=2),
    # モデル名(対応表は claude-code.md)
    Rule(r"claude-opus-5-5-(?:max|medium)", "opus", min_hits=10, regex=True),
    Rule("gpt-5.6-sol-max", "fable", min_hits=5),
    Rule("grok-4.7-xhigh-fast", "sonnet", min_hits=10),
]

# 変換後に残っていたら build を失敗させる文字列
FORBIDDEN = ["~/.cursor/", "pstack-models.mdc", "generalPurpose", "grok-4.7", "claude-opus-5-5"]

SKILL_NOTICE = (
    "> **Claude Code:** converted from the Cursor version of pstack. Before running this skill, read "
    "`claude-code.md` at the plugin root (two directories above this skill's base directory). It maps "
    "Cursor tools, models and paths to Claude Code.\n\n"
)
AGENT_NOTICE = (
    "> **Claude Code:** converted from the Cursor version of pstack. `claude-code.md` at the plugin root "
    "maps Cursor tools, models and paths to Claude Code.\n\n"
)

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
            if r.only and r.only != rel:
                continue
            if r.regex:
                text, n = re.subn(r.pattern, r.repl, text)
            else:
                n = text.count(r.pattern)
                text = text.replace(r.pattern, r.repl)
            hits[i] += n
        if text != orig:
            path.write_text(text)

    stale = [(r, n) for r, n in zip(RULES, hits) if n < r.min_hits]
    if stale:
        print("上流の文章が変わったため、当たらなくなったルールがあります:", file=sys.stderr)
        for r, n in stale:
            where = f" ({r.only})" if r.only else ""
            print(f"  {n}/{r.min_hits} 回: {r.pattern[:90]!r}{where}", file=sys.stderr)
        sys.exit(1)

    leftovers = [
        f"  {p.relative_to(out)}: {w}"
        for p in files
        for w in FORBIDDEN
        if w in p.read_text()
    ]
    if leftovers:
        print("変換しきれなかった Cursor 固有の記述があります:", file=sys.stderr)
        print("\n".join(leftovers), file=sys.stderr)
        sys.exit(1)


def upstream_info() -> dict[str, str]:
    info = {}
    for line in (HERE / "UPSTREAM").read_text().splitlines():
        k, _, v = line.partition(": ")
        info[k] = v
    return info


def write_manifest(out: Path) -> None:
    up = json.loads((VENDOR / ".cursor-plugin" / "plugin.json").read_text())
    info = upstream_info()
    manifest = {
        "name": up["name"],
        "version": f"{up['version']}-cc.{info['commit'][:7]}",
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


def build(out: Path) -> None:
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
