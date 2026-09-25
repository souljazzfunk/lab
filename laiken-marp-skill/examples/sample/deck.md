---
marp: true
paginate: true
theme: laiken-light
---

<style>
/* 図が主役のスライド。見出しとの間に36px以上、下にも余白 */
img[alt~="center"] { display:block; margin:48px auto 0; }
/* 挿絵。右端は本文の左右余白より内側へ。インラインの style 属性は Marp が落とすのでクラスで書く */
.ill { position:absolute; right:96px; bottom:80px; width:240px; }
.ill.sm { width:190px; }
</style>

<!-- _class: top -->
<!-- _paginate: false -->

# AIのスライド、<br>なぜか薄くなる問題

らいけん（X: @thunder_bark）

---

<!-- _class: crosshead -->

# AIにスライドを<br>作らせたこと、ありますか？

---

<!-- _class: crosshead -->

# そのまま人前で使えましたか？

---

# こうなりがち

- 全ページが同じ形
- 見出しが全部同じ長さ
- 図の文字が小さい

きれいなのに、頭に残りません

<img src="./images/irasutoya-complex-slide.png" class="ill">

---

<!-- _class: crosshead -->

# じゃあ、どこを直すの？

---

# 直すのは3か所だけ

![center w:1144](./images/flow.svg)

---

# 聞き手の「なんで？」の順に話す

- 言葉の説明から始めない
- 中扉に心の声を書く
- 答えは1枚ずつ見せる

<img src="./images/irasutoya-seminar.png" class="ill">

---

# 見た目は目分量で決めない

| 測るもの | 下限 |
| --- | --- |
| 文字の大きさ | 24pt |
| 文字と箱の縁 | 14px |
| 図と本文の間 | 36px |
| 中身と下の端 | 60px |

---

# 書き出したら、まとめて測る

```bash
marp deck.md --pdf
python3 tools/check-margins.py deck.pdf
python3 tools/check-gaps.py deck.pdf
python3 tools/check-figure-text.py deck.pdf
```

---

# …測れば完成！ではないんです

- 測れるのは、描けた物だけ
- 消えた矢印は見逃す
- 最後は**自分の目で見る**

<img src="./images/irasutoya-magnifier.png" class="ill sm">

---

<!-- _class: crosshead -->

# まずは手元の1本を<br>測ってみませんか？
