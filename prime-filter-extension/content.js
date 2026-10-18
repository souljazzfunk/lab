(() => {
  const CARD = 'article[data-testid="card"]';
  const BENEFIT_RE = /benefit-id\/[^/]+\/([^/]+)\/logos\//;
  let primeOnly = false;
  let bar, toggleBtn, csvBtn, countEl;

  const isWatchlist = () => location.pathname.includes('/mystuff/watchlist');

  const parseCard = card => {
    const a = card.querySelector('a[href*="/detail/"]');
    const benefit = card.innerHTML.match(BENEFIT_RE)?.[1] ?? '';
    const entitlement = card.dataset.cardEntitlement ?? '';
    return {
      title: card.dataset.cardTitle ?? '',
      type: card.dataset.cardEntityType ?? '',
      entitlement,
      benefit,
      prime: entitlement === 'Entitled' && benefit === 'Prime',
      asin: a?.href.match(/\/detail\/([A-Z0-9]{10})/)?.[1] ?? '',
      url: a ? a.href.split('?')[0] : '',
    };
  };

  // グリッドの隙間を残さないよう、カードだけを包むラッパーごと隠す
  const hideTarget = card => {
    let el = card;
    while (el.parentElement && el.parentElement.children.length === 1 && el.parentElement !== document.body) {
      el = el.parentElement;
    }
    return el;
  };

  const apply = () => {
    if (!bar) return;
    const cards = document.querySelectorAll(CARD);
    let prime = 0;
    for (const card of cards) {
      const isPrime = parseCard(card).prime;
      if (isPrime) prime++;
      hideTarget(card).classList.toggle('pwf-hidden', primeOnly && !isPrime);
    }
    const text = `${prime} / ${cards.length}`;
    // 自分の書き換えで MutationObserver が無限に回らないよう、変化時のみ更新
    if (countEl.textContent !== text) countEl.textContent = text;
  };

  const loadAll = async () => {
    const sleep = ms => new Promise(r => setTimeout(r, ms));
    const y = window.scrollY;
    let prev = -1, stable = 0;
    while (stable < 3) {
      window.scrollTo(0, document.body.scrollHeight);
      await sleep(1500);
      const n = document.querySelectorAll(CARD).length;
      stable = n === prev ? stable + 1 : 0;
      prev = n;
    }
    window.scrollTo(0, y);
  };

  const exportCsv = async () => {
    csvBtn.disabled = true;
    csvBtn.textContent = '読み込み中…';
    try {
      await loadAll();
      const rows = new Map();
      for (const card of document.querySelectorAll(CARD)) {
        const r = parseCard(card);
        rows.set(r.asin || r.title, r);
      }
      const list = [...rows.values()].filter(r => !primeOnly || r.prime);
      if (!list.length) return;
      const cols = Object.keys(list[0]);
      const esc = v => `"${String(v).replace(/"/g, '""')}"`;
      const csv = '﻿' + [cols.join(','), ...list.map(r => cols.map(c => esc(r[c])).join(','))].join('\n');
      const date = new Date().toLocaleDateString('sv-SE', { timeZone: 'Asia/Tokyo' });
      const link = Object.assign(document.createElement('a'), {
        href: URL.createObjectURL(new Blob([csv], { type: 'text/csv' })),
        download: `watchlist${primeOnly ? '_prime' : ''}_${date}.csv`,
      });
      link.click();
      URL.revokeObjectURL(link.href);
    } finally {
      csvBtn.disabled = false;
      csvBtn.textContent = 'CSV';
    }
  };

  const setPrimeOnly = value => {
    primeOnly = value;
    toggleBtn.setAttribute('aria-pressed', String(value));
    chrome.storage.local.set({ primeOnly: value });
    apply();
  };

  const mount = () => {
    bar = document.createElement('div');
    bar.id = 'pwf-bar';
    toggleBtn = document.createElement('button');
    toggleBtn.textContent = 'プライムのみ';
    toggleBtn.setAttribute('aria-pressed', 'false');
    toggleBtn.addEventListener('click', () => setPrimeOnly(!primeOnly));
    countEl = document.createElement('span');
    countEl.id = 'pwf-count';
    countEl.title = 'プライム見放題 / 読み込み済み';
    csvBtn = document.createElement('button');
    csvBtn.textContent = 'CSV';
    csvBtn.title = '全件読み込んでCSVを書き出す（プライムのみ ON なら絞り込み後）';
    csvBtn.addEventListener('click', exportCsv);
    bar.append(toggleBtn, countEl, csvBtn);
    document.body.append(bar);
    chrome.storage.local.get('primeOnly', ({ primeOnly: saved }) => setPrimeOnly(!!saved));
  };

  const unmount = () => {
    bar?.remove();
    bar = null;
    document.querySelectorAll('.pwf-hidden').forEach(el => el.classList.remove('pwf-hidden'));
  };

  // ページ内遷移と遅延読み込みの両方に追従する
  let scheduled = false;
  const sync = () => {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => {
      scheduled = false;
      if (isWatchlist() && !bar) mount();
      else if (!isWatchlist() && bar) unmount();
      apply();
    });
  };
  new MutationObserver(sync).observe(document.body, { childList: true, subtree: true });
  sync();
})();
