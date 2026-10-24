---
name: upstream-sync-fix
description: 上流の自動同期(pstack・yomiyasu・simple-english)が止まっていないかを確かめ、止まっていたら直して main まで入れる。毎日の定期タスクから呼ばれる。手でも /upstream-sync-fix で使える。
---

# 上流の同期を直す

毎朝、3 つの上流同期が走る。普段は自動で PR を出して merge まで済むが、止まることがある。このスキルは 3 つ全部を見て、止まっているものを直し、main に入れるところまでやる。人の承認は待たない。

| 対象 | ワークフロー(JST) | 失敗の issue の title | 自動 PR のブランチ | 検査 |
|---|---|---|---|---|
| pstack | `pstack-upstream-sync.yml`(8:47) | `pstack 上流の同期: build が失敗しました` | `automation/pstack-upstream-sync` | `pstack-cc.yml` |
| yomiyasu | `yomiyasu-upstream-sync.yml`(8:52) | `yomiyasu 上流の同期: 取り込みが失敗しました` | `automation/yomiyasu-upstream-sync` | `yomiyasu.yml` |
| simple-english | `simple-english-upstream-sync.yml`(8:57) | `simple-english 上流の同期: 取り込みが失敗しました` | `automation/simple-english-upstream-sync` | `simple-english.yml` |

止まり方は 3 つある。

- **取り込みか build の失敗**: 上の issue が開いている。
- **手作業待ちの PR**: 自動 PR が開いたまま(自動 merge しない変更があった)。
- **ワークフロー自体の失敗**: 最新の実行が issue も PR も残さずに失敗している(検査や merge の job が落ちた、Actions の書き方が古くなった、など)。

GitHub は MCP の `mcp__github__*` ツールで触る(`gh` は使えない)。リポジトリは `souljazzfunk/lab`。

## 1. 止まっているか確かめる

対象ごとに:

1. 失敗の issue が開いているか。
2. 自動 PR が開いているか。
3. ワークフローの最新の実行が失敗していないか。失敗していればログを読む(`get_job_logs` の `failed_only`)。
4. 手元で取り込みを試す(下の「対象ごとのやり方」)。

どの対象も当たらず、取り込みが通って `<対象>/UPSTREAM` が変わらない(main が上流に追いついている)なら、何もせずに終わる。取り込みが通って上流に更新があるだけなら、次の定期実行が拾うので何もしない。

一時的な失敗(ネットワーク、runner の喪失)で、手元では通るなら、`actions_run_trigger` の `run_workflow` で main のワークフローを一度だけ起動し直して終わる。

## 2. 直す

作業ブランチはセッションで指定されたものを使う。指定がなければ `claude/upstream-sync-fix-<YYYYMMDD>`(JST)を main から切る。止まっている対象が複数あれば、1 つのブランチ・1 つの PR でまとめて直してよい。

自動 PR があるときは、その PR のブランチではなく作業ブランチの上で最新の上流を取り込み直して直す(自動 PR は後で閉じる)。

### pstack

- 取り込み: `pstack-cc/sync-upstream.sh` → `python3 pstack-cc/build.py`
- **build 失敗**: 表示されたルールの上流側の文章を `git diff vendor/pstack/<ファイル>` で確かめ、`build.py` の `RULES` を新しい文章に合わせる。置き換え後の文章も、上流の変更(手順番号、言い回し)に合わせて直す。Claude Code での意味(`pstack-cc/claude-code.md` の対応表)は変えない。上流から該当箇所が消えたルールは消してよい。
- **overrides の上流版が変わった**: `git diff` で上流の変更点を見て、`pstack-cc/overrides/` の同じファイルに反映する。
- **スキルが増えた・消えた**: `pstack-cc/docs/skill-map.{ja,en}.md` のスキル数(`ls pstack-cc/plugin/skills | wc -l`)と、名前の出てくる箇所を直す。消えたスキルを `build.py` の `MODEL_INVOCABLE` などが参照していたら外す。
- 検査:
  ```bash
  python3 pstack-cc/build.py --check
  python3 -m venv "$TMPDIR/ruff" && "$TMPDIR/ruff/bin/pip" install -q ruff==0.15.8 && "$TMPDIR/ruff/bin/ruff" check pstack-cc/
  claude plugin validate --strict pstack-cc/plugin
  ```

### yomiyasu / simple-english

2 つは同じ作り。以下 `<名前>` は `yomiyasu` か `simple-english`。

- 取り込み: `<名前>/sync-upstream.sh`(最後に `<名前>/build.sh` まで走る)
- **取り込みの失敗**: 上流のファイル構成が変わり、`build.sh` が写すファイル(`.claude-plugin/plugin.json`、`LICENSE`、`skills/<名前>`)が見つからなくなったことが多い。上流の新しい配置を確かめて `build.sh` を直す。配布物は「マニフェスト・スキル・LICENSE だけ」の最小構成を保つ(上流ルートをそのまま配ると marketplace 同期で skipped になる。`<名前>/README.md` を参照)。
- **マニフェストの version 以外が変わった**: `vendor/<名前>/.claude-plugin/plugin.json` の変更を見て、`.claude-plugin/marketplace.json` の `<名前>` の説明と食い違っていれば直す。
- 検査:
  ```bash
  <名前>/build.sh && test -z "$(git status --porcelain <名前>/plugin)"   # コミット後に
  claude plugin validate --strict <名前>/plugin/.claude-plugin/plugin.json
  ```
  `shellcheck <名前>/sync-upstream.sh <名前>/build.sh`(無ければ入れる)。

### 共通

- marketplace: `claude plugin validate --strict .`
- ワークフロー自体の失敗なら、ログの原因を `.github/workflows/` で直す。直したワークフローは merge 後に `run_workflow` で一度起動し、通ることを確かめる。

## 3. main に入れる

1. 直した対象ごとにコミットする。題は `<対象>: 上流 <短い SHA> に追従し、<直したこと>` の形。本文に上流のコミット範囲と直した内容を書く。
2. push して main 向けの PR を出す。本文に何が止まっていて、どう直したかを書き、失敗の issue を `Closes #<番号>` で結ぶ。
3. PR の検査が通るのを待つ(`subscribe_pr_activity` で待つ。`sleep` で回さない)。落ちたら直して push し直す。
4. 通ったら squash で merge する。
5. 失敗の issue が閉じたことを確かめる(閉じていなければ `state_reason: completed` で閉じ、PR へのリンクをコメントする)。手作業待ちの自動 PR があれば「<PR> で取り込み済み」とコメントして閉じる。

直せない(上流の変更が大きく、変換の方針から考え直す必要がある)ときは、merge せずに PR を draft のまま残し、issue に何が判断待ちかを書いて終わる。
