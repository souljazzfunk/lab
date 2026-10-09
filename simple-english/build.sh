#!/usr/bin/env bash
# vendor/simple-english/ から配布用の最小プラグインを simple-english/plugin/ に組み立てる。
# 上流の中身は書き換えず、スキルと LICENSE だけを写す。
# 上流ルートには入れ子の marketplace.json や evals/ があり、yomiyasu と同じく claude.ai の
# マーケットプレイス同期で skipped になりうるので外す。
# 上流の plugin.json にある hooks(全セッションでスキルを常時有効にする SessionStart と、
# Write/Edit 後の lint)は配らない。スキルだけを入れたいので、マニフェストから hooks を消して写す。
set -euo pipefail

root="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
src="$root/vendor/simple-english"
dest="$root/simple-english/plugin"

rm -rf "$dest"
mkdir -p "$dest/.claude-plugin" "$dest/skills"
jq 'del(.hooks)' "$src/.claude-plugin/plugin.json" > "$dest/.claude-plugin/plugin.json"
cp "$src/LICENSE" "$dest/LICENSE"
cp -R "$src/skills/simple-english" "$dest/skills/simple-english"
