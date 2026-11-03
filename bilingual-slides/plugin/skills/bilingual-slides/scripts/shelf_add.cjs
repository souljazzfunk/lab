#!/usr/bin/env node
// Usage: node shelf_add.cjs shelf.html --title "Name" --url https://claude.ai/artifact/ID [--tag Slides] [--date YYYY-MM-DD]
//
// Adds one entry to the top of this month's list in a saved copy of the
// "Artifact Shelf" page, creating the month section when it is missing, and
// bumps the artifact count and the footer snapshot date. Edits the file in
// place, so the shelf never has to be read into context or rewritten by hand.
// --date defaults to today in JST. Does nothing if the URL is already listed.
const fs = require('fs');

const args = process.argv.slice(2);
const opt = (k) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : null; };
const file = args.find((a, i) => !a.startsWith('--') && !['--title', '--url', '--tag', '--date'].includes(args[i - 1]));
const title = opt('--title'), url = opt('--url'), tag = opt('--tag') || 'Slides';
if (!file || !title || !url) { console.error('Usage: node shelf_add.cjs shelf.html --title "Name" --url URL [--tag Slides] [--date YYYY-MM-DD]'); process.exit(2); }
const date = opt('--date') || new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Tokyo' }).format(new Date());

let html = fs.readFileSync(file, 'utf8');
if (html.includes(`href="${url}"`)) { console.log(`${file}: ${url} is already listed`); process.exit(0); }

const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const ja = /[぀-ヿ㐀-鿿]/.test(title);
const name = ja ? `<span class="ja">${esc(title)}</span>` : esc(title);
const li = `      <li><a href="${esc(url)}"><span class="name">${name}<span class="tag">${esc(tag)}</span></span><span class="meta">${date}</span></a></li>`;

const [y, m] = date.split('-').map(Number);
const month = `${new Date(Date.UTC(y, m - 1, 1)).toLocaleString('en-US', { month: 'long', timeZone: 'UTC' })} ${y}`;
const head = `<h2>${month}</h2>\n    <ol>\n`;
if (html.includes(head)) {
  html = html.replace(head, head + li + '\n');
} else {
  const first = html.indexOf('<section class="month">');
  if (first < 0) { console.error(`${file}: no <section class="month"> found — is this the shelf page?`); process.exit(1); }
  html = html.slice(0, first) + `<section class="month">\n    ${head}${li}\n    </ol>\n  </section>\n\n  ` + html.slice(first);
}
html = html.replace(/(\d+) artifacts,/, (s, n) => `${Number(n) + 1} artifacts,`);
html = html.replace(/Snapshot taken \d{4}-\d{2}-\d{2} \(JST\)/, `Snapshot taken ${date} (JST)`);
fs.writeFileSync(file, html);
console.log(`${file}: added "${title}" under ${month} (${date})`);
