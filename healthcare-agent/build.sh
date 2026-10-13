#!/usr/bin/env bash
# healthcare-agent/ のソースから配布用プラグインを healthcare-agent/plugin/ に組み立てる。
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
dest="$here/plugin"
skill="$dest/skills/doctor-finder"

rm -rf "$dest"
mkdir -p "$dest/.claude-plugin" "$skill/scripts"
cat > "$dest/.claude-plugin/plugin.json" <<'JSON'
{
  "name": "doctor-finder",
  "description": "ヘルスケア受付エージェント: 自然言語の問い合わせから、院内の医師データ(JSON)で最適な医師と空き枠を案内する。API キー不要、検索はローカル。",
  "version": "0.1.0",
  "author": {"name": "souljazzfunk"},
  "keywords": ["healthcare", "agent", "search"]
}
JSON
cp "$here/skill-src/SKILL.md" "$skill/SKILL.md"
cp "$here/core.py" "$here/agent.py" "$here/sample_doctors.json" "$skill/scripts/"
