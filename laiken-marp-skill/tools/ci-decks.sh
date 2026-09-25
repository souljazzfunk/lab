#!/bin/sh
# 見本デッキを書き出して、検査4本を通す。CI と手元の両方で使う。
#   - GOOD のデッキは、全検査が NG 0 件であること
#   - BAD のデッキ（わざと崩した版）は、全検査が NG を出すこと（検査が壊れていないかの確認）
# 使い方: sh tools/ci-decks.sh    （laiken-marp-skill/ で実行）
set -u
GOOD="examples/sample examples/demo examples/catalog"
BAD="examples/broken"
THEME="$(pwd)/theme/laiken-light.css"
TOOLS="$(pwd)/tools"
fail=0

render() {
  (cd "$1" && marp --no-stdin deck.md --pdf --html --theme "$THEME" --allow-local-files -o deck.pdf >/dev/null 2>&1) \
    || { echo "NG $1: Marp の書き出し（PDF）に失敗"; fail=1; return 1; }
  # ブラウザで見る用の HTML。リポジトリには入れず、CI の成果物として残す
  (cd "$1" && marp --no-stdin deck.md --html --theme "$THEME" -o deck.html >/dev/null 2>&1) \
    || { echo "NG $1: Marp の書き出し（HTML）に失敗"; fail=1; return 1; }
  # 右上の EN / JA / Both と、左下のダーク / ライトの切り替えを足す
  python3 "$TOOLS/add-toggles.py" "$1/deck.html" >/dev/null \
    || { echo "NG $1: 切り替えを足せない"; fail=1; return 1; }
}

# 検査を1本走らせ、終了コードを返す。出力は字下げして残す
run() {
  dir=$1; shift
  (cd "$dir" && "$@") > /tmp/ci-check.log 2>&1
  code=$?
  sed 's/^/    /' /tmp/ci-check.log
  return $code
}

checks() {
  dir=$1
  run "$dir" python3 "$TOOLS/check-margins.py" deck.pdf;     echo "margins $?"
  run "$dir" python3 "$TOOLS/check-gaps.py" deck.pdf;        echo "gaps $?"
  run "$dir" python3 "$TOOLS/check-figure-text.py" deck.pdf; echo "figure-text $?"
  # images/*.svg はシェルで展開させる
  (cd "$dir" && node "$TOOLS/check-svg-box-fit.mjs" images/*.svg) > /tmp/ci-check.log 2>&1
  code=$?; sed 's/^/    /' /tmp/ci-check.log; echo "svg-box-fit $code"
  # 全角の括弧に隣接して反映されなかった **強調** のアスタリスク
  n=$(cd "$dir" && mutool draw -F stext -o - deck.pdf 2>/dev/null | grep -c 'c="\*"')
  echo "    残ったアスタリスク: $n 個"
  [ "$n" -eq 0 ]; echo "asterisk $?"
}

for d in $GOOD; do
  echo "## $d（NG 0 件であること）"
  render "$d" || continue
  checks "$d" > /tmp/ci-result.log
  grep '^    ' /tmp/ci-result.log
  grep -v '^    ' /tmp/ci-result.log | while read -r name code; do
    if [ "$code" -eq 0 ]; then echo "OK   $name"; else echo "FAIL $name"; fi
  done
  grep -v '^    ' /tmp/ci-result.log | awk '$2 != 0 {exit 1}' || fail=1
done

# 二か国語のデッキ（lang: mul）は、EN だけ・JA だけの版も書き出して測る
for d in $GOOD; do
  grep -q '^lang: mul' "$d/deck.md" || continue
  for l in en ja; do
    echo "## $d（lang: $l）"
    sed "s/^lang: mul/lang: $l/" "$d/deck.md" > "$d/deck.$l.md"
    (cd "$d" && marp --no-stdin "deck.$l.md" --pdf --html --theme "$THEME" --allow-local-files -o "deck.$l.pdf" >/dev/null 2>&1) \
      || { echo "NG $d: Marp の書き出し（lang: $l）に失敗"; fail=1; rm -f "$d/deck.$l.md"; continue; }
    rm -f "$d/deck.$l.md"
    for c in margins gaps figure-text; do
      if run "$d" python3 "$TOOLS/check-$c.py" "deck.$l.pdf"; then echo "OK   $c"; else echo "FAIL $c"; fail=1; fi
    done
  done
done

for d in $BAD; do
  echo "## $d（検査4本がすべて NG を出すこと）"
  render "$d" || continue
  checks "$d" > /tmp/ci-result.log
  grep -v '^    ' /tmp/ci-result.log | grep -v '^asterisk' | while read -r name code; do
    if [ "$code" -ne 0 ]; then echo "OK   $name が崩れを検出"; else echo "FAIL $name が崩れを見逃した"; fi
  done
  grep -v '^    ' /tmp/ci-result.log | grep -v '^asterisk' | awk '$2 == 0 {exit 1}' || fail=1
done

[ "$fail" -eq 0 ] && echo "すべて合格" || echo "不合格あり"
exit "$fail"
