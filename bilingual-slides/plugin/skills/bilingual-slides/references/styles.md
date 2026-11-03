# スタイル・配色・ブランドの参照

SKILL.md から外した詳細。ブランド色を入れるとき、スタイルを足すときだけ読む。値の正本は `assets/template.html` の `<style>`（`/* ===== Tokens` から始まるブロック）。

## Standard のトークン

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

## Organic のトークン

| トークン | ライト | ダーク |
|---|---|---|
| `--slide` / `--page` | `#faf8f4` / `#e9e4dc` | `#1a1b18` / `#0f100e` |
| `--ink` / `--ink-2` / `--muted` | `#23221f` / `#4a463f` / `#635e56` | `#ece8e0` / `#cfc9be` / `#a39d92` |
| `--accent` / `--accent-fill` | `#4d6b4f`（セージ） | `#a8c3a2` / `#3d5440` |
| `--soft` / `--accent-soft` | `#efebe4` / `#e6ece2` | `#24261f` / `#263024` |
| `--s2` / `--s3` | `#a0502f`（テラコッタ）/ `#86651a`（オーカー） | `#e3a283` / `#d8b864` |

Organic では、カードの地がアクセントの淡い面になり、結論文の上に短い丸い棒、表紙と中扉に円の飾りが入る。飾りはスライドの端で切れてよい（検査は飾りを数えない）。自分で飾りを足すときは擬似要素か `class="deco"` の要素にする。

## ブランド色を入れる

会社や製品のデッキは、ブランド色を `--accent` と `--accent-fill` に入れる。ライトとダークの両方の値を決める。

テンプレート本体は書き換えない。スライド断片の先頭に `<style>` を 1 つ置き、使っているスタイルの 3 か所すべてを上書きする（`build_deck.cjs` はこの `<style>` もそのまま入れる）:

```html
<style>
:root[data-style="standard"] { --accent: #c2410c; --accent-fill: #9a3412; }
:root[data-style="standard"][data-theme="dark"] { --accent: #fdba74; --accent-fill: #9a3412; }
@media (prefers-color-scheme: dark) {
  :root[data-style="standard"]:not([data-theme="light"]) { --accent: #fdba74; --accent-fill: #9a3412; }
}
</style>
```

差し替えたら、検査で `low-contrast` が出ないことを確かめる（小さい文字は 4.5、40px 以上か 32px 以上の太字は 3）。

## スタイルを足す（テンプレートの開発）

1. `template.html` の Organic のブロックを写して、`:root[data-style="<名前>"]`（ライト）、`:root[data-style="<名前>"][data-theme="dark"]`、`@media (prefers-color-scheme: dark)` の `:root[data-style="<名前>"]:not([data-theme="light"])` の 3 か所にトークンを書く
2. 書体は `--font-body` と `--font-head` で持つ。サンセリフだけにし、ラテン書体を先、和文書体を次に並べる。`<head>` に `<!-- style: <名前> -->` の行と Google Fonts の `<link>` を 1 行ずつ足す（`build_deck.cjs` はこの印で選ぶ）
3. 形は `--radius`、`--marker-radius`、`--rule`、`--head-track` で変える
4. `check_slides.cjs assets/template.html --style <名前>` を通し、SKILL.md のスタイルの表とこのファイルに 1 行足す
