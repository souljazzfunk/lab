// ウォッチリストを Amazon のデータから全件取る。画面のカードは表示位置の近くしか描画されないので使わない。
(() => {
  const WATCHLIST_URL = '/gp/video/mystuff/watchlist';
  const PAGINATE_URL = '/gp/video/api/paginateCollection';

  // Amazon のウォッチリスト画面がスクロール時に送る値をそのまま写した（2026-11-23）。
  // 変わると応答が JSON でなくなり、fetchWatchlist が例外を投げる。
  const PAGE_PARAMS = [
    ['pageType', 'home'],
    ['pageId', 'Watchlist'],
    ['collectionType', 'Container'],
    ['actionScheme', 'default'],
    ['payloadScheme', 'default'],
    ['decorationScheme', 'web-decoration-asin-v4'],
    ['featureScheme', 'web-features-v6'],
    ...[
      'integration', 'CLIENT_DECORATION_ENABLE_DAAPI', 'ENABLE_DRAPER_CONTENT', 'HorizontalPagination',
      'CleanSlate', 'EpgContainerPagination', 'ENABLE_GPCI', 'SupportsImageTextLinkTextInStandardHero',
      'Remaster', 'SupportsChannelWidget', 'PromotionalBannerSupported', 'RemoveFromContinueWatching',
      'SearchChannelBundles', 'LinearStationInAllCarousels', 'SupportChannelItemDecoration',
      'TvodMovieBundles', 'LinearFavoritesSupported', 'RecordingCardSupported',
    ].map(f => ['dynamicFeatures', f]),
    ['widgetScheme', 'web-explore-v49'],
    ['variant', 'desktopOSX'],
    ['myStuffViewType', 'watchlist'],
  ];

  const benefitOf = entity => JSON.stringify(entity.images ?? {}).match(/benefit-id\/[^/]+\/([^/]+)\/logos\//)?.[1] ?? '';

  const isPrime = entity =>
    entity.entitlementCues?.entitlementType === 'Entitled' && benefitOf(entity) === 'Prime';

  const toItem = entity => ({
    asin: entity.titleID,
    title: entity.title ?? entity.displayTitle ?? '',
    type: entity.entityType ?? '',
    prime: isPrime(entity),
    offer: entity.entitlementCues?.focusMessage?.message || entity.entitlementCues?.glanceMessage?.message || '',
    url: entity.link?.url ? new URL(entity.link.url.split('?')[0], location.origin).href : '',
    image: entity.images?.cover?.url ?? '',
  });

  const parseWatchlistPage = html => {
    const doc = new DOMParser().parseFromString(html, 'text/html');
    const script = [...doc.querySelectorAll('script[type="application/json"]')]
      .find(s => s.textContent.startsWith('{"init"'));
    const container = script && JSON.parse(script.textContent)
      .init?.preparations?.body?.content?.baseOutput?.containers?.[0];
    if (!container?.entities) throw new Error('ウォッチリストのデータがページに見つからない');
    return {
      entities: container.entities,
      estimatedTotal: container.estimatedTotal ?? null,
      cursor: container.paginationServiceToken
        ? { targetId: container.paginationTargetId, serviceToken: container.paginationServiceToken, startIndex: container.paginationStartIndex }
        : null,
    };
  };

  const parsePageResponse = json => ({
    entities: json.entities ?? [],
    cursor: json.hasMoreItems && json.pagination
      ? { targetId: json.pagination.targetId, serviceToken: json.pagination.serviceToken, startIndex: json.pagination.startIndex }
      : null,
  });

  const httpGetWatchlist = async () => {
    const res = await fetch(WATCHLIST_URL, { credentials: 'include' });
    if (!res.ok) throw new Error(`ウォッチリストの取得に失敗 (HTTP ${res.status})`);
    return parseWatchlistPage(await res.text());
  };

  const httpGetPage = async cursor => {
    const body = new URLSearchParams(PAGE_PARAMS);
    body.set('paginationTargetId', cursor.targetId);
    body.set('serviceToken', cursor.serviceToken);
    body.set('startIndex', String(cursor.startIndex));
    const res = await fetch(PAGINATE_URL, {
      method: 'POST',
      credentials: 'include',
      headers: { 'content-type': 'application/x-www-form-urlencoded', accept: 'application/json' },
      body,
    });
    const text = await res.text();
    if (!res.ok || !text.trim().startsWith('{')) {
      throw new Error(`続きの取得に失敗 (HTTP ${res.status}, 開始位置 ${cursor.startIndex})。Amazon 側の仕様が変わった可能性がある`);
    }
    return parsePageResponse(JSON.parse(text));
  };

  // 全ページを辿り、ASIN で重複を除いて返す。Amazon の件数見積もりと合わないときは complete=false。
  const fetchWatchlist = async ({ getFirst = httpGetWatchlist, getPage = httpGetPage, maxPages = 100 } = {}) => {
    const first = await getFirst();
    const byAsin = new Map();
    const add = entities => entities.forEach(e => e.titleID && !byAsin.has(e.titleID) && byAsin.set(e.titleID, toItem(e)));
    add(first.entities);
    let cursor = first.cursor;
    for (let n = 0; cursor; n++) {
      if (n >= maxPages) throw new Error(`${maxPages} ページを超えたので打ち切った`);
      const page = await getPage(cursor);
      add(page.entities);
      cursor = page.cursor;
    }
    const items = [...byAsin.values()];
    return {
      items,
      estimatedTotal: first.estimatedTotal,
      complete: first.estimatedTotal == null || items.length === first.estimatedTotal,
    };
  };

  globalThis.PrimeWatchlist = { fetchWatchlist, parseWatchlistPage, parsePageResponse, toItem, isPrime };
})();
