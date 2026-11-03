#!/usr/bin/env node
// Usage: node build_deck.cjs slides.html -o deck.html [--style standard|organic] [--title "Name"]
//
// Wraps a slides-only fragment (the <section class="slide"> elements) in
// assets/template.html: replaces the block between <!-- SLIDES:BEGIN --> and
// <!-- SLIDES:END -->, sets <html data-style> and <title>, and keeps only the
// font <link> for the chosen style. The CSS, nav bar and script stay untouched,
// so the deck never has to be read or written in full.
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
const opt = (k) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : null; };
const src = args.find((a, i) => !a.startsWith('-') && !['-o', '--style', '--title', '--template'].includes(args[i - 1]));
const out = opt('-o');
if (!src || !out) { console.error('Usage: node build_deck.cjs slides.html -o deck.html [--style NAME] [--title "Name"]'); process.exit(2); }

const tplPath = opt('--template') || path.join(__dirname, '..', 'assets', 'template.html');
let html = fs.readFileSync(tplPath, 'utf8');
let slides = fs.readFileSync(src, 'utf8');

// Accept either a bare fragment or a full deck (take its slide block).
const block = /<!-- SLIDES:BEGIN -->[\s\S]*?<!-- SLIDES:END -->/;
const inner = slides.match(/<!-- SLIDES:BEGIN -->\n?([\s\S]*?)\n?<!-- SLIDES:END -->/);
if (inner) slides = inner[1];
if (!/<section[^>]*class="[^"]*\bslide\b/.test(slides)) { console.error(`${src}: no <section class="slide"> found`); process.exit(1); }
html = html.replace(block, () => `<!-- SLIDES:BEGIN -->\n${slides.trim()}\n<!-- SLIDES:END -->`);

const styles = [...html.matchAll(/<!-- style: ([\w-]+) -->/g)].map((m) => m[1]);
const style = opt('--style') || 'standard';
if (!styles.includes(style)) { console.error(`unknown style "${style}" (have: ${styles.join(', ')})`); process.exit(1); }
html = html.replace(/(<html[^>]*data-style=")[^"]*(")/, `$1${style}$2`);
html = html.replace(/<!-- Fonts: keep only[^\n]*\n/, '');
html = html.replace(/<!-- style: ([\w-]+) -->\n(<link[^\n]*>)\n/g, (m, s, link) => (s === style ? link + '\n' : ''));

const title = opt('--title');
if (title) html = html.replace(/<title>[^<]*<\/title>/, `<title>${title.replace(/[<&]/g, (c) => (c === '<' ? '&lt;' : '&amp;'))}</title>`);

fs.writeFileSync(out, html);
const n = (slides.match(/<section[^>]*class="[^"]*\bslide\b/g) || []).length;
console.log(`${out}: ${n} slides, style ${style}${title ? `, title "${title}"` : ''}`);
