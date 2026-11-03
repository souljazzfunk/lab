#!/usr/bin/env node
// Usage: NODE_PATH="$(npm root -g)" node check_slides.cjs deck.html [--shots DIR]
//
// Renders every slide of a bilingual-slides deck in JA / EN / Both and in
// light / dark on the 1280×720 stage, then reports layout issues:
//   slide-overflow, text-outside-slide, text-overflow-box, text-overlap,
//   line-count (title / bullet / caption wraps too much), stranded-last-line,
//   font-too-small (< 22 stage px), low-contrast, svg-label-* (from eli5),
//   page-hscroll / stage-not-fit at phone and laptop widths.
// Exits 1 when anything is found. --shots DIR saves one PNG per slide/mode/theme.
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const MODES = ['ja', 'en', 'both'];
const THEMES = ['light', 'dark'];
const MIN_FONT = 22;
const SAFE = 40; // text must stay this far inside the slide edge (stage px)

async function audit(opts) {
  const { MIN_FONT, SAFE, checkLayout } = opts;
  const out = [];
  const q = (s) => JSON.stringify((s || '').replace(/\s+/g, ' ').trim().slice(0, 48));
  const slide = document.querySelector('.slide.active');
  if (!slide) return ['no-active-slide'];
  const sr = slide.getBoundingClientRect();
  const visible = (el) => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  const hit = (a, b, pad = 0) =>
    a.left < b.right - pad && b.left < a.right - pad && a.top < b.bottom - pad && b.top < a.bottom - pad;
  const ownText = (el) => [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
  const textBox = (el) => {
    // union of the element's own text-node line boxes (ignores padding/empty space)
    const rs = [];
    for (const n of el.childNodes) {
      if (n.nodeType !== 3 || !n.textContent.trim()) continue;
      const rg = document.createRange(); rg.selectNodeContents(n);
      for (const r of rg.getClientRects()) if (r.width > 0) rs.push(r);
    }
    if (!rs.length) return null;
    return {
      left: Math.min(...rs.map((r) => r.left)), right: Math.max(...rs.map((r) => r.right)),
      top: Math.min(...rs.map((r) => r.top)), bottom: Math.max(...rs.map((r) => r.bottom)),
    };
  };

  // ---------- colour helpers ----------
  const parse = (c) => {
    if (!c) return null;
    let m = c.match(/rgba?\(([^)]+)\)/);
    if (m) {
      const p = m[1].split(/[\s,\/]+/).filter(Boolean).map(parseFloat);
      return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
    }
    m = c.match(/color\(srgb\s+([^)]+)\)/);
    if (m) {
      const p = m[1].split(/[\s\/]+/).filter(Boolean).map(parseFloat);
      return { r: p[0] * 255, g: p[1] * 255, b: p[2] * 255, a: p.length > 3 ? p[3] : 1 };
    }
    return null;
  };
  const over = (top, bottom) => ({
    r: top.r * top.a + bottom.r * (1 - top.a), g: top.g * top.a + bottom.g * (1 - top.a),
    b: top.b * top.a + bottom.b * (1 - top.a), a: 1,
  });
  const lum = (c) => {
    const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
    return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b);
  };
  const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
  const bgOf = (el) => {
    const stack = [];
    for (let e = el; e && e !== document.documentElement; e = e.parentElement) {
      const c = parse(getComputedStyle(e).backgroundColor);
      if (c && c.a > 0) { stack.push(c); if (c.a >= 1) break; }
    }
    let base = { r: 255, g: 255, b: 255, a: 1 };
    for (let i = stack.length - 1; i >= 0; i--) base = over(stack[i], base);
    return base;
  };
  const opacityOf = (el) => {
    let o = 1;
    for (let e = el; e && e !== document.documentElement; e = e.parentElement) o *= parseFloat(getComputedStyle(e).opacity);
    return o;
  };
  const need = (px, weight) => (px >= 40 || (px >= 32 && weight >= 700) ? 3 : 4.5);

  // ---------- HTML text ----------
  const textEls = [...slide.querySelectorAll('*')].filter(
    (el) => !(el instanceof SVGElement) && ownText(el) && visible(el));

  if (checkLayout) {
    if (slide.scrollHeight > slide.clientHeight + 1 || slide.scrollWidth > slide.clientWidth + 1)
      out.push(`slide-overflow: content is ${slide.scrollWidth}×${slide.scrollHeight}, slide ${slide.clientWidth}×${slide.clientHeight}`);
    const body = slide.querySelector('.body');
    if (body && (body.scrollHeight > body.clientHeight + 1)) out.push(`body-overflow: .body needs ${body.scrollHeight}px, has ${body.clientHeight}px`);
  }

  const boxes = [];
  for (const el of textEls) {
    const cs = getComputedStyle(el);
    const fsz = parseFloat(cs.fontSize);
    if (checkLayout) {
      if (fsz < MIN_FONT - 0.1) out.push(`font-too-small (${fsz.toFixed(1)}px): ${q(el.textContent)}`);
      const tb = textBox(el);
      if (tb) {
        if (tb.left < sr.left + SAFE - 1 || tb.right > sr.right - SAFE + 1 || tb.top < sr.top + SAFE / 2 - 1 || tb.bottom > sr.bottom - SAFE / 2 + 1)
          out.push(`text-outside-slide: ${q(el.textContent)}`);
        boxes.push({ el, r: tb });
      }
      if (cs.display !== 'inline' && cs.overflow !== 'visible' && el.scrollWidth > el.clientWidth + 1)
        out.push(`text-overflow-box: ${q(el.textContent)}`);
      if (cs.display !== 'inline' && el.scrollWidth > el.clientWidth + 2 && cs.whiteSpace === 'nowrap')
        out.push(`text-overflow-box: ${q(el.textContent)}`);
    }
    // contrast
    const fg = parse(cs.color);
    if (fg) {
      const bg = bgOf(el);
      const o = opacityOf(el) * fg.a;
      const eff = over({ ...fg, a: o }, bg);
      const r = ratio(eff, bg);
      const req = need(fsz, parseInt(cs.fontWeight, 10));
      if (r < req) out.push(`low-contrast ${r.toFixed(2)} < ${req}: ${q(el.textContent)}`);
    }
  }
  if (checkLayout) {
    for (let i = 0; i < boxes.length; i++)
      for (let j = i + 1; j < boxes.length; j++) {
        const a = boxes[i], b = boxes[j];
        if (a.el.contains(b.el) || b.el.contains(a.el)) continue;
        // line boxes include the font's ascent/descent, so allow a small font-relative slack
        const pad = 0.18 * Math.min(parseFloat(getComputedStyle(a.el).fontSize), parseFloat(getComputedStyle(b.el).fontSize));
        if (hit(a.r, b.r, pad)) out.push(`text-overlap: ${q(a.el.textContent)} × ${q(b.el.textContent)}`);
      }
  }

  // ---------- line counts ----------
  const lines = (el) => {
    const range = document.createRange(); range.selectNodeContents(el);
    const fsz = parseFloat(getComputedStyle(el).fontSize);
    const ls = [];
    for (const r of range.getClientRects()) {
      if (r.width < 1) continue;
      const mid = (r.top + r.bottom) / 2;
      let l = ls.find((x) => Math.abs(x.mid - mid) < fsz * 0.6);
      if (!l) ls.push((l = { mid, left: r.left, right: r.right }));
      l.left = Math.min(l.left, r.left); l.right = Math.max(l.right, r.right);
    }
    ls.sort((a, b) => a.mid - b.mid);
    return { ls, fsz };
  };
  const RULES = [
    ['h1, .title', 2, 'title'],
    ['.statement', 3, 'statement'],
    ['.points li, .agenda li, .card h3, .kpi .l, .kicker, .foot', 2, 'item'],
    ['.lead, .sub, .card p, .card li, .cap, figcaption, .tbl th, .tbl td', 2, 'caption'],
  ];
  if (checkLayout) {
    for (const [sel, max, kind] of RULES) {
      for (const el of slide.querySelectorAll(sel)) {
        if (!visible(el)) continue;
        const parts = [...el.querySelectorAll('[lang]')].filter((c) => !c.querySelector('[lang]') && visible(c));
        const kick = el.matches('.kicker, .foot');
        for (const p of (parts.length && !kick ? parts : [el])) {
          const { ls, fsz } = lines(p);
          if (ls.length > max) out.push(`line-count ${kind} ${ls.length} > ${max}: ${q(p.textContent)}`);
          if (ls.length > 1) {
            const last = ls[ls.length - 1];
            if (last.right - last.left < fsz * 2.2) out.push(`stranded-last-line: ${q(p.textContent)}`);
          }
        }
      }
    }
  }

  // ---------- SVG ----------
  for (const svg of slide.querySelectorAll('svg')) {
    if (!visible(svg)) continue;
    const frame = (svg.closest('figure') || svg).getBoundingClientRect();
    const labels = [...svg.querySelectorAll('text')]
      .filter((t) => visible(t) && t.textContent.trim())
      .map((t) => ({ t, r: t.getBoundingClientRect() }));
    const shapes = [...svg.querySelectorAll('rect, circle, ellipse, polygon, path')]
      .filter((s) => !s.closest('defs, marker') && getComputedStyle(s).fill !== 'none')
      .map((s) => ({ s, r: s.getBoundingClientRect() }));
    const svgBg = bgOf(svg);
    for (const { t, r } of labels) {
      const scale = t.getScreenCTM() ? t.getScreenCTM().a / (parseFloat(getComputedStyle(document.querySelector('.deck')).getPropertyValue('--s')) || 1) : 1;
      for (const sp of [t, ...t.querySelectorAll('tspan')]) {
        if (!visible(sp) || !sp.textContent.trim()) continue;
        const px = parseFloat(getComputedStyle(sp).fontSize) * scale;
        if (checkLayout && px < MIN_FONT - 0.1) out.push(`font-too-small svg (${px.toFixed(1)}px): ${q(sp.textContent)}`);
      }
      if (checkLayout && (r.left < frame.left - 1 || r.right > frame.right + 1 || r.top < frame.top - 1 || r.bottom > frame.bottom + 1))
        out.push(`svg-label-outside-figure: ${q(t.textContent)}`);
      const cx = (r.left + r.right) / 2, cy = (r.top + r.bottom) / 2;
      const behind = shapes
        .filter(({ r: s }) => cx > s.left && cx < s.right && cy > s.top && cy < s.bottom)
        .sort((a, b) => a.r.width * a.r.height - b.r.width * b.r.height)[0];
      if (behind && checkLayout) {
        const s = behind.r, pad = 8;
        if (r.left < s.left + pad || r.right > s.right - pad || r.top < s.top + 2 || r.bottom > s.bottom - 2)
          out.push(`svg-label-spills-shape: ${q(t.textContent)}`);
      }
      const fg = parse(getComputedStyle(t).fill);
      if (fg) {
        let bg = svgBg;
        if (behind) { const f = parse(getComputedStyle(behind.s).fill); if (f) bg = over(f, svgBg); }
        const cr = ratio(over(fg, bg), bg);
        const px = parseFloat(getComputedStyle(t).fontSize) * scale;
        const req = need(px, parseInt(getComputedStyle(t).fontWeight, 10));
        if (cr < req) out.push(`low-contrast svg ${cr.toFixed(2)} < ${req}: ${q(t.textContent)}`);
      }
    }
    if (checkLayout)
      for (let i = 0; i < labels.length; i++)
        for (let j = i + 1; j < labels.length; j++)
          if (hit(labels[i].r, labels[j].r, 1))
            out.push(`svg-label-overlap: ${q(labels[i].t.textContent)} × ${q(labels[j].t.textContent)}`);
  }
  return [...new Set(out)];
}

