#!/usr/bin/env python3
"""各ページの中身が下端・右端にどれだけ迫っているかを画像から測る。

使い方: python3 tools/check-margins.py <deck.pdf> [--bottom 60] [--right 60]
仕組み: 各ページを 1280x720 相当に焼き、ページの地の色（左上隅から取る）と違うピクセルの最下行・最右列を取る。
       地の色はページごとに取るので、明るい地（laiken-light）でも中扉の淡い地でも、黒地でも同じように測れる。
       右下のページ番号（幅 140px・高さ 48px の隅）は除外する。全面画像のスライド（bg cover）と、
       下端まで面を敷いたスライドは対象外。
       必要なもの: pdftoppm（poppler）、Pillow
"""
import sys, subprocess, tempfile, os, glob
from PIL import Image

if len(sys.argv) < 2 or sys.argv[1].startswith('--'):
    print(__doc__); sys.exit(2)
pdf = sys.argv[1]
def opt(name, default):
    return int(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default
MIN_B, MIN_R = opt('--bottom', 60), opt('--right', 60)
TOL = 18  # 地の色からの距離（RGB 各成分の最大差）がこれ以上なら「中身」

tmp = tempfile.mkdtemp()
subprocess.run(['pdftoppm', '-png', '-r', '96', pdf, os.path.join(tmp, 'p')], check=True, stderr=subprocess.DEVNULL)
ng = 0; n = 0
for f in sorted(glob.glob(os.path.join(tmp, 'p-*.png'))):
    n += 1
    im = Image.open(f).convert('RGB'); W, H = im.size
    sx = 1280 / W
    px = im.load()
    bg = px[4, 4]
    ink = lambda c, bg=bg: max(abs(c[0] - bg[0]), abs(c[1] - bg[1]), abs(c[2] - bg[2])) >= TOL
    # 表紙のグラデーションのように、地の色が一様でないページは対象外
    if ink(px[W - 5, H - 5]):
        continue
    # 全面画像（地の色でないピクセルが半分以上）は対象外
    lit = sum(1 for y in range(0, H, 6) for x in range(0, W, 6) if ink(px[x, y]))
    if lit > (W // 6) * (H // 6) * 0.5:
        continue
    maxy = -1; maxx = -1
    for y in range(H):
        for x in range(W):
            if ink(px[x, y]):
                if x > W - 140 / sx and y > H - 48 / sx:  # ページ番号の隅
                    continue
                if y > maxy: maxy = y
                if x > maxx: maxx = x
    if maxy < 0: continue
    # 最下行がほぼ全幅で塗られているスライドは、意図した全面の面なので対象外
    if maxy == H - 1 and sum(1 for x in range(0, W, 4) if ink(px[x, H - 1])) > (W // 4) * 0.9:
        continue
    bottom = round((H - 1 - maxy) * sx); right = round((W - 1 - maxx) * sx)
    flags = []
    if bottom < MIN_B: flags.append(f'下端の空き {bottom}px（最低 {MIN_B}）')
    if right < MIN_R: flags.append(f'右端の空き {right}px（最低 {MIN_R}）')
    if flags:
        ng += 1; print(f'NG p{n} ' + ' / '.join(flags))
print(f'{n} ページ走査、NG {ng} 件')
sys.exit(1 if ng else 0)
