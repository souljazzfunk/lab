(() => {
  const { fetchWatchlist } = globalThis.PrimeWatchlist;

  // idle → loading → ready | error。開くたびに Amazon から取り直す
  let state = { kind: 'idle' };
  let bar, panel;

  const isWatchlist = () => location.pathname.includes('/mystuff/watchlist');

  const el = (tag, props = {}, children = []) => {
    const node = Object.assign(document.createElement(tag), props);
    node.append(...children);
    return node;
  };

  const exportCsv = items => {
    const cols = ['title', 'type', 'asin', 'url'];
    const esc = v => `"${String(v).replace(/"/g, '""')}"`;
    const csv = '﻿' + [cols.join(','), ...items.map(r => cols.map(c => esc(r[c])).join(','))].join('\n');
    const date = new Date().toLocaleDateString('sv-SE', { timeZone: 'Asia/Tokyo' });
    const link = el('a', {
      href: URL.createObjectURL(new Blob([csv], { type: 'text/csv' })),
      download: `watchlist_prime_${date}.csv`,
    });
    link.click();
    URL.revokeObjectURL(link.href);
  };

  const renderPanel = () => {
    const header = el('div', { className: 'pwf-header' });
    const body = el('div', { className: 'pwf-body' });

    if (state.kind === 'loading') {
      header.append(el('span', { textContent: 'ウォッチリストを読み込み中…' }));
    } else if (state.kind === 'error') {
      header.append(el('span', { className: 'pwf-error', textContent: state.message }));
    } else if (state.kind === 'ready') {
      const { items, estimatedTotal, complete } = state;
      const prime = items.filter(i => i.prime);
      header.append(el('span', { textContent: `プライム見放題 ${prime.length} 件 / ウォッチリスト ${items.length} 件` }));
      if (!complete) {
        header.append(el('span', {
          className: 'pwf-error',
          textContent: `Amazon の件数 ${estimatedTotal} 件と合わない。取りこぼしの可能性がある`,
        }));
      }
      header.append(el('button', { textContent: 'CSV', onclick: () => exportCsv(prime) }));
      body.append(el('ul', { className: 'pwf-grid' }, prime.map(item =>
        el('li', {}, [el('a', { href: item.url, title: item.title }, [
          el('img', { src: item.image, alt: '', loading: 'lazy' }),
          el('span', { textContent: item.title }),
        ])]),
      )));
    }
    header.append(el('button', { textContent: '閉じる', onclick: close }));
    panel.replaceChildren(header, body);
  };

  const setState = next => {
    state = next;
    if (panel) renderPanel();
  };

  const open = async () => {
    if (!panel) {
      panel = el('div', { id: 'pwf-panel', role: 'dialog' });
      panel.setAttribute('aria-label', 'プライム見放題の一覧');
      document.body.append(panel);
    }
    setState({ kind: 'loading' });
    try {
      setState({ kind: 'ready', ...(await fetchWatchlist()) });
    } catch (e) {
      setState({ kind: 'error', message: e.message });
    }
  };

  const close = () => {
    panel?.remove();
    panel = null;
    state = { kind: 'idle' };
  };

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && panel) close();
  });

  // Prime Video はページ内遷移なので、ウォッチリストにいる間だけボタンを出す
  const syncBar = () => {
    if (isWatchlist() && !bar) {
      bar = el('div', { id: 'pwf-bar' }, [el('button', { textContent: 'プライム見放題だけ見る', onclick: open })]);
      document.body.append(bar);
    } else if (!isWatchlist() && bar) {
      bar.remove();
      bar = null;
      close();
    }
  };
  setInterval(syncBar, 1000);
  syncBar();
})();
