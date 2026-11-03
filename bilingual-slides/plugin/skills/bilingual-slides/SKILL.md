---
name: bilingual-slides
description: プロフェッショナルなスライドを、日英バイリンガル（JA / EN / Both 切り替え）とライト / ダーク切り替えつきの HTML アーティファクト 1 枚で作る。スタイルは Standard と Organic & Tech（ニュー・ナチュラル）から選べる。キーボード・スワイプで送れて、PDF にも印刷できる。/bilingual-slides [テーマや素材] と打たれたとき、または「スライドを作って」「プレゼン資料を HTML で」「バイリンガルのデッキ」と頼まれたときに使う。
---

# bilingual-slides

会議でそのまま映せる、プロフェッショナルなスライドを HTML アーティファクト 1 枚で作る。eli5 スキルと同じ仕組みで、全テキストが日英の 2 言語を持ち、JA / EN / Both とライト / ダークを画面下のバーで切り替えられる。書体はサンセリフだけ。

素材がなくて内容の判断が要るときも、ユーザーに確認しないで、妥当な仮定で作り切る。仮定は最後の報告に 1 行で書く。

## 1. 先に話の筋を決める

- 1 スライド 1 メッセージ。見出しはトピック名ではなく、結論を言い切る文にする（「課題」ではなく「時間の 4 割が転記に消えている」）
- 見出しだけを順に読んで話が通ること。通らなければ、作る前に順番を直す
- 既定の構成は 8〜12 枚。表紙 → 目次 → （中扉 → 本文）× 2〜3 → 結論 → 次の一手
- 結論を最初に言う構成（ピラミッド型）を既定にする。`pyramid-principle` スキルがあれば筋立てに使ってよい
- 数字には出典か前提を添える。素材にない数字を作らない。仮の数字はそれと分かる書き方にする

## 2. スライドだけを書く

テンプレート（`assets/template.html`、約 32KB）を丸ごと Read したり、コピーして Write したりしない。CSS・バー・スクリプトはスクリプトが差し込む。書くのは `<section class="slide">` の並びだけ。

1. 見本のスライドを一度だけ読む（約 11KB）。CSS とスクリプトは読まない
   ```bash
   sed -n '/SLIDES:BEGIN/,/SLIDES:END/p' <このスキルのディレクトリ>/assets/template.html
   ```
2. スライドの断片を scratchpad に Write する（例: `<scratchpad>/slides.html`。`<section class="slide">` だけを並べる）
3. 組み立てと検査を 1 回のコマンドで回す
   ```bash
   SK=<このスキルのディレクトリ>; node $SK/scripts/build_deck.cjs <scratchpad>/slides.html -o <scratchpad>/deck.html --style standard --title "AI Agent Rollout" && NODE_PATH="$(npm root -g)" node $SK/scripts/check_slides.cjs <scratchpad>/deck.html
   ```
   `build_deck.cjs` が `<html data-style>`、`<title>`（2〜4 語の名前）、そのスタイルのフォントの `<link>` だけを残す処理を受け持つ
4. 直すときは `slides.html` を Edit で部分的に直し、3 のコマンドをもう一度回す。`deck.html` は Read も Edit もしない

- 表紙の日付は JST で書く（`2026-11-03 (JST)`）
- 各スライドの `<footer class="foot">` にはデッキの短い名前を入れる。ページ番号は JS が入れる
- 言語（JA / EN / Both、既定 Both）とテーマ（ライト / ダーク）の切り替え、← → / スワイプ / `L` `D` `F` のキー、`#3` での頁指定、1 スライド 1 ページの印刷は、テンプレートが実装済み。手を入れない

### バイリンガルの書き方

全テキスト要素に `<span lang="ja">` と `<span lang="en">` を 1 つずつ持たせ、親に `class="t"` を付ける。

```html
<h2 class="title t"><span lang="ja">人は判断に集中する</span><span lang="en">People focus on decisions</span></h2>
```

- Both では JA の下に EN を小さく薄く出す（`max(22px, .62em)`）
- 1 行に並べたいもの（フッター）は `class="bi-inline"` にする。Both では「JA / EN」と並ぶ
- 数字や固有名詞だけの要素（`120h`、KPI の値）は言語を分けなくてよい
- SVG のラベルは `<text>` 1 つに `<tspan lang="ja">` と `<tspan lang="en">` を入れる。Both では EN が JA の下に積まれる。`text` には `x` を必ず書く
- 英語は意訳でよい。日本語の直訳より、短く言い切る英語を優先する

## 3. スライドの型と入る量

ステージは 1280×720 px。左右 80px、上 56px、下 84px（フッター）の余白を使い、本文に使える幅は 1120px。**入る量は Both モードで数える**。Both は行数がほぼ倍になるので、Both で収まれば JA と EN でも収まる。

| 型 | マークアップ | 上限（Both で） |
|---|---|---|
| 表紙 | `.slide.cover` に `.kicker` `h1.t` `.sub.t` `.meta` | h1 は JA 14 字 / EN 32 字で 1 行 |
| 目次 | `ol.agenda` の `li > span.t` | 4 項目 |
| 中扉 | `.slide.section.on-accent` に `.num` と `h2.title.t` | 見出し 1 行 |
| 箇条書き | `ul.points` の `li.t` | 4 項目、各 JA 28 字 / EN 55 字 |
| 数字 | `.kpis > .kpi` に `.v`（数字）と `.l.t`（ラベル） | 3 つ |
| 図 | `figure.fig > svg`（viewBox 幅 1120） | ラベルは横に 4 つまで |
| 比較 | `.cols`（2 列）/ `.cols.three`（3 列）の `.card` に `h3.t` `p.t` | カード 1 枚に本文 1〜2 行 |
| 表 | `table.tbl`、強調行は `tr.hl` | ヘッダ＋3 行、3〜4 列 |
| 結論 | `.body.center > p.statement.t` | JA 24 字 / EN 60 字 |

