---
marp: true
paginate: true
theme: laiken-light
---

<style>
img { display:block; margin:0 auto; }
</style>

<!-- _class: top -->
<!-- _paginate: false -->

# AIに作らせたスライド、<br>なぜか薄くなる問題

<br><br>

サンプルデッキ

---

<!-- _class: crosshead -->

# AIにスライドを作らせたこと、<br>ありますか？

---

<!-- _class: crosshead -->

# そのまま登壇に使えましたか？

---

# こうなりがち

- 全ページが「見出し＋カード3枚」の同じ形
- 見出しが全部、同じ長さの体言止め
- 図の文字が小さくて、後ろの席から読めない

体裁は整っているのに、話が頭に残りません

---

<!-- _class: crosshead -->

# じゃあ、どこを直せばいいの？

---

# 直すのは3か所だけ

図のすぐ上に本文を置きます
![w:1000](./images/flow-bad.svg)

---

# 話の順番は、聞き手の疑問の順番

- 概念の定義から始めない
- 中扉には、聞き手の心の声を書く
- 答えは先に出さず、1スライドずつ開く

アジェンダも、まとめも作りません

---

# 見た目は目分量で決めない

| 測るもの | 下限 |
| --- | --- |
| 図の中の文字 | 16pt |
| 文字と箱の縁 | 14px |
| 図と本文の間隔 | 36px |
| 中身とスライド下端 | 60px |
| あ | 1 |
| い | 2 |
| う | 3 |
| え | 4 |
| お | 5 |

---

# 書き出したら、検査をまとめて通す

```bash
marp --no-stdin deck.md --pdf --allow-local-files
python3 tools/check-margins.py deck.pdf
python3 tools/check-gaps.py deck.pdf
python3 tools/check-figure-text.py deck.pdf
```

---

# …検査が通れば完成！ではないんです

- 検査が測れるのは、描かれた要素だけ
- 矢印が消えた図は、全部OKで通ってしまう
- 最後は全ページを画像にして、<strong>自分の目で見る</strong>

---

<!-- _class: crosshead -->

# まずは手元の1本を、<br>測るところから始めてみませんか？
