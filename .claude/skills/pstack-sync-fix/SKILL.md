---
name: pstack-sync-fix
description: pstack 上流の自動同期(.github/workflows/pstack-upstream-sync.yml)が止まっていないかを確かめ、止まっていたら直して main まで入れる。毎日の定期タスクから呼ばれる。手でも /pstack-sync-fix で使える。
---

# pstack 上流の同期を直す

毎日 8:47 JST に `pstack 上流の同期` が走る。普段は自動で PR を出して merge まで済むが、次の 2 つでは止まる。このスキルはそれを見つけて直し、main に入れるところまでやる。人の承認は待たない。

- **build 失敗**: 上流の文章が変わって `pstack-cc/build.py` の `RULES` が当たらない。issue「pstack 上流の同期: build が失敗しました」が開いている。
- **手作業待ちの PR**: ブランチ `automation/pstack-upstream-sync` の PR が開いたまま(スキルの削除か、`pstack-cc/overrides/` の上流版の変更があった)。

GitHub は MCP の `mcp__github__*` ツールで触る(`gh` は使えない)。リポジトリは `souljazzfunk/lab`。

## 1. 止まっているか確かめる

1. 開いている issue を title「pstack 上流の同期: build が失敗しました」で探す。
2. `automation/pstack-upstream-sync` を head にした開いた PR を探す。
3. `pstack-upstream-sync.yml` の最新の実行を見る。失敗していればログを読む(`get_job_logs` の `failed_only`)。
4. 手元で `pstack-cc/sync-upstream.sh` → `python3 pstack-cc/build.py` を実行する。

どれにも当たらず、build も通って `git status` に `pstack-cc/UPSTREAM` の変更がない(main が上流に追いついている)なら、何もせずに終わる。build が通って上流に更新があるだけなら、次の定期実行が拾うので何もしない。

## 2. 直す

作業ブランチはセッションで指定されたものを使う。指定がなければ `claude/pstack-sync-fix-<YYYYMMDD>`(JST)を main から切る。

- **build 失敗**: 表示されたルールの上流側の文章を `git diff vendor/pstack/<ファイル>` で確かめ、`build.py` の `RULES` を新しい文章に合わせる。置き換え後の文章も、上流の変更(手順番号、言い回し)に合わせて直す。Claude Code での意味(`claude-code.md` の対応表)は変えない。ルールそのものが要らなくなった(上流から該当箇所が消えた)ときは消してよい。
- **overrides の上流版が変わった**: `git diff` で上流の変更点を見て、`pstack-cc/overrides/` の同じファイルに反映する。
- **スキルが増えた・消えた**: `pstack-cc/docs/skill-map.{ja,en}.md` のスキル数(`ls pstack-cc/plugin/skills | wc -l`)と、名前の出てくる箇所を直す。消えたスキルを `build.py` の `MODEL_INVOCABLE` などが参照していたら外す。

手作業待ちの PR があるときは、その PR のブランチではなく作業ブランチの上で最新の上流を取り込み直して直す(PR は後で閉じる)。

## 3. 検査する

CI(`.github/workflows/pstack-cc.yml`)と同じものを手元で通す。

```bash
python3 pstack-cc/build.py --check
python3 -m venv "$TMPDIR/ruff" && "$TMPDIR/ruff/bin/pip" install -q ruff==0.15.8 && "$TMPDIR/ruff/bin/ruff" check pstack-cc/
claude plugin validate --strict pstack-cc/plugin
claude plugin validate --strict .
```

`shellcheck` は `sync-upstream.sh` を変えたときだけ(無ければ入れる)。

## 4. main に入れる

1. `git add -A vendor/pstack pstack-cc` してコミットする。題は `pstack-cc: pstack <版> に追従し、当たらなくなった置き換えルールを直す` の形(版は `pstack-cc/plugin/.claude-plugin/plugin.json` の `version`)。本文に上流のコミット範囲と直したルールを書く。
2. push して main 向けの PR を出す。本文に何が当たらなくなり、どう直したかを書く。
3. PR の `pstack-cc` の検査が通るのを待つ(`subscribe_pr_activity` で待つ。`sleep` で回さない)。落ちたら直して push し直す。
4. 通ったら squash で merge する。
5. build 失敗の issue を `state_reason: completed` で閉じ、直した PR へのリンクをコメントする。手作業待ちの自動 PR があれば「<PR> で取り込み済み」とコメントして閉じる。

直せない(上流の変更が大きく、置き換えの方針から考え直す必要がある)ときは、merge せずに PR を draft のまま残し、issue に何が判断待ちかを書いて終わる。
