#!/usr/bin/env bash
# vendor/yomiyasu/ から配布用の最小プラグインを yomiyasu/plugin/ に組み立てる。
# 上流の中身は書き換えず、プラグインに要るもの(マニフェスト・スキル・LICENSE)だけを写す。
# 上流ルートには入れ子の marketplace.json、ルート直下の SKILL.md(重複)、tests/ などがあり、
# claude.ai のマーケットプレイス同期で yomiyasu が「skipped」になったため、それらを外している。
set -euo pipefail

root="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
src="$root/vendor/yomiyasu"
dest="$root/yomiyasu/plugin"

rm -rf "$dest"
mkdir -p "$dest/.claude-plugin" "$dest/skills"
cp "$src/.claude-plugin/plugin.json" "$dest/.claude-plugin/plugin.json"
cp "$src/LICENSE" "$dest/LICENSE"
cp -R "$src/skills/yomiyasu" "$dest/skills/yomiyasu"
rm -rf "$dest/skills/yomiyasu/.claude-plugin"
