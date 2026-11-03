---
name: bilingual-slides
description: プロフェッショナルなスライドを、日英バイリンガル（JA / EN / Both 切り替え）とライト / ダーク切り替えつきの HTML アーティファクト 1 枚で作る。キーボード・スワイプで送れて、PDF にも印刷できる。/bilingual-slides [テーマや素材] と打たれたとき、または「スライドを作って」「プレゼン資料を HTML で」「バイリンガルのデッキ」と頼まれたときに使う。
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

## 2. テンプレートから作る

このスキルの `assets/template.html` をコピーして、`<section class="slide">` を差し替える。`<head>` の CSS、下の `<nav class="bar">`、末尾の `<script>` は残す。この 3 つがステージの縮尺、送り操作、言語とテーマの切り替え、印刷を受け持つ。

- `<title>` は 2〜4 語の名前にする（例: `AI Agent Rollout`）
- 表紙の日付は JST で書く（`2026-11-03 (JST)`）
- 各スライドの `<footer class="foot">` にはデッキの短い名前を入れる。ページ番号は JS が入れる

### バイリンガルの書き方

全テキスト要素に `<span lang="ja">` と `<span lang="en">` を 1 つずつ持たせ、親に `class="t"` を付ける。

```html
<h2 class="title t"><span lang="ja">人は判断に集中する</span><span lang="en">People focus on decisions</span></h2>
```

- JA は JA だけ、EN は EN だけ、Both は JA の下に EN を小さく薄く出す（`max(22px, .62em)`）
- 1 行に並べたいもの（フッター）は `class="bi-inline"` にする。Both では「JA / EN」と並ぶ
- 数字や固有名詞だけの要素（`120h`、KPI の値）は言語を分けなくてよい
- SVG のラベルは `<text>` 1 つに `<tspan lang="ja">` と `<tspan lang="en">` を入れる。`setLang` が Both では EN を JA の下へ積み、EN では元の位置へ戻す。`text` には `x` を必ず書く
- 英語は意訳でよい。日本語の直訳より、短く言い切る英語を優先する

### 切り替えの約束（テンプレートが実装済み）

- `window.setLang(mode)`（`"ja"` / `"en"` / `"both"`、既定 `both`）と `window.setTheme(theme)`（`"light"` / `"dark"`、既定は `prefers-color-scheme`）。どちらも localStorage に覚える（try/catch 済み）
- 送り: ← → / Space / PageUp / PageDown / Home / End、スワイプ、バーのボタン。`L` で言語、`D` でテーマ、`F` で全画面
- URL の `#3` で 3 枚目から開く
- 印刷すると 1 スライド 1 ページの 1280×720 で出る

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

## 4. 配色とブランド

色はすべて `:root`（ライト）と `:root[data-theme="dark"]`（ダーク）、`@media (prefers-color-scheme: dark)` のトークンで持つ。スライドの中で色を直に書かない。

| トークン | 用途 | ライト（白地との比） | ダーク |
|---|---|---|---|
| `--ink` | 本文 | `#111827`（17.7） | `#f3f4f6` |
| `--ink-2` | 補足の本文 | `#374151`（10.3） | `#d1d5db` |
| `--muted` | キャプション、Both の EN | `#4b5563`（7.6） | `#9ca3af` |
| `--accent` | 強調の文字、小見出し | `#1d4ed8`（6.7） | `#8ab4ff` |
| `--accent-fill` | 中扉の地、主役の箱（白文字） | `#1d4ed8` | `#1e3a8a` |
| `--soft` / `--accent-soft` | 面 | `#f3f4f6` / `#eef2ff` | `#1a2230` / `#1c2747` |
| `--line` | 罫線、枠 | `#d1d5db` | `#334155` |
| `--s2` / `--s3` | 2・3 番目の系列 | `#0f766e` / `#b45309` | `#5eead4` / `#fbbf24` |

- 会社や製品のデッキは、そのブランド色を `--accent` と `--accent-fill` に入れる。ライトとダークの両方の値を決め、3 か所（ライト、ダーク、media query）すべてを書き換える
- 差し替えたら、検査の `low-contrast` が出ないことを確かめる（小さい文字は 4.5、40px 以上か 32px 以上の太字は 3）

## 5. 検査して直す（公開の前に）

ローカルに保存して、同梱の検査を通す（Chromium と Playwright を使う）。

```bash
NODE_PATH="$(npm root -g)" node <このスキルのディレクトリ>/scripts/check_slides.cjs deck.html --shots <scratchpad>/shots
```

全スライドを JA / EN / Both × ライト / ダークで 1280×720 に描いて、次を報告する。何か見つかると exit 1 で終わる。

- `slide-overflow` / `body-overflow`: スライドや本文の領域からあふれている
- `text-outside-slide`: 文字がスライドの端から 40px の内側に収まっていない
- `text-overlap` / `text-overflow-box`: 文字どうしの重なり、箱からのはみ出し
- `line-count`: 見出しや箇条書きが 2 行を超えた（結論文は 3 行）
- `stranded-last-line`: 最後の行に 1〜2 文字だけが落ちた
- `font-too-small`: 22px 未満の文字（SVG も含む）
- `low-contrast`: 文字色と地のコントラスト比が足りない（ダークでも測る）
- `svg-label-*`: ラベルが図の外、箱の外、ほかのラベルと重なる
- `page-hscroll` / `stage-not-fit` / `bar-overflow`: 400px・1024px・1440px の画面で、横スクロールが出る、スライドが切れる、バーがはみ出す

報告をすべて直して、`No layout issues found.` が出るまで繰り返す。直し方は上の「入る量」の規則に従う。文字を小さくして逃げない。

検査は見た目の良し悪しまでは判断しない。`--shots` の PNG（Both のライト、Both のダーク、EN のライト）を見て、余白の偏り、のっぺりした面、同じ型の連続がないかを目で確かめる。Playwright が無い環境では、各モードのスクリーンショットを撮って同じ項目を目で確かめる。

## 6. 公開する

`artifact-design` スキルを読んでから、手書きの HTML ページとして Artifact ツールで公開する（`icon: "slides"`）。Slides 型のアーティファクトからは作らない。JA / EN / Both の切り替えを持てないため。

## 7. 棚に追加する

公開したら、索引のアーティファクト「Artifact Shelf」(https://claude.ai/artifact/5Yk2Pzs2hRmdho9zCQJeQb) に追加する。

1. `path: "index.html"` で読む。生のページがローカルに保存される。`path` なしの読み取りはサービスの外枠つきで返るので、編集する元にはしない
2. 再公開が受け付けられるように、URL を `path` なしでも 1 回読む
3. 保存したファイルの、今月の一覧の先頭に `<li>` を足す（今月の節が無ければ作る）。タイトル、`SLIDES` タグ、今日の日付（JST）を入れる。ヘッダーの件数と、フッターのスナップショット日付を更新する
4. そのファイルを `url` つきで再公開して、リンクを変えない

Topic: $ARGUMENTS
