# yomiyasu

[yomiyasu](https://github.com/nanaism/yomiyasu)(nanaism 作、MIT)を lab の marketplace から入れられるようにしたもの。AI が書いた不自然な日本語を、読みやすく自然な文章に書き直すスキル。

上流はそのまま Claude Code のプラグインなので、変換はせず `vendor/yomiyasu/` に無改造で置き、marketplace からそこを直接配っている。著作権表示とライセンスは [`vendor/yomiyasu/LICENSE`](../vendor/yomiyasu/LICENSE) にある。

## 使う

```
/plugin marketplace add souljazzfunk/lab
/plugin install yomiyasu@lab
```

使い方の詳細は上流の [README](../vendor/yomiyasu/README.md)。

## 上流の更新を取り込む

```bash
yomiyasu/sync-upstream.sh           # 既定は main。コミットやタグも指定できる
git diff --stat vendor/yomiyasu     # 上流で何が変わったかを見る
claude plugin validate --strict vendor/yomiyasu/.claude-plugin/plugin.json
git add vendor/yomiyasu yomiyasu && git commit
```

`UPSTREAM` に取り込んだコミットが記録される。`vendor/yomiyasu/` は手で編集しない。
