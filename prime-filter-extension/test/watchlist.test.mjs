import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

globalThis.location = { origin: 'https://www.amazon.co.jp' };
vm.runInThisContext(readFileSync(new URL('../watchlist.js', import.meta.url), 'utf8'));
const { fetchWatchlist, parsePageResponse, toItem } = globalThis.PrimeWatchlist;

const logo = benefit => `https://example/G/09/digital/video/merch/subs/benefit-id/m-r/${benefit}/logos/x.png`;
const entity = (id, kind) => ({
  titleID: id,
  title: `title ${id}`,
  entityType: 'Movie',
  link: { url: `/gp/video/detail/${id}?ref_=x` },
  images: { cover: { url: kind === 'prime' ? logo('Prime') : kind === 'channel' ? logo('maxjp') : 'https://example/plain.jpg' } },
  entitlementCues: { entitlementType: kind === 'prime' ? 'Entitled' : 'Unentitled', focusMessage: { message: '' } },
});

const pages = (all, size) => {
  const chunks = [];
  for (let i = 0; i < all.length; i += size) chunks.push(all.slice(i, i + size));
  return chunks.map((entities, i) => ({
    entities,
    cursor: i + 1 < chunks.length ? { targetId: 't', serviceToken: `s${i + 1}`, startIndex: (i + 1) * size } : null,
  }));
};

test('follows every page until hasMoreItems is false', async () => {
  const all = Array.from({ length: 133 }, (_, i) => entity(`A${i}`, i % 3 === 0 ? 'prime' : 'rental'));
  const [first, ...rest] = pages(all, 20);
  const seen = [];
  const result = await fetchWatchlist({
    getFirst: async () => ({ ...first, estimatedTotal: 133 }),
    getPage: async cursor => { seen.push(cursor.startIndex); return rest[seen.length - 1]; },
  });
  assert.equal(result.items.length, 133, 'every watchlist item is collected');
  assert.equal(result.complete, true, 'count matches Amazon estimate');
  assert.deepEqual(seen, [20, 40, 60, 80, 100, 120], 'each cursor is requested once, in order');
  assert.equal(result.items.filter(i => i.prime).length, 45, 'prime items are kept regardless of page');
});

test('reports an incomplete fetch instead of hiding it', async () => {
  const result = await fetchWatchlist({
    getFirst: async () => ({ entities: [entity('A1', 'prime')], estimatedTotal: 5, cursor: null }),
    getPage: async () => assert.fail('no further page'),
  });
  assert.equal(result.complete, false, 'mismatch with estimatedTotal is surfaced');
});

test('drops duplicates that appear on two pages', async () => {
  const result = await fetchWatchlist({
    getFirst: async () => ({ entities: [entity('A1', 'prime')], estimatedTotal: 2, cursor: { startIndex: 1 } }),
    getPage: async () => ({ entities: [entity('A1', 'prime'), entity('A2', 'rental')], cursor: null }),
  });
  assert.deepEqual(result.items.map(i => i.asin), ['A1', 'A2']);
  assert.equal(result.complete, true);
});

test('fails loudly when a page request fails', async () => {
  await assert.rejects(fetchWatchlist({
    getFirst: async () => ({ entities: [], estimatedTotal: 40, cursor: { startIndex: 20 } }),
    getPage: async () => { throw new Error('続きの取得に失敗'); },
  }), /続きの取得に失敗/);
});

test('prime means entitled with the Prime benefit, not a channel or rental', () => {
  assert.equal(toItem(entity('P', 'prime')).prime, true);
  assert.equal(toItem(entity('C', 'channel')).prime, false);
  assert.equal(toItem(entity('R', 'rental')).prime, false);
  const subscribedChannel = { ...entity('S', 'channel'), entitlementCues: { entitlementType: 'Entitled' } };
  assert.equal(toItem(subscribedChannel).prime, false, 'a subscribed channel is not Prime');
});

test('item url is absolute and drops the tracking query', () => {
  assert.equal(toItem(entity('B0X', 'prime')).url, 'https://www.amazon.co.jp/gp/video/detail/B0X');
});

test('page response without hasMoreItems ends the walk', () => {
  assert.equal(parsePageResponse({ entities: [], hasMoreItems: false, pagination: { targetId: 't' } }).cursor, null);
  assert.deepEqual(
    parsePageResponse({ entities: [], hasMoreItems: true, pagination: { targetId: 't', serviceToken: 's', startIndex: 60 } }).cursor,
    { targetId: 't', serviceToken: 's', startIndex: 60 },
  );
});
