#!/usr/bin/env python3
"""Marp で書き出した HTML に、言語とダークモードの切り替えを足す。

使い方: python3 tools/add-toggles.py deck.html [...]
  - 右上: EN / JA / Both のトグル。各 section の lang を en / ja / mul に書き換え、
          テーマ（laiken-light）の .en / .ja と alt に en / ja を入れた図の出し分けが切り替わる
  - 左下: ダーク / ライトの小さなボタン。各 section に data-scheme="dark" を付け外しする
最初の表示は、デッキのフロントマターの lang（ja / en / mul）。選んだものはブラウザに覚えさせる。
同じファイルに2回かけても、切り替えは1組だけになる。
"""
import sys

MARK = '<!-- laiken-toggles -->'

SNIPPET = MARK + r'''
<style>
.lk-ui{position:fixed;z-index:100;font:600 14px/1 'Hiragino Sans','Noto Sans JP','Noto Sans CJK JP',sans-serif;
  --lk-bg:rgba(248,246,241,.9);--lk-ink:#241e1c;--lk-line:#dcd1c6;--lk-on:#9e2f28;--lk-on-ink:#ffffff}
html[data-scheme="dark"] .lk-ui{--lk-bg:rgba(29,25,23,.9);--lk-ink:#f1ece6;--lk-line:#4d423c;--lk-on:#f08c80;--lk-on-ink:#1d1917}
.lk-ui button{font:inherit;color:var(--lk-ink);background:none;border:0;cursor:pointer;margin:0}
#lk-lang{top:14px;right:14px;display:flex;padding:3px;gap:2px;border-radius:999px;
  background:var(--lk-bg);border:1px solid var(--lk-line);opacity:.75;transition:opacity .2s}
#lk-lang:hover,#lk-lang:focus-within{opacity:1}
#lk-lang button{padding:7px 12px;border-radius:999px}
#lk-lang button[aria-pressed="true"]{background:var(--lk-on);color:var(--lk-on-ink)}
#lk-scheme{left:10px;bottom:10px;width:28px;height:28px;padding:0;border-radius:50%;
  font-size:16px;opacity:.25;transition:opacity .2s}
#lk-scheme:hover,#lk-scheme:focus-visible{opacity:.9}
@media print{.lk-ui{display:none}}
</style>
<div id="lk-lang" class="lk-ui" role="group" aria-label="Language">
  <button type="button" data-v="en" lang="en">EN</button>
  <button type="button" data-v="ja" lang="ja">JA</button>
  <button type="button" data-v="mul" lang="en">Both</button>
</div>
<button type="button" id="lk-scheme" class="lk-ui" aria-label="Dark / light" title="Dark / light">&#9680;</button>
<script>
(() => {
  const key = 'laiken-toggles:' + location.pathname;
  const load = () => { try { return JSON.parse(localStorage.getItem(key)) || {}; } catch (e) { return {}; } };
  const save = (s) => { try { localStorage.setItem(key, JSON.stringify(s)); } catch (e) {} };
  const sections = () => document.querySelectorAll('section');
  const norm = (l) => /^ja\b/i.test(l) ? 'ja' : /^en\b/i.test(l) ? 'en' : 'mul';
  const first = document.querySelector('section[lang]');
  const state = Object.assign({ lang: norm(first ? first.lang : ''), scheme: 'light' }, load());
  const apply = () => {
    sections().forEach((s) => {
      s.setAttribute('lang', state.lang);
      if (state.scheme === 'dark') s.setAttribute('data-scheme', 'dark');
      else s.removeAttribute('data-scheme');
    });
    document.documentElement.lang = state.lang;
    document.documentElement.dataset.scheme = state.scheme;
    document.querySelectorAll('#lk-lang button').forEach((b) =>
      b.setAttribute('aria-pressed', String(b.dataset.v === state.lang)));
  };
  const on = (el, fn) => el.addEventListener('click', (e) => {
    e.stopPropagation(); fn(e); save(state); apply(); e.currentTarget.blur();
  });
  document.querySelectorAll('#lk-lang button').forEach((b) => on(b, () => { state.lang = b.dataset.v; }));
  on(document.getElementById('lk-scheme'), () => { state.scheme = state.scheme === 'dark' ? 'light' : 'dark'; });
  apply();
})();
</script>
'''


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    for path in sys.argv[1:]:
        html = open(path, encoding='utf-8').read()
        if MARK in html:
            print(f'{path}: 切り替えは入っている')
            continue
        if '</body>' not in html:
            print(f'NG {path}: </body> がない（Marp の HTML ではない？）')
            sys.exit(1)
        i = html.rindex('</body>')
        open(path, 'w', encoding='utf-8').write(html[:i] + SNIPPET + html[i:])
        print(f'{path}: 言語とダークモードの切り替えを足した')


if __name__ == '__main__':
    main()
