#!/usr/bin/env bash
# nanaism/yomiyasu を vendor/yomiyasu/ に無改造で写し、取り込んだコミットを UPSTREAM に記録する。
# 使い方: yomiyasu/sync-upstream.sh [ref]   (ref の既定は main)
set -euo pipefail

repo_url="https://github.com/nanaism/yomiyasu.git"
ref="${1:-main}"

root="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
dest="$root/vendor/yomiyasu"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

git clone --quiet "$repo_url" "$tmp/src"
git -C "$tmp/src" checkout --quiet "$ref"

rm -rf "$dest"
mkdir -p "$dest"
cp -R "$tmp/src/." "$dest/"
rm -rf "$dest/.git"

{
	echo "repo: $repo_url"
	echo "commit: $(git -C "$tmp/src" rev-parse HEAD)"
	echo "date: $(git -C "$tmp/src" log -1 --format=%cI)"
} > "$root/yomiyasu/UPSTREAM"

echo "vendor/yomiyasu を更新しました:"
cat "$root/yomiyasu/UPSTREAM"
echo
echo "次に: git diff --stat vendor/yomiyasu で変更を確認 → claude plugin validate --strict vendor/yomiyasu"
