# Asiandocs 1080p

Manifest V3 Chrome extension. On [asiandocs.co.jp](https://asiandocs.co.jp) member pages, the J-Stream / Equipmedia player starts at a low quality (often 360p). This extension waits for the player and clicks **1080p**. If 1080p is not listed, it clicks the highest numeric quality and leaves **Auto** alone.

It only clicks DOM controls. It does not read cookies, store credentials, send requests, or download video.

## Install

1. Open `chrome://extensions`.
2. Turn on **Developer mode**.
3. **Load unpacked** and choose this folder (`asiandocs-1080p/`, the one that contains `manifest.json`).
4. Open a member video page and start playback. The quality control should move to 1080p (or the highest listed size).

Reload the extension from that page after pulling updates.

## How it works

Content scripts run at `document_start` with `all_frames: true`.

Matched hosts:

| Pattern | Why |
| --- | --- |
| `asiandocs.co.jp` and `*.asiandocs.co.jp` | The member page. The player is sometimes built in this document. |
| `stream.ne.jp` and `*.stream.ne.jp` | J-Stream player documents. Equipmedia's loader is `https://ssl-cache.stream.ne.jp/.../player/t3/if.js`, and the player frame itself is a page such as `https://ssl-cache.stream.ne.jp/.../player/player_3_2_0/onetag_t3.html`. The publish-tag base path `b` is `*.eq.webcdn.stream.ne.jp`. Both names are under `*.stream.ne.jp`. |

`stream.co.jp` is J-Stream's corporate and Equipmedia help site (`support.eq.stream.co.jp`). The embed traces checked for this extension serve the player document from `stream.ne.jp`, so `stream.co.jp` is not matched. `jstream.jp` was not confirmed as a player-document host, so it is not matched either.

The parent page and a cross-origin player frame do not share DOM. `all_frames` plus the player host is what lets the script reach controls that live in the frame.

Two files are injected:

- `content.js` (isolated world) watches the document and clicks the quality control.
- `nav.js` (main world) wraps `history.pushState` / `replaceState` and listens for `popstate` / `hashchange`. It only dispatches a `asiandocs-1080p-nav` event so a single-page navigation can be noticed. Page Content-Security-Policy does not block an extension main-world script. The wrapper does not read the page, cookies, or storage.

`content.js` attaches a `MutationObserver` to `<html>` (`childList`, `subtree`, and `class` / `hidden` / `aria-selected` / `aria-checked`). It disconnects after 30 seconds. While it is watching, `<html data-ad1080-watching="1">` is set. A history change starts a fresh 30 second watch, which is how a player inserted after the first timeout is still handled. Replacing the player node while a watch is already active is handled by the observer without a navigation.

Quality choice:

- Prefer an item whose `data-type` or text is `1080p` (also `フルHD` / `FHD` / `full HD`).
- Otherwise the highest `NNNp` value, for example 480p over 360p.
- If nothing has a pixel size, the highest bitrate label (`Mbps` / `Kbps` / `bps`). This matches the inner jsp menu, whose items are bandwidth strings plus `auto`.
- `Auto`, `自動`, `オート`, and `data-type="0"` are never chosen.
- DOM position is not used. A full Equipmedia list puts full HD at quality index 5, but the script does not click "the 6th row".

Menus:

- Equipmedia (`eqp`): items are `.eqp-resolution-item` or `.eqp-resolution-balloon-item` inside `.eqp-resolution-balloon-list`. The public player CSS shows the list only while an ancestor has `.eqp-quality-visible`, after a click on `.eqp-content-resolution`. The script opens that control when the item is not visible, then clicks the item. It does not click a hidden item.
- J-Stream inner menu (`jsp`): `.jsp-resolution-box` adds `.resolution-shown`, which reveals `.jsp-resolution-base` and `.jsp-resolution-item`. Same open-then-click sequence. The selected row uses `.jsp-check`.
- If an `.eqp-player` already has eqp quality items, the nested jsp menu is left alone. The public stylesheet hides `#jsp-right-controls` when the eqp controls are the ones on screen.

A row counts as already selected when it has `aria-selected` / `aria-checked`, `.jsp-check`, or a resolution class ending in `focus`, `selected`, `current`, or `checked` (including `.eqp-resolution-balloon-item-focus`). The text of the quality button is also compared. In those cases the script does not click. Each control is capped at two selection clicks per cycle and six over the life of that element, so a player that ignores the click cannot loop. If the same button later shows a different quality, the cycle resets up to three times (a reused shell); the lifetime cap still applies.

Open shadow roots are searched. A closed shadow root is not visible to the script.

## Tests

```bash
cd asiandocs-1080p/tests
npm install
npx playwright install chromium
npm test
```

Playwright launches its Chromium (Chrome for Testing) in `--headless=new` with `--load-extension` pointed at this folder. Branded Google Chrome ignores `--load-extension` / `--disable-extensions-except` on the command line, so the automated run uses Chromium. Loading the same folder from `chrome://extensions` is the install path above.

The harness serves fake players on `http://test.asiandocs.co.jp` and `http://player.stream.ne.jp` via `--host-resolver-rules` to `127.0.0.1`. Those hostnames are what make the real content-script match patterns run. `http://127.0.0.1` is the negative case.

## What was verified

Automated, against fake DOM, with the unpacked extension loaded in Chromium 156 headless:

- Direct eqp menu. `1080p` has `data-index="5"` but is not the 6th row (that row is `240p`). The script opens `.eqp-content-resolution` once, then clicks `data-type="1080p"` once. Hidden-item clicks are ignored by the fixture and did not occur.
- The same player inserted 800ms after load.
- Cross-origin iframe: parent `test.asiandocs.co.jp`, frame `player.stream.ne.jp`. The frame switches to 1080p. The parent document has no player and records no clicks.
- No 1080p row: Auto / 360p / 480p ends on 480p, and Auto is not clicked.
- jsp menu (`.jsp-resolution-box`, `.jsp-resolution-base`, `.jsp-resolution-item`, `.jsp-check`) selects 1080p, opening the box first.
- jsp rows labeled `0.8Mbps`, `1.2Mbps`, `2.4Mbps`, and `auto` select `2.4Mbps`.
- 1080p already focused: zero opens and zero selects after the watcher is confirmed active.
- Item class `.eqp-resolution-balloon-item` and selected class `.eqp-resolution-balloon-item-focus` (the names in the public Equipmedia stylesheet).
- The same eqp controls inside an open shadow root.
- eqp and jsp menus in one player: only the eqp control is clicked.
- In-page navigation (`history.pushState`) that replaces the player with a new one, while the watcher is still active.
- Watcher removal after 30 seconds (`data-ad1080-watching` cleared), then `pushState` plus a new player, which is switched to 1080p.
- `http://127.0.0.1` with the same markup is not touched (label stays 360p, no watcher attribute).
- On the direct page, the only document requests are the page and `fixture.js` (plus a possible favicon). The content script has no `fetch`, XHR, WebSocket, or download call.

## What was not verified

- A logged-in member page on asiandocs.co.jp. An anonymous fetch of `https://asiandocs.co.jp/contents/1386` returns the editorial page and a YouTube trailer iframe. It does not include `eqp-player`.
- Whether the real player ignores untrusted clicks. `element.click()` from a content script is not a user gesture (`event.isTrusted` is false). The fixtures listen for a normal `click`. If Equipmedia requires a trusted event, this extension cannot switch quality without a heavier permission such as the debugger, which this package does not request.
- The live menu's exact markup: which class is present (`eqp-resolution-item` vs `eqp-resolution-balloon-item`), the selected-state class, and whether the list is in a closed shadow root.
- A real `stream.ne.jp` player frame on the member site (the iframe `src` host was not captured from a logged-in session).
- Branded Google Chrome's `chrome://extensions` dialog itself. The directory is the unpacked extension Chromium loaded; the branded browser blocks the command-line flag used by the test.

## If it does nothing on the real player

These details would show which assumption failed:

- `outerHTML` of `.eqp-resolution-balloon-list` (one selected row and one other row).
- `outerHTML` of `.eqp-content-resolution`, including its parent classes.
- The player iframe's `src` (scheme and host are enough; query strings can be trimmed).
- Whether the controls are inside a shadow root, and whether that root is `open` or `closed`.
- The class list and `data-*` attributes of the 1080p row and of the row that looks selected at 360p.
- Whether a click on the quality item is ignored until the balloon is open.
- For the inner jsp menu: the text of each `.jsp-resolution-item` (`1080p`, `フルHD`, or `2.4Mbps`) and which element the click listener is attached to.
