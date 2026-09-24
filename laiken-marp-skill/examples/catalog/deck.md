---
marp: true
paginate: true
theme: laiken-light
title: laiken-marp-skill 型カタログ
author: らいけん
---

<style>
/* カタログ用：上端のヘッダに型の名前を出す。見出しと重ならないよう上の余白を広げる */
section { padding-top: 104px; }
header { font-size: 24pt; color: #a8501f; font-weight: 700; top: 34px; left: 68px; }
/* 図が主役のスライド */
img[alt~="center"] { display: block; margin: 48px auto 0; }
/* 挿絵。右端は本文の左右余白より内側へ */
.ill { position: absolute; right: 96px; bottom: 80px; width: 240px; }
/* スクリーンショット：中央、角丸、枠 */
img[alt~="shot"] { display: block; margin: 40px auto 0; border-radius: 14px; border: 1px solid #d9d2c2; }
/* ステップバー：見出しの上に置く現在地 */
img[alt~="stepbar"] { display: block; margin: 0 0 32px; }
/* 補足ボックス */
.gbox { position: absolute; left: 0; right: 0; margin: 0 auto;
        width: fit-content; min-width: 900px; max-width: 1144px;
        bottom: 64px; background: #f0ece2; border: 3px solid #d9d2c2;
        border-radius: 18px; padding: 16px 56px; text-align: center; }
.gbox, .gbox p { font-size: 32pt; line-height: 1.35; }
.gbox p { margin: 0; }
</style>

<!-- _class: top -->
<!-- _paginate: false -->

# laiken-marp-skill<br>型カタログ

らいけん（X: @thunder_bark）

---

<!-- _class: crosshead -->
<!-- _header: "" -->

# デモで使わなかった型を、<br>1枚ずつ見てみよう

---

<!-- _class: image-full -->
<!-- _header: 型：image-full（テーマ） -->

# 東京だけ、とびぬけて大きい

![w:1000](./images/bars.svg)

---

<!-- _class: split -->
<!-- _header: 型：split（テーマ） -->

# スマホでも1本だけ

- 画面が小さいほど
- グラフは1つに絞る

![bg right:40% contain](./images/phone.svg)

---

<!-- _header: 型：横帯スタック（図） -->

# ダッシュボードは4階建て

![center w:1140](./images/stack.svg)

---

<!-- _header: 型：番号付きラベル（図） -->

# 作る順番は3つ

![center w:1140](./images/numbered.svg)

---

<!-- _header: 型：箱の外の上にラベル（図） -->

# データが画面に届くまで

![center w:1140](./images/outer-labels.svg)

---

<!-- _header: 型：挿絵（右下） -->

# 最後は目で見る

- 隣の人に見せる
- 2秒で分かるか聞く

<img src="./images/magnifier.svg" class="ill">

---

<!-- _header: 型：スクリーンショットを中央に -->

# 表のページは、こうなる

![shot w:720](./images/shot-demo.png)

---

<!-- _header: 型：表の注目行に網掛け -->

<style scoped>
table tr:nth-child(3) td { background: rgba(201, 96, 42, .12); }
</style>

# 迷ったら、この表

| 言いたいこと | 使うグラフ |
| --- | --- |
| 増えた、減った | 折れ線 |
| どっちが大きい | 横棒 |
| どれくらいの割合 | 積み上げ棒 |
| どこで起きた | 地図 |

---

<!-- _header: 型：引用枠（実在の一言だけ） -->

# 頼んだのは、この一言だけ

> これforkしてLaiken用に改造して

<!-- このスキルを作ったときに、らいけんが Claude Code に送った依頼文そのまま -->

---

<!-- _header: 型：h2（小見出し） -->

# グラフは2つに分ける

## 見せる用

1つだけ、画面いっぱいに

## 調べる用

残りは全部、別のシートへ

---

<!-- _header: 型：吹き出しの寸劇 -->

# 会議でよくある光景

![center w:1140](./images/skit.svg)

---

<!-- _header: 型：想定反論（1枚目） -->

# 9個とも大事なんですけど！

- 全部、頑張って作った
- 消すのはもったいない

---

<!-- _header: 型：想定反論（2枚目） -->

# 消さなくて大丈夫です

- 別のシートに移すだけ
- 見たい人は、そこで見る

---

<!-- _header: 型：誤解の先回り -->

# もしかして、<br>これを思い浮かべてませんか…？

![center w:330](./images/pie12.svg)

---

<!-- _header: 型：ステップバーで現在地 -->

![stepbar w:1140](./images/stepbar-2.svg)

# 1つを、画面いっぱいに

- 小さいグラフを並べない
- 主役は画面の半分以上

---

<!-- _header: 型：用語の導入 -->

# 見る人が最初に見る「主役」

- 画面で一番大きい
- 色がついている

<div class="gbox">

主役は、1画面に1つだけ

</div>

---

<!-- _class: crosshead -->
<!-- _header: "" -->

# 気になる型から、<br>1つ使ってみませんか？
