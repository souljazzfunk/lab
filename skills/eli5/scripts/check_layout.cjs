#!/usr/bin/env node
// Layout checker for eli5 pages.
// Usage: NODE_PATH="$(npm root -g)" node check_layout.cjs page.html
// Renders the page in every language mode (ja / en / both) at desktop and
// phone widths and prints each layout problem found. Exit code 1 if any.
const path = require('path');
const { chromium } = require('playwright');

const file = process.argv[2];
if (!file) { console.error('usage: check_layout.cjs page.html'); process.exit(2); }
const url = 'file://' + path.resolve(file);
const MODES = ['both', 'ja', 'en'];
const WIDTHS = [1024, 400];

function audit() {
  const out = [];
  const vw = document.documentElement.clientWidth;
  const name = (el) => {
    const t = (el.textContent || '').trim().replace(/\s+/g, ' ');
    return `<${el.tagName.toLowerCase()}> "${t.slice(0, 40)}${t.length > 40 ? '…' : ''}"`;
  };
  const visible = (el) => {
    const s = getComputedStyle(el);
    return s.display !== 'none' && s.visibility !== 'hidden' && el.getClientRects().length > 0;
  };
  const hit = (a, b, pad = 1) => a.left < b.right - pad && b.left < a.right - pad && a.top < b.bottom - pad && b.top < a.bottom - pad;

  // 1. Page scrolls sideways.
  if (document.documentElement.scrollWidth > vw + 1)
    out.push(`page scrolls horizontally (${document.documentElement.scrollWidth}px > ${vw}px)`);

  // 2. HTML text overflowing its box or the viewport.
  for (const el of document.body.querySelectorAll('*')) {
    if (el.closest('svg') || !visible(el)) continue;
    const s = getComputedStyle(el);
    const scrolls = /(auto|scroll)/.test(s.overflowX);
    if (!scrolls && el.scrollWidth > el.clientWidth + 1 && el.clientWidth > 0 && s.display !== 'inline')
      out.push(`text overflows its box: ${name(el)} (${el.scrollWidth}px in ${el.clientWidth}px)`);
    const r = el.getBoundingClientRect();
    if ([...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()) && (r.right > vw + 1 || r.left < -1))
      out.push(`text off screen: ${name(el)}`);
  }

  // 3. Caption over-wrapping: too many lines, or a stranded last line.
  for (const sp of document.querySelectorAll('span[lang]')) {
    if (sp.closest('svg') || !visible(sp)) continue;
    const range = document.createRange();
    range.selectNodeContents(sp);
    const rects = [...range.getClientRects()].filter(r => r.width > 0);
    const lines = [...new Set(rects.map(r => Math.round(r.bottom)))].length;
    const block = sp.parentElement.closest('figcaption,figure,.caption,.label,li,td,th,button,h1,h2,h3,p,div');
    const width = block ? block.clientWidth : vw;
    const len = sp.textContent.trim().length;
    const inFigure = sp.closest('figure,figcaption,.caption,.label,.card,button,h1,h2,h3');
    if (inFigure && lines > 2)
      out.push(`caption wraps to ${lines} lines (${sp.lang}): ${name(sp)} in ${width}px`);
    if (lines >= 2 && rects.length) {
      const lastBottom = Math.max(...rects.map(r => Math.round(r.bottom)));
      const last = rects.filter(r => Math.round(r.bottom) === lastBottom)
        .reduce((a, r) => ({ width: a.width + r.width }), { width: 0 });
      if (last.width < Math.min(40, width * 0.12) && len > 4)
        out.push(`stranded last line (${sp.lang}): ${name(sp)}`);
    }
  }

  // 4. SVG labels: outside the drawing, off screen, or colliding.
  for (const svg of document.querySelectorAll('svg')) {
    if (!visible(svg) || svg.closest('button,.toggle,[role=toolbar]')) continue;
    const box = svg.getBoundingClientRect();
    const texts = [...svg.querySelectorAll('text')].filter(visible);
    const rects = texts.map(t => t.getBoundingClientRect());
    texts.forEach((t, i) => {
      const r = rects[i];
      if (r.left < box.left - 1 || r.right > box.right + 1 || r.top < box.top - 1 || r.bottom > box.bottom + 1)
        out.push(`SVG label leaves its figure: ${name(t)}`);
      if (r.left < -1 || r.right > vw + 1)
        out.push(`SVG label off screen: ${name(t)}`);
      for (let j = i + 1; j < texts.length; j++)
        if (hit(r, rects[j], 2)) out.push(`SVG labels overlap: ${name(t)} × ${name(texts[j])}`);
      // text wider than the shape it sits on (rect/circle/ellipse behind it)
      for (const sh of svg.querySelectorAll('rect,circle,ellipse')) {
        const b = sh.getBoundingClientRect();
        if (b.width < 20 || b.width >= box.width * 0.9) continue;
        const cx = (r.left + r.right) / 2, cy = (r.top + r.bottom) / 2;
        const centered = cx > b.left && cx < b.right && cy > b.top && cy < b.bottom;
        if (centered && (r.left < b.left - 1 || r.right > b.right + 1 || r.top < b.top - 1 || r.bottom > b.bottom + 1)) {
          out.push(`SVG label spills out of its shape: ${name(t)}`);
          break;
        }
      }
    });
  }

  // 5. Fixed toggle bar covering content at the top of the page.
  for (const el of document.querySelectorAll('*')) {
    if (getComputedStyle(el).position !== 'fixed' || !visible(el)) continue;
    const f = el.getBoundingClientRect();
    for (const o of document.body.querySelectorAll('h1,h2,p,figure,svg,li')) {
      if (el.contains(o) || o.contains(el) || !visible(o)) continue;
      if (hit(f, o.getBoundingClientRect(), 2)) { out.push(`fixed toggle covers ${name(o)}`); break; }
    }
  }
  return [...new Set(out)];
}

(async () => {
  const browser = await chromium.launch();
  let total = 0;
  for (const width of WIDTHS) {
    const page = await browser.newPage({ viewport: { width, height: 900 } });
    await page.goto(url);
    await page.evaluate(() => document.fonts && document.fonts.ready);
    for (const mode of MODES) {
      await page.evaluate((m) => {
        if (typeof window.setLang === 'function') window.setLang(m);
        else document.documentElement.dataset.lang = m;
        window.scrollTo(0, 0);
      }, mode);
      await page.waitForTimeout(100);
      const issues = await page.evaluate(audit);
      for (const i of issues) console.log(`[${width}px ${mode}] ${i}`);
      total += issues.length;
    }
    await page.close();
  }
  await browser.close();
  console.log(total ? `\n${total} layout issue(s) found.` : 'No layout issues found.');
  process.exit(total ? 1 : 0);
})();
