---
marp: true
paginate: true
theme: laiken-light
title: ダッシュボード、5歳児に説明できますか？
author: らいけん
---

<style>
/* 図が主役のスライド。見出しとの間に36px以上 */
img[alt~="center"] { display:block; margin:56px auto 0; }
/* 図の下のキャプション */
.cap { text-align:center; color:#7a6a52; font-size:24pt; margin-top:36px; }
/* 比較のスライドは大きい数字を2つだけ */
.vs { display:grid; grid-template-columns:1fr 3px 1fr; align-items:center; margin-top:56px; }
.vs .bar { background:#d9d2c2; height:220px; }
.vs div { text-align:center; }
.vs .num { font-size:88pt; font-weight:700; line-height:1.1; }
.vs .num.key { color:#c9602a; }
.vs .lbl { font-size:30pt; color:#6d675a; }
/* 補足ボックス（laiken-slide-design の確定デザイン） */
.gbox { position:absolute; left:0; right:0; margin:0 auto;
        width:fit-content; min-width:900px; max-width:1144px;
        bottom:64px; background:#f0ece2; border:3px solid #d9d2c2;
        border-radius:18px; padding:16px 56px; text-align:center; }
.gbox, .gbox p { font-size:32pt; line-height:1.35; }
.gbox p { margin:0; }
.gbox.key { background:#c9602a; border-color:#c9602a; }
.gbox.key, .gbox.key p { color:#ffffff; font-weight:700; }
</style>

<!-- _class: top -->
<!-- _paginate: false -->

# ダッシュボード、<br>5歳児に説明できますか？

らいけん（X: @thunder_bark）

<!-- デモ用のデッキ。laiken-marp-skill のテーマと型で組んでいる -->

---

<!-- _class: crosshead -->

# 作ったグラフ、見てもらえてますか？

---

<!-- _class: crosshead -->

# 見た人、2秒で分かりましたか？

<!-- 2つ目の問いで手が減る。ここが本編の入口 -->

---

# こうなりがち

- グラフが9個ならぶ
- 色が12色ある
- 数字が細かすぎる

<div class="gbox">

見た人は、どこを見ればいいか迷います

</div>

---

<!-- _class: crosshead -->

# じゃあ、どうすればいいの？

---

# 伝わるまでの3ステップ

![center w:1144](./images/steps-1.svg)

<p class="cap">まず、言いたいことを1つ決める</p>

<!-- 同じ図を3枚に割って、1つずつ足していく -->

---

# 伝わるまでの3ステップ

![center w:1144](./images/steps-2.svg)

<p class="cap">次に、その1つを画面いっぱいに</p>

---

# 伝わるまでの3ステップ

![center w:1144](./images/steps-3.svg)

<p class="cap">最後に、主役だけに色をつける</p>

---

# 見る場所が1つになる！

<div class="vs">
<div><div class="num">9個</div><div class="lbl">いままでのグラフ</div></div>
<div class="bar"></div>
<div><div class="num key">1個</div><div class="lbl">言いたいことのグラフ</div></div>
</div>

<!-- 残りの8個は、必要な人だけが見る別のシートへ -->

---

# 迷ったら、この表

| 言いたいこと | 使うグラフ |
| --- | --- |
| 増えた、減った | 折れ線 |
| どっちが大きい | 横棒 |
| どれくらいの割合 | 積み上げ棒 |
| どこで起きた | 地図 |

---

# 主役だけ色をつける式

```text
IF [地域] = "東京"
THEN "主役"
ELSE "その他"
END
```

この結果を「色」に置くだけ

<!-- Tableau の計算フィールド。主役はアクセント色、その他はグレーにする -->

---

# …これで完成！ではないんです

- 隣の人に2秒だけ見せる
- 「何の話？」と聞いてみる

<div class="gbox key">

ひとことで言えたら合格

</div>

---

<!-- _class: crosshead -->

# まずは1枚、<br>グラフを減らしてみませんか？
