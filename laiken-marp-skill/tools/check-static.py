#!/usr/bin/env python3
"""スキルに書いた決まりのうち、ファイルを読むだけで確かめられるものを検査する（PDF は作らない）。

使い方: python3 tools/check-static.py <デッキのディレクトリ...> [--theme theme/laiken-light.css] [--skills skills]

デッキのディレクトリ（deck.md と images/*.svg）ごとに:
  - 文字サイズ: SVG は 32px 未満、CSS は 24pt / 32px 未満を NG（ページ番号・header・footer は例外）
  - 矢印: SVG の <marker> は NG（line と polygon で描く決まり）
  - 配色: テーマの :root にない色（#ffffff は可）を NG。わざと多色にする図は
          ルートの <svg> に data-palette="free" を付けて除外する
  - 見出しの語尾: 「てる」「ばいい」「んです」で終わる h1 を NG。
          ただし「…」で始まるどんでん返しの見出し（「…人生そんなに簡単じゃないんです」）は可
--skills を付けると、各スキルの冒頭に name と description があり、name がフォルダ名と一致するかも見る。
"""
import glob, os, re, sys

MIN_SVG_PX = 32
MIN_PT, MIN_PX = 24, 32
EXEMPT_SELECTOR = re.compile(r'::after|\bheader\b|\bfooter\b')
HEX = re.compile(r'#[0-9a-fA-F]{6}\b')
BAD_END = re.compile(r'(てる|ばいい|んです)$')


def palette(theme):
    css = open(theme, encoding='utf-8').read()
    root = re.search(r':root\s*\{(.*?)\}', css, re.S).group(1)
    return {c.lower() for c in HEX.findall(root)} | {'#ffffff'}


def css_font_ng(css):
    out = []
    for sel, body in re.findall(r'([^{}]+)\{([^{}]*)\}', css):
        if EXEMPT_SELECTOR.search(sel):
            continue
        for val, unit in re.findall(r'font-size\s*:\s*([\d.]+)(pt|px)', body):
            v = float(val)
            if (unit == 'pt' and v < MIN_PT) or (unit == 'px' and v < MIN_PX):
                out.append(f'{sel.strip()[:40]} の font-size {val}{unit}')
    return out


def check_deck(d, pal):
    ng = []
    md = os.path.join(d, 'deck.md')
    if os.path.exists(md):
        text = open(md, encoding='utf-8').read()
        for css in re.findall(r'<style[^>]*>(.*?)</style>', text, re.S):
            ng += [f'{md}: {m}（下限 {MIN_PT}pt / {MIN_PX}px）' for m in css_font_ng(css)]
        body = re.sub(r'<!--.*?-->', '', text, flags=re.S)
        ng += [f'{md}: テーマにない色 {c}' for c in sorted({c.lower() for c in HEX.findall(body)} - pal)]
        for line in text.splitlines():
            if line.startswith('# '):
                h = re.sub(r'<br>', '', line[2:]).strip()
                if BAD_END.search(h) and not h.startswith('…'):
                    ng.append(f'{md}: 見出しの語尾「{h}」')
    for svg in sorted(glob.glob(os.path.join(d, 'images', '*.svg'))):
        s = open(svg, encoding='utf-8').read()
        for v in re.findall(r'font-size\s*[=:]\s*"?([\d.]+)', s):
            if float(v) < MIN_SVG_PX:
                ng.append(f'{svg}: font-size {v}（下限 {MIN_SVG_PX}px）')
        if '<marker' in s:
            ng.append(f'{svg}: <marker> を使っている（line と polygon で描く）')
        if 'data-palette="free"' not in s:
            ng += [f'{svg}: テーマにない色 {c}' for c in sorted({c.lower() for c in HEX.findall(s)} - pal)]
    return ng


def check_skills(root):
    ng = []
    for f in sorted(glob.glob(os.path.join(root, '*', 'SKILL.md'))):
        text = open(f, encoding='utf-8').read()
        m = re.match(r'---\n(.*?)\n---\n', text, re.S)
        if not m:
            ng.append(f'{f}: 冒頭の --- で囲んだ設定がない'); continue
        meta = dict(re.findall(r'^(\w+):\s*(.+)$', m.group(1), re.M))
        folder = os.path.basename(os.path.dirname(f))
        if meta.get('name') != folder:
            ng.append(f'{f}: name「{meta.get("name")}」がフォルダ名「{folder}」と違う')
        if not meta.get('description'):
            ng.append(f'{f}: description がない')
    return ng


def main():
    args = sys.argv[1:]
    def take(flag, default=None):
        if flag in args:
            i = args.index(flag); v = args[i + 1]; del args[i:i + 2]; return v
        return default
    theme = take('--theme', 'theme/laiken-light.css')
    skills = take('--skills')
    if not args and not skills:
        print(__doc__); sys.exit(2)
    pal = palette(theme)
    ng = css_font_ng(open(theme, encoding='utf-8').read())
    ng = [f'{theme}: {m}' for m in ng]
    for d in args:
        ng += check_deck(d, pal)
    if skills:
        ng += check_skills(skills)
    for m in ng:
        print('NG', m)
    print(f'{len(args)} デッキ{"＋スキル" if skills else ""}を検査、NG {len(ng)} 件')
    sys.exit(1 if ng else 0)


if __name__ == '__main__':
    main()
