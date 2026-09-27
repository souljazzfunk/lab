# チュートリアル: pstack で小さな機能を足す

[English](tutorial.en.md)

このチュートリアルでは、pstack を Claude Code に入れ、このリポジトリの `pstack-cc/build.py` に `--stats` オプションを 1 つ足します。`--stats` は、置き換えルールごとに「何回当たったか」を表で出すオプションです。

途中で pstack の主なスキルを順に使います。コードの仕組みを `/pstack:how` で調べ、経緯を `/pstack:why` で調べ、実装を `/pstack:poteto-mode` に任せ、最後に `/pstack:teach` で説明させます。所要時間は 40 分ほどです。

## 始める前に

次のものを用意します。

- Claude Code(`claude --version` が 2.1 以降)
- `git` と Python 3.11 以降
- `souljazzfunk/lab` を clone できる GitHub アカウント

エージェントの出力は毎回少しずつ変わります。このチュートリアルの「見えるもの」は、文面そのものではなく、出力に含まれているはずの要素を書いています。

## 1. 練習用のリポジトリを用意する

まず、リポジトリを clone して練習用のブランチを作ります。

```bash
git clone https://github.com/souljazzfunk/lab.git pstack-tutorial
cd pstack-tutorial
git switch -c tutorial/build-stats
python3 pstack-cc/build.py --check
```

最後のコマンドは次の 1 行を出します。

```
pstack-cc/plugin/ は最新です。
```

この 1 行が出れば、手元の生成物とソースが一致しています。以降の変更がこれを壊していないかは、同じコマンドで確かめます。

## 2. pstack を入れる

同じディレクトリで Claude Code を起動します。

```bash
claude
```

Claude Code の中で、次の 2 つを順に実行します。

```
/plugin marketplace add souljazzfunk/lab
/plugin install pstack@lab
```

インストールが終わったら、Claude Code を再起動します。`/pstack:` と入力すると、補完の候補に `/pstack:poteto-mode`、`/pstack:how`、`/pstack:why` などが並びます。

## 3. モデルの割り当てを決める

次に、pstack がサブエージェントに使うモデルを決めます。

```
/pstack:setup-pstack
```

役割ごとのモデルの一覧が出て、そのまま使うかを聞かれます。ここでは **そのまま使う** を選びます。

終わると `~/.claude/pstack-models.md` ができます。別のターミナルで中身を見ると、`how explorer: sonnet` のような行が並んでいます。

```bash
cat ~/.claude/pstack-models.md
```

使っているプランで `fable` が使えない場合、スキルはそのモデルを飛ばして親のモデルで動きます。ここで設定を変える必要はありません。

## 4. `/pstack:how` でコードの仕組みを聞く

実装を頼む前に、変更する場所の仕組みをエージェントに説明させます。

```
/pstack:how pstack-cc/build.py はどうやって vendor/pstack から pstack-cc/plugin を作っているか
```

エージェントは最初に質問の複雑さを判定します。複数の観点があると判断すると、探索役のサブエージェントを 2〜4 体、並列に起動します。

数分後、次の見出しを持つ説明が返ってきます(当てはまらない見出しは省かれます)。

- Overview
- Key Concepts
- How It Works
- Where Things Live
- Gotchas

説明の中に `RULES`、`min_hits`、`apply_rules` が出てくることを確かめます。この 3 つが、次の手順で足す `--stats` の材料です。

## 5. `/pstack:why` で経緯を聞く

コードを読んでも「なぜそうしたか」は分かりません。そこで `/pstack:why` を使います。

```
/pstack:why build.py はなぜ置き換えルールごとに min_hits を持っているのか
```

エージェントは git の履歴、README、コードを並列に調べます。返ってくる答えには、根拠になったコミットやファイルが引用されています。

答えの中に「上流の文章が変わってルールが当たらなくなったら、build を失敗させるため」という趣旨の説明があることを確かめます。`--stats` は、この「当たった回数」を人間にも見えるようにする機能です。

## 6. `/pstack:poteto-mode` に実装させる

ここで実装を頼みます。

```
/pstack:poteto-mode pstack-cc/build.py に --stats オプションを足して。置き換えルールごとに、当たった回数と min_hits を表で出す。pstack-cc/plugin/ は書き換えない。python3 pstack-cc/build.py --stats の実際の出力と、--check が通ることを証拠として見せて
```

エージェントは作業の種類から playbook を選びます。今回は **Feature** です。最初に todo リストが出て、先頭に Feature playbook の手順が並びます。

- `how` over the affected subsystem.
- `architect` for parallel design exploration.
- 以下、throughput checkpoint、実装の委任、検証、コミット、PR

手順を飛ばす場合も、リストから消さずに `skip: <理由>` と書きます。小さな変更なので、いくつかの手順は理由付きで飛ばされるはずです。

実装が終わると、エージェントは次のものを含む返事を書きます。

- 何を作ったか。どのデータの形を選び、なぜそうしたか
- 判断に使った principle の名前(例: Laziness Protocol、Prove It Works)
- `python3 pstack-cc/build.py --stats` を実際に動かした出力
- `python3 pstack-cc/build.py --check` が通った出力

最後に、自分でも同じコマンドを動かします。Claude Code の入力欄で `!` を先頭に付けると、シェルのコマンドを実行できます。

```
!python3 pstack-cc/build.py --stats
!python3 pstack-cc/build.py --check
```

1 つ目はルールごとの行を持つ表を出します。2 つ目は手順 1 と同じ「最新です」の 1 行を出します。`git status` で `pstack-cc/plugin/` に変更がないことも確かめます。

エージェントが PR を作ろうとしたら、ここでは止めます。練習用のブランチなので、push は不要です。

## 7. `/pstack:teach` で説明させる

最後に、エージェントがした選択を説明させます。

```
/pstack:teach --stats をこの形で実装した理由を教えて。ほかにどんな形があり、何と何を比べて決めたか
```

`/pstack:teach` は内部で `how` と `why` を呼び、結果を 1 つの説明にまとめます。返ってくる説明には、実際に選んだ形と、選ばなかった形の比較が入っています。説明に納得できない点があれば、そのまま質問を続けます。

## 8. 片付ける

練習用のブランチとディレクトリを消します。

```bash
cd ..
rm -rf pstack-tutorial
```

`~/.claude/pstack-models.md` とインストールしたプラグインは残ります。自分のリポジトリでもそのまま使えます。

## ここまでにしたこと

pstack を入れ、モデルを割り当て、`how` と `why` でコードを理解してから、`poteto-mode` に機能を実装させて証拠付きで確かめました。最後に `teach` で、エージェントの判断を自分の言葉で理解できる形にしました。

## 次にすること

- 自分のリポジトリで `/pstack:create-verification-skill` を実行します。エージェントがアプリを実際に動かして、自分の変更を確かめられるようになります。pstack の作者はこれを最も大事なスキルとしています。
- エージェントの間違いを直したら、同じ間違いを二度と起こさせない場所を探します。作者は講演で、コードの構造で起こりえなくする、lint や CI で止める、ルールやスキルに書く、の順に検討するよう勧めています。レビューで人が指摘するだけでは、PR の数に追いつきません。
- スキル同士の関係は [スキル地図](skill-map.ja.md) にあります。
- Cursor と Claude Code の違いは [`claude-code.md`](../claude-code.md) にあります。
- 作者 Lauren Tan(poteto)の解説記事(英語)は [The Complete Guide to pstack Pt. 1](https://x.com/poteto/status/2094457600259842065) と [Pt. 2](https://x.com/poteto/status/2097732320606507506) です。
