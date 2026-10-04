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
