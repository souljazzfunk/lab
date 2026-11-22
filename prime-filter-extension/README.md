# prime-filter-extension

Amazon Prime Video のウォッチリスト(`https://www.amazon.co.jp/gp/video/mystuff/watchlist`)から、プライム見放題の作品だけを一覧で表示する Chrome 拡張機能。

## 入れ方

1. `chrome://extensions` を開き、右上の「デベロッパーモード」を ON にする
2. 「パッケージ化されていない拡張機能を読み込む」でこのフォルダを選ぶ

## 使い方

ウォッチリストを開くと右下に「プライム見放題だけ見る」ボタンが出る。押すと、ウォッチリスト全件を Amazon から読み込み、プライム見放題の作品だけを画面全体の一覧で表示する。Esc か「閉じる」で戻る。

- 見出しに `プライム見放題 N 件 / ウォッチリスト M 件` を出す
- **CSV**: 一覧に出ている作品(タイトル、種類、ASIN、URL)を書き出す
- 読み込んだ件数が Amazon の示す件数(`estimatedTotal`)と合わないときは、赤字で警告を出す

## 仕組み

Amazon のウォッチリスト画面は、表示位置の近くのカードしか描画しない。スクロールに合わせて続きを読み込み、描画するカードも入れ替える。そのため画面のカードを数えたり隠したりする方式では、描画されていない作品を判定できず、隠すと Amazon 側の描画も崩れる。

この拡張は画面のカードを使わず、Amazon のデータを直接読む(`watchlist.js`)。

1. `/gp/video/mystuff/watchlist` の HTML に埋め込まれた JSON から、最初の 20 件と続きを取るためのトークンを読む
2. `/gp/video/api/paginateCollection` に POST し、応答の `pagination` を辿って `hasMoreItems` が false になるまで取る
3. ASIN で重複を除き、`estimatedTotal` と件数を突き合わせる

`entitlementType` が `Entitled` で、画像 URL のロゴ指定(`benefit-id/.../Prime/logos/`)が Prime のものを、プライム見放題とみなす。チャンネル作品は Entitled でもロゴが別の名前になる。

`paginateCollection` に送る値は、Amazon の画面がスクロール時に送る値を写したもの。Amazon が変えると応答が JSON でなくなり、一覧の代わりにエラーが出る。そのときは画面がスクロール時に送る値を見直して `watchlist.js` の `PAGE_PARAMS` を直す。

## テスト

```bash
node --test test/watchlist.test.mjs
```
