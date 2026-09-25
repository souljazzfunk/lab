# laiken-marp-skill

らいけん（X: [@thunder_bark](https://x.com/thunder_bark)）が登壇スライドを Marp で作るときの、ストーリー・図・デザインバランスの型です。AIエージェント（Claude Code など）に読ませるスキルの形にしてあり、人が読んでもそのまま使えます。

みのるん（[@minorun365](https://x.com/minorun365)）の [minorun-marp-skill](https://github.com/minorun365/minorun-marp-skill) をフォークして改造しました。

![見本デッキ](examples/sample/preview.png)

## 元リポジトリからの主な変更

| 項目 | minorun-marp-skill | laiken-marp-skill |
|---|---|---|
| テーマ | 黒地＋シアン（minorun-dark） | ジャスミンライスの地＋唐辛子の深紅＋カルダモンの緑（laiken-light） |
| 書体 | 丸ゴシック | サンセリフのみ（ヒラギノ角ゴ／游ゴシック／Noto Sans CJK） |
| 本文 | 26pt | 36pt。下限24pt |
| 大原則 | ― | 5歳児でもわかるスライド（2秒で理解、1項目20文字、箇条書き4行まで） |
| 図 | marker の矢印、16pt下限 | line＋polygon の矢印、viewBox幅1140、24pt下限 |
| 検査 | 黒地専用 | ページの地の色を自動で取る（明るい地でも黒地でも測れる） |
| 言語 | 日本語 | 日本語・英語・両方（EN / JA / Both）。HTML の右上で切り替え |
| 配色の切り替え | ― | HTML の左下の小さなボタンでダーク / ライト |

## 中身

| 場所 | 内容 |
|---|---|
| `skills/laiken-slide-story` | 5歳児原則、らいけんのデッキの約束、つかみ、中扉、段階的な開示、見出しの文体、締め方、尺の見積り |
| `skills/laiken-slide-figures` | 図の情報量の絞り方、laiken-light の配色でのSVGパターン、文字サイズの下限、挿絵の置き方 |
| `skills/laiken-slide-design` | 文字サイズと1スライドの量、余白の測り方、縦のバランス、配色、表とコードの型、Marpの罠 |
| `theme/laiken-light.css` | 唐辛子の深紅とカルダモンの緑の Marp テーマ（タイ・スリランカのカレーから）。二か国語の出し分けとダークの配色を含む |
| `tools/` | 書き出したPDFとSVGを実測する検査スクリプトと、HTML に言語・配色の切り替えを足す `add-toggles.py` |
| `examples/sample` | 見本デッキ（日英の二か国語）。`examples/broken` は検査が反応することを確かめるための、わざと崩した版 |

## 使い方

Claude Code で使うなら、`skills/` の3つを自分のスキル置き場へコピーします。

```bash
cp -r skills/* ~/.claude/skills/
```

テーマと検査スクリプトは、スライドを置くリポジトリへ `theme/` と `tools/` ごとコピーしてください。

```bash
marp --no-stdin deck.md --pdf --theme theme/laiken-light.css --allow-local-files

python3 tools/check-margins.py deck.pdf         # 中身の下端と右端の空き
python3 tools/check-gaps.py deck.pdf            # 図や箱と、隣の本文の間隔
python3 tools/check-figure-text.py deck.pdf     # 24pt未満の文字、箱の縁に詰まった文字
node tools/check-svg-box-fit.mjs images/*.svg   # SVGの文字が箱に収まっているか
python3 tools/check-reuse-diff.py new.md old.md # 流用したスライドの、見出しと図の対応
python3 tools/check-contrast.py                 # テーマの配色のコントラスト比
python3 tools/check-static.py <デッキのディレクトリ> # 文字サイズ・矢印・配色・見出しの語尾
python3 tools/add-toggles.py deck.html          # HTML に EN / JA / Both とダーク / ライトの切り替えを足す
```

## 二か国語とダークモード

1つの `deck.md` に日本語と英語を並べて書きます。

```markdown
---
theme: laiken-light
lang: mul        # ja＝日本語だけ、en＝英語だけ、mul＝Both
---

# <span class="ja">直すのは3か所だけ</span><span class="en">Just three things to fix</span>

![center ja w:1144](./images/flow.svg)
![center en w:1144](./images/flow.en.svg)
```

PDF はフロントマターの `lang` のとおりに書き出されます。HTML は、書き出したあとに `add-toggles.py` をかけると、右上に EN / JA / Both のトグル、左下に目立たないダーク / ライトのボタンが付きます。選んだものはブラウザに記憶されます。

```bash
marp --no-stdin deck.md --html --theme theme/laiken-light.css -o deck.html
python3 tools/add-toggles.py deck.html
```

書き方の決まり（Both での分量、英語版の図の作り方など）は `skills/laiken-slide-design` の「二か国語」にあります。

## CI

`.github/workflows/laiken-marp-skill.yml` が、`laiken-marp-skill/` を変えたプルリクエストで次を走らせます。

| ジョブ | 内容 |
|---|---|
| `lint` | `tools/` のコードの検査。Python は ruff（設定は `ruff.toml`）、シェルは shellcheck、JavaScript は `node --check` |
| `static` | `check-contrast.py`（ライトとダークの両方）と `check-static.py`。崩した版（`examples/broken`）を検出できることも確かめる |
| `decks` | `tools/ci-decks.sh`。見本・デモ・カタログを書き出して検査4本が NG 0 件、崩した版では4本とも NG が出ること。`lang: mul` のデッキは EN だけ・JA だけの版も測る。HTML には切り替えを足す |

`decks` が書き出した PDF と HTML（切り替え付き）は、Actions の実行結果のページから `decks-pdf` と `decks-html` としてダウンロードできます。`deck.pdf` と `deck.html` はリポジトリには入れません。

手元で同じことをするなら、`laiken-marp-skill/` で次を実行します。

```bash
sh tools/ci-decks.sh
ruff check tools/ && shellcheck tools/*.sh
```

検査スクリプトが使うもの:

- [Marp CLI](https://github.com/marp-team/marp-cli)（`npm i -g @marp-team/marp-cli`）と Chrome / Chromium
- poppler（`pdftoppm` `pdfinfo`）と mupdf-tools（`mutool`）。macOS なら `brew install poppler mupdf-tools`
- Python 3 と Pillow

`check-svg-box-fit.mjs` は Marp CLI に同梱の puppeteer-core を借ります。場所が違う環境では `MARP_NODE_MODULES` と `CHROME_PATH` で指定できます。Claude Code のクラウド環境では `/opt/pw-browsers/chromium` を自動で使います（Marp CLI には `CHROME_PATH=/opt/pw-browsers/chromium` を渡してください）。

## License

Apache License 2.0。原著作物は Copyright 2026 Minoru Onda。改変部分は Copyright 2026 らいけん。変更点は `NOTICE` を参照してください。
