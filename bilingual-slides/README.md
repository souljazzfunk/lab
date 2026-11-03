# bilingual-slides

プロフェッショナルなスライドを、HTML アーティファクト 1 枚で作るスキル。eli5 スキルと同じ仕組みで、全テキストが日英の 2 言語を持ち、画面下のバーで JA / EN / Both とライト / ダークを切り替えられる。

- 1280×720 のステージを画面に合わせて縮める。← → / Space / スワイプで送り、`L` で言語、`D` でテーマ、`F` で全画面
- 印刷すると 1 スライド 1 ページの PDF になる
- スタイルは `<html data-style>` で選ぶ。`standard`（白地と青）と `organic`（Organic & Tech / ニュー・ナチュラル: アースカラー、セージグリーン、ウォームグレーに Space Grotesk の鋭い見出し）。指定が無ければ話題から選ぶ
- 型は表紙、目次、中扉、箇条書き、数字（KPI）、図（SVG）、比較カード、表、結論文。見本は [`assets/template.html`](plugin/skills/bilingual-slides/assets/template.html)
- [`scripts/check_slides.cjs`](plugin/skills/bilingual-slides/scripts/check_slides.cjs) が、全スライドを 3 言語 × 2 テーマで描いて、あふれ、重なり、2 行を超える見出し、22px 未満の文字、コントラスト不足、SVG ラベルのはみ出しを報告する。同じ原因の報告は 1 行にまとめ、`--shots` ではデッキ全体を 1 枚に並べたコンタクトシートも出す
- [`scripts/build_deck.cjs`](plugin/skills/bilingual-slides/scripts/build_deck.cjs) が、スライドだけの断片をテンプレートに差し込み、スタイル、タイトル、フォントを決める。テンプレートの CSS とスクリプト（約 21KB）を Claude が読み書きしなくて済む
- [`scripts/shelf_add.cjs`](plugin/skills/bilingual-slides/scripts/shelf_add.cjs) が、索引ページ「Artifact Shelf」に 1 行足す
- 色の値、ブランド色の入れ方、スタイルの足し方は [`references/styles.md`](plugin/skills/bilingual-slides/references/styles.md)（必要なときだけ読む）

## 使う

```
/plugin marketplace add souljazzfunk/lab
/plugin install bilingual-slides@lab
```

```
/bilingual-slides AI エージェント導入の社内提案
/bilingual-slides Organic で、再生可能エネルギー事業の紹介
```

## テンプレートを検査する

```bash
NODE_PATH="$(npm root -g)" node bilingual-slides/plugin/skills/bilingual-slides/scripts/check_slides.cjs bilingual-slides/plugin/skills/bilingual-slides/assets/template.html
NODE_PATH="$(npm root -g)" node bilingual-slides/plugin/skills/bilingual-slides/scripts/check_slides.cjs bilingual-slides/plugin/skills/bilingual-slides/assets/template.html --style organic
```