- スライドの見出しは `p.kicker`（小見出し、1 語）と `h2.title.t`（結論の文）の組。見出しは JA 22 字 / EN 40 字以内で 1 行に収める
- 上限を超えたら、文字を小さくしない。削るか、2 枚に割る
- 1 スライドの強調（`<strong>`）は 1 か所まで。残すのはパンチラインの数字か言葉だけ
- 同じ型ばかり続けない。3 枚続けて箇条書きになったら、どれかを数字・図・比較に変える
- 図や表に入れる文字は 22px 未満にしない（Both の EN でも）。SVG のラベルは 28px（副ラベルは 24px）を基準にする

### 図

- SVG は `viewBox="0 0 1120 H"`（H は 260〜360）で描き、ステージと 1:1 の縮尺にする
- 塗りと線は `fill="var(--soft)"` `stroke="var(--line)"` のようにトークンで書く。16 進で書くとダークモードで切り替わらない
- ラベルの入る箱は、長いほうの行（EN は 0.55em/字、JA は 1em/字）＋左右 16px より広くする。Both では 2 行になるので、箱の高さは 120px 以上にする
- グラフを描くときは `dataviz` スキルを先に読む。系列の色は `--accent` `--s2` `--s3` の順に使う

## 4. スタイルと配色

見た目の系統は `build_deck.cjs --style` で選ぶ。ライト / ダークはどのスタイルにもある。

| `--style` | 見た目 | 向く話題 |
|---|---|---|
| `standard`（既定） | 白地と青、Inter + Noto Sans JP、角丸 16px、太い罫 | 社内提案、報告、技術、数字中心の話 |
| `organic`（Organic & Tech / ニュー・ナチュラル） | アースカラー（生成り、セージ、テラコッタ）、Space Grotesk の見出しと Zen Kaku Gothic New、角丸 28px、細い罫、円の飾り | サステナビリティ、ウェルビーイング、人や地域、ブランド、デザイン、人を中心に置くテクノロジー |

選び方（ユーザーには聞かない）: 指定（「Organic で」「ニュー・ナチュラルで」など）があれば従う。無ければ、話題が `organic` の向く話題に当たるときだけ `organic`、それ以外は `standard`。指定なしで選んだときは、最後の報告に「スタイル: Organic（話題から選択）」と 1 行書く。

- 色はトークン（`--ink` `--ink-2` `--muted` `--accent` `--accent-fill` `--soft` `--accent-soft` `--line` `--s2` `--s3`）で書く。スライドの中で色を直に書かない
- ブランド色を入れるとき、スタイルを足すときだけ `references/styles.md` を読む。それ以外では読まない

## 5. 検査して直す

検査は 2 の 3 のコマンドで回る。全スライドを JA / EN / Both × ライト / ダークで 1280×720 に描き、400px・1024px・1440px の画面でも試す。見つかると exit 1。同じ原因の報告は 1 行にまとまり、`[slides 2,4-10 ja,both light]` のように起きた場所が付く。

報告は `slide-overflow` `body-overflow` `text-outside-slide` `text-overlap` `text-overflow-box` `line-count` `stranded-last-line` `font-too-small` `low-contrast` `svg-label-*` `page-hscroll` `stage-not-fit` `bar-overflow`。名前のとおりの意味で、直し方は 3 の「入る量」の規則に従う。文字を小さくして逃げない。`No layout issues found.` が出るまで繰り返す。

見た目は、問題が 0 件になってから **1 回だけ** `--shots <scratchpad>/shots` を付けて回して確かめる。開くのはコンタクトシート（デッキ全体が 1 枚に入る画像）だけにする。

- `sheet-both-light.png` は必ず見る。余白の偏り、のっぺりした面、同じ型の連続を探す
- `sheet-both-dark.png` と `sheet-en-light.png` は、図や飾りを足したデッキのときだけ見る（色と文字量は検査が測っている）
- スライド 1 枚ずつの PNG（`slide-03-both-light.png` など）は、シートで気になった枚だけ開く

Playwright が無い環境では、Both のライトのスクリーンショットを撮って同じ項目を目で確かめる。

## 6. 公開する

`artifact-design` スキルを読んでから、`<scratchpad>/deck.html` を手書きの HTML ページとして Artifact ツールで公開する（`icon: "slides"`）。デザインの規則はテンプレートが満たしているので、スキルを読んだあとで `deck.html` を開き直したり書き直したりしない。Slides 型のアーティファクトからは作らない。JA / EN / Both の切り替えを持てないため。

## 7. 棚に追加する

公開したら、索引のアーティファクト「Artifact Shelf」(https://claude.ai/artifact/5Yk2Pzs2hRmdho9zCQJeQb) に追加する。棚のページは読み込むたびに数千トークンかかるので、中身は手で読み書きしない。

1. `path: "index.html"` で読む。生のページがローカルに保存される（`path` なしの読み取りはサービスの外枠つきで返るので、編集の元にはしない）
2. 再公開が受け付けられるように、URL を `path` なしでも 1 回読む
3. 保存したファイルを Read も Write もしないで、スクリプトで 1 行足す。今月の節（無ければ作る）の先頭に入り、件数とスナップショットの日付（JST）も更新される
   ```bash
   node <このスキルのディレクトリ>/scripts/shelf_add.cjs <保存されたファイル> --title "<タイトル>" --url <公開した URL> --tag Slides
   ```
4. そのファイルを `url` つきで再公開して、リンクを変えない

Topic: $ARGUMENTS
