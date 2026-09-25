#!/usr/bin/env python3
"""大きい塊（画像・図・コードの箱・表）と隣の文の縦の間隔を実測する。
pdftoppm -r 96 で 1280x720 に焼き、地の色（ページ左上隅から取る）でない行の連なりを「帯」として拾い、
高さ 130px 以上の帯（画像・図・箱）と隣の帯の間隔が MIN_GAP 未満なら NG。
見出しと本文の間、箇条書き同士の間は対象外（帯の高さと h1 の下線で区別する。laiken-light の本文は1行65px）。
使い方: python3 tools/check-gaps.py <deck>.pdf [--min 36]"""
import subprocess, sys, tempfile, os, glob
from PIL import Image

if len(sys.argv) < 2 or sys.argv[1].startswith('--'):
    print(__doc__); sys.exit(2)
MIN_GAP = 36
BLOCK = 130   # これ以上の高さの帯を「塊」とみなす（2行の本文は 125px 前後）
TOL = 18
args = [a for a in sys.argv[1:] if not a.startswith('--')]
if '--min' in sys.argv: MIN_GAP = int(sys.argv[sys.argv.index('--min') + 1])
pdf = args[0]
tmp = tempfile.mkdtemp()
subprocess.run(['pdftoppm', '-r', '96', '-png', pdf, os.path.join(tmp, 'p')], check=True, stderr=subprocess.DEVNULL)
ng = 0
pages = sorted(glob.glob(os.path.join(tmp, 'p-*.png')))
for i, f in enumerate(pages, 1):
    im = Image.open(f).convert('RGB')
    W, H = im.size
    px = im.load()
    bg = px[4, 4]
    ink = lambda c, bg=bg: max(abs(c[0] - bg[0]), abs(c[1] - bg[1]), abs(c[2] - bg[2])) >= TOL
    # ページ番号の角（右下 140x48）と左右の余白 60px は無視。全面画像のページは対象外
    rows = []
    for y in range(H):
        # 右下の挿絵（.ill）の領域 x>900,y>380 も無視する（本文とは横に並ぶだけで、縦の間隔ではない）
        lit = any(ink(px[x, y]) for x in range(60, W - 60, 2) if not (x > W - 140 and y > H - 48) and not (x > 900 and y > 380))
        rows.append(lit)
    if sum(rows) > H * 0.9:
        continue
    if sum(rows) < 200 and all(not rows[y] for y in list(range(0, 180)) + list(range(560, H - 48))):
        continue  # 中扉（中央に見出しだけ）は対象外
    bands, y = [], 0
    while y < H:
        if rows[y]:
            y0 = y
            while y < H and rows[y]: y += 1
            bands.append((y0, y))
        else:
            y += 1
    # h1 の下線（高さ 8px 以下で横幅いっぱいの帯）。英語の見出しは y や g の下がりが下線に近く、
    # 下の結合で見出しと下線が1つの帯になるので、下線を含む帯は見出しとして隣の帯から外す
    rules = {b for b in bands if b[1] - b[0] <= 8 and all(ink(px[x, b[0]]) for x in range(80, W - 80, 8))}
    # 行間で割れた文字の帯を、12px 以内なら結合（2行の箇条書きの行間と、画像の縁の細い帯を吸収する）
    merged, heading = [], []
    for b in bands:
        if merged and b[0] - merged[-1][1] <= 12:
            merged[-1] = (merged[-1][0], b[1])
            heading[-1] = heading[-1] or b in rules
        else:
            merged.append(b)
            heading.append(False)
    for k, (y0, y1) in enumerate(merged):
        if y1 - y0 < BLOCK:
            continue
        for nb in (merged[k - 1] if k > 0 else None, merged[k + 1] if k + 1 < len(merged) else None):
            if nb is None or nb[1] - nb[0] < 40: continue  # 図のラベル（32px の1行は 40px 未満）や画像の縁は本文ではない
            if heading[merged.index(nb)]: continue
            gap = (y0 - nb[1]) if nb[1] <= y0 else (nb[0] - y1)
            if 0 <= gap < MIN_GAP:
                ng += 1
                print(f'NG p{i} 高さ{y1 - y0}px の塊（y={y0}〜{y1}）と隣の帯の間隔 {gap}px（最低 {MIN_GAP}）')
print(f'{len(pages)} ページ走査、NG {ng} 件')
sys.exit(1 if ng else 0)