async function prep(page, mode, theme) {
  await page.evaluate(([m, t]) => {
    if (typeof window.setLang === 'function') window.setLang(m); else document.documentElement.dataset.lang = m;
    if (typeof window.setTheme === 'function') window.setTheme(t); else document.documentElement.dataset.theme = t;
  }, [mode, theme]);
}

(async () => {
  const args = process.argv.slice(2);
  const file = args.find((a) => !a.startsWith('--'));
  const si = args.indexOf('--shots');
  const shots = si >= 0 ? args[si + 1] : null;
  if (!file) { console.error('Usage: node check_slides.cjs deck.html [--shots DIR]'); process.exit(2); }
  if (shots) fs.mkdirSync(shots, { recursive: true });
  const url = 'file://' + path.resolve(file);
  const browser = await chromium.launch();
  let total = 0;
  const report = (tag, list) => { for (const i of list) console.log(`[${tag}] ${i}`); total += list.length; };

  // Stage checks: 1280×720 stage at scale 1 (bar is 48px tall).
  const page = await browser.newPage({ viewport: { width: 1280, height: 768 } });
  page.on('pageerror', (e) => { console.log(`[js] page-error: ${e.message}`); total++; });
  await page.goto(url);
  await page.evaluate(() => document.fonts && document.fonts.ready);
  const count = await page.evaluate(() => (window.deck ? window.deck.count : document.querySelectorAll('.slide').length));
  if (!count) { console.log('no slides found (.slide)'); process.exit(1); }
  for (const theme of THEMES) {
    for (const mode of MODES) {
      await prep(page, mode, theme);
      for (let i = 0; i < count; i++) {
        await page.evaluate((n) => window.deck.go(n), i);
        await page.waitForTimeout(60);
        const issues = await page.evaluate(audit, { MIN_FONT, SAFE, checkLayout: theme === 'light' });
        report(`slide ${i + 1} ${mode} ${theme}`, issues);
        if (shots && (theme === 'light' || mode === 'both')) {
          const el = await page.$('.slide.active');
          await el.screenshot({ path: path.join(shots, `slide-${String(i + 1).padStart(2, '0')}-${mode}-${theme}.png`) });
        }
      }
    }
  }
  await page.close();

  // Frame checks: phone and laptop widths.
  for (const [w, h] of [[400, 800], [1024, 700], [1440, 900]]) {
    const p = await browser.newPage({ viewport: { width: w, height: h } });
    await p.goto(url);
    await p.waitForTimeout(150);
    const issues = await p.evaluate(() => {
      const o = [];
      const sw = document.documentElement.scrollWidth;
      if (sw > innerWidth + 1) o.push(`page-hscroll: page is ${sw}px wide, viewport ${innerWidth}px`);
      const d = document.querySelector('.deck').getBoundingClientRect();
      const v = document.querySelector('.viewport').getBoundingClientRect();
      if (d.left < v.left - 1 || d.right > v.right + 1 || d.top < v.top - 1 || d.bottom > v.bottom + 1)
        o.push('stage-not-fit: slide is cut off by the viewport');
      const bar = document.querySelector('.bar');
      if (bar && bar.scrollWidth > bar.clientWidth + 1) o.push('bar-overflow: control bar is wider than the screen');
      return o;
    });
    report(`frame ${w}px`, issues);
    await p.close();
  }

  await browser.close();
  if (total === 0) console.log(`No layout issues found. (${count} slides × ${MODES.length} languages × ${THEMES.length} themes)`);
  else { console.log(`\n${total} issue(s).`); process.exit(1); }
})();
