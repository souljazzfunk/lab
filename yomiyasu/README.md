# yomiyasu

[yomiyasu](https://github.com/nanaism/yomiyasu)(nanaism 作、MIT)を lab の marketplace から入れられるようにしたもの。AI が書いた不自然な日本語を、読みやすく自然な文章に書き直すスキル。

上流は `vendor/yomiyasu/` に無改造で置き、marketplace からは `yomiyasu/build.sh` で組み立てた最小構成の `yomiyasu/plugin/`(マニフェスト・スキル・LICENSE だけ)を配っている。上流ルートをそのまま配ると、入れ子の marketplace.json や重複した SKILL.md のせいか、claude.ai のマーケットプレイス同期で yomiyasu が skipped になったため。著作権表示とライセンスは [`vendor/yomiyasu/LICENSE`](../vendor/yomiyasu/LICENSE) にある。

## 使う

```
/plugin marketplace add souljazzfunk/lab
/plugin install yomiyasu@lab
```

使い方の詳細は上流の [README](../vendor/yomiyasu/README.md)。

## 上流の更新を取り込む

```bash
yomiyasu/sync-upstream.sh           # 既定は main。最後に build.sh も走る
git diff --stat vendor/yomiyasu yomiyasu/plugin
claude plugin validate --strict yomiyasu/plugin/.claude-plugin/plugin.json
git add vendor/yomiyasu yomiyasu && git commit
```

`UPSTREAM` に取り込んだコミットが記録される。`vendor/yomiyasu/` と `yomiyasu/plugin/` は手で編集しない。

### 毎日の自動チェック

`.github/workflows/yomiyasu-upstream-sync.yml` が毎日 8:52 JST に上流の main を確認する(Actions タブから手動でも実行できる)。

- 更新があれば上の手順で取り込み、`automation/yomiyasu-upstream-sync` ブランチで PR を出し(開いていれば更新し)、`yomiyasu.yml` の検査を起動する。上流に yomiyasu 以外のスキルが増えたときや、上流のマニフェストが変わったときは、PR 本文にそう書かれる。
- 取り込みか組み立てが失敗したら、PR ではなく「yomiyasu 上流の同期: 取り込みが失敗しました」という issue にログを残し、実行を失敗させる。
- 同じ上流コミットについては、PR も issue も一度しか作らない。
