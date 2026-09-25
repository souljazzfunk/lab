#!/usr/bin/env bash
# cursor/plugins の pstack/ を vendor/pstack/ に無改造で写し、取り込んだコミットを UPSTREAM に記録する。
# 使い方: pstack-cc/sync-upstream.sh [ref]   (ref の既定は main)
set -euo pipefail

repo_url="https://github.com/cursor/plugins.git"
subdir="pstack"
ref="${1:-main}"

root="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
dest="$root/vendor/pstack"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

git clone --quiet --filter=blob:none --no-checkout "$repo_url" "$tmp/src"
git -C "$tmp/src" sparse-checkout set "$subdir"
git -C "$tmp/src" checkout --quiet "$ref"

rm -rf "$dest"
mkdir -p "$dest"
cp -R "$tmp/src/$subdir/." "$dest/"

{
	echo "repo: $repo_url"
	echo "path: $subdir"
	echo "commit: $(git -C "$tmp/src" rev-parse HEAD)"
	echo "date: $(git -C "$tmp/src" log -1 --format=%cI)"
} > "$root/pstack-cc/UPSTREAM"

echo "vendor/pstack を更新しました:"
cat "$root/pstack-cc/UPSTREAM"
echo
echo "次に: git diff --stat vendor/pstack で変更を確認 → python3 pstack-cc/build.py"
