# simple-english

[Simple English](https://github.com/AminBlg/SimpleEnglish)(AminBlg 作、MIT)を lab の marketplace から入れられるようにしたもの。ASD-STE100 Simplified Technical English の考え方で、短い文・能動態・一語一義の平易な英語を書くスキル。

上流は `vendor/simple-english/` に無改造で置き、marketplace からは `simple-english/build.sh` で組み立てた最小構成の `simple-english/plugin/`(マニフェスト・スキル・LICENSE だけ)を配っている。著作権表示とライセンスは [`vendor/simple-english/LICENSE`](../vendor/simple-english/LICENSE) にある。

lab に置いている理由: claude.ai でスキルを GitHub から自動更新(auto-sync)するには、取り込み元のリポジトリに Claude GitHub App が入っている必要がある。上流は他人のリポジトリなので App を入れられない。lab に写しておけば、lab の marketplace 同期で更新が届く。

上流との違い:

- 上流の `plugin.json` にある hooks は配らない。全セッションでスキルを常時有効にする SessionStart と、Write/Edit のたびに走る lint で、どちらも claude.ai では動かない。スキルだけが要るので、`build.sh` がマニフェストから `hooks` を消して写す。
- 上流ルートの入れ子の marketplace.json、`evals/`、`tools/` などは配らない。yomiyasu で、上流ルートをそのまま配るとマーケットプレイス同期で skipped になったため。

## 使う

```
/plugin marketplace add souljazzfunk/lab
/plugin install simple-english@lab
```

使い方の詳細は上流の [README](../vendor/simple-english/README.md)。

## 上流の更新を取り込む

```bash
simple-english/sync-upstream.sh           # 既定は main。最後に build.sh も走る
git diff --stat vendor/simple-english simple-english/plugin
claude plugin validate --strict simple-english/plugin/.claude-plugin/plugin.json
git add vendor/simple-english simple-english && git commit
```

`UPSTREAM` に取り込んだコミットが記録される。`vendor/simple-english/` と `simple-english/plugin/` は手で編集しない。

### 毎日の自動チェック

`.github/workflows/simple-english-upstream-sync.yml` が毎日 8:57 JST に上流の main を確認する(Actions タブから手動でも実行できる)。

- 更新があれば上の手順で取り込み、`automation/simple-english-upstream-sync` ブランチで PR を出し(開いていれば更新し)、`simple-english.yml` の検査を起動する。上流に simple-english 以外のスキルが増えたときや、上流のマニフェストが変わったときは、PR 本文にそう書かれる。
- 取り込みか組み立てが失敗したら、PR ではなく「simple-english 上流の同期: 取り込みが失敗しました」という issue にログを残し、実行を失敗させる。
- 同じ上流コミットについては、PR も issue も一度しか作らない。
