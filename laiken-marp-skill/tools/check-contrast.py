#!/usr/bin/env python3
"""テーマの配色が、役割ごとのコントラスト比の下限を満たしているかを確かめる。

使い方: python3 tools/check-contrast.py [theme/laiken-light.css]
仕組み: テーマの :root に並ぶ色の変数（--bg など）を読み、下の RULES の組み合わせで比を計算する。
       配色を差し替えたときに、読めない組み合わせを入れないための検査。PDF は作らない。
"""
import re, sys

# (文字や図形の色, その下の面の色, 下限, 用途)
RULES = [
    ('ink', 'bg', 7.0, '本文'),
    ('ink', 'soft', 7.0, '中扉の見出し'),
    ('ink', 'surface', 7.0, '表・コードの文字'),
    ('ink2', 'bg', 4.5, '入れ子の箇条書き、表紙の名前'),
    ('sub', 'bg', 4.5, '補足の文字'),
    ('accent', 'bg', 4.5, '強調の文字'),
    ('accent-ink', 'bg', 4.5, 'リンク、コードのキーワード'),
    ('accent2', 'bg', 4.5, 'h2、キャプション'),
    ('accent2', 'soft', 4.5, '表のヘッダ'),
    ('code-str', 'surface', 4.5, 'コードの文字列'),
    ('surface', 'accent', 4.5, 'アクセントの面に乗せる白文字'),
    ('on-accent-sub', 'accent', 4.5, 'アクセントの面に乗せる補足文字'),
    ('rule', 'bg', 2.5, '見出しの下線・箇条書きの点（文字には使わない）'),
    ('arrow', 'bg', 2.0, '矢印（文字には使わない）'),
]


def lum(h):
    h = h.lstrip('#')
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(int(h[i:i + 2], 16)) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a, b):
    x, y = sorted([lum(a), lum(b)])
    return (y + 0.05) / (x + 0.05)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'theme/laiken-light.css'
    css = open(path, encoding='utf-8').read()
    root = re.search(r':root\s*\{(.*?)\}', css, re.S).group(1)
    v = dict(re.findall(r'--([\w-]+):\s*(#[0-9a-fA-F]{6})', root))
    ng = 0
    for fg, bg, need, use in RULES:
        if fg not in v or bg not in v:
            ng += 1
            print(f'NG 変数がない: --{fg} / --{bg}（{use}）')
            continue
        r = ratio(v[fg], v[bg])
        mark = 'OK' if r >= need else 'NG'
        if r < need:
            ng += 1
        print(f'{mark} {r:5.2f}（下限 {need:g}） --{fg} {v[fg]} / --{bg} {v[bg]}  {use}')
    print(f'{len(RULES)} 組を検査、NG {ng} 件')
    sys.exit(1 if ng else 0)


if __name__ == '__main__':
    main()
