/* Waits for a J-Stream / Equipmedia player and chooses 1080p, or the
   highest numeric quality when 1080p is not listed. Clicks only.
   No network, cookies, storage, or downloads. */
(function () {
  if (window.__asiandocs1080) return;
  window.__asiandocs1080 = true;

  const WAIT_MS = 30000;
  const MAX_SELECTS_PER_CYCLE = 2;
  const MAX_OPENS_PER_CYCLE = 3;
  const MAX_LIFETIME_SELECTS = 6;
  const MAX_RESETS = 3;

  const states = new WeakMap();
  let observer = null;
  let waitTimer = null;
  let scanTimer = null;
  let scanning = false;

  function fold(value) {
    return String(value || "")
      .replace(/[０-９]/g, (ch) => String.fromCharCode(ch.charCodeAt(0) - 0xfee0))
      .replace(/Ｐ/g, "p")
      .replace(/\s+/g, " ")
      .trim();
  }

  function isAutoToken(value) {
    return /^(auto|自動|オート|abr|0)$/i.test(value);
  }

  function pixels(value) {
    if (!value) return null;
    const labeled = value.match(/(\d{3,4})\s*p\b/i);
    if (labeled) return Number(labeled[1]);
    if (/^\d{3,4}$/.test(value)) {
      const height = Number(value);
      if (height >= 144 && height <= 4320) return height;
    }
    return null;
  }

  function bitrate(value) {
    const mbps = value.match(/(\d+(?:\.\d+)?)\s*mbps\b/i);
    if (mbps) return Number(mbps[1]) * 1000;
    const kbps = value.match(/(\d+(?:\.\d+)?)\s*kbps\b/i);
    if (kbps) return Number(kbps[1]);
    const bps = value.match(/(\d+(?:\.\d+)?)\s*bps\b/i);
    if (bps) return Number(bps[1]) / 1000;
    return null;
  }

  function describe(dataType, text) {
    const dt = fold(dataType);
    const label = fold(text);
    if (isAutoToken(dt)) return { auto: true };
    const dtPixels = pixels(dt);
    if (dtPixels) return { auto: false, kind: "px", value: dtPixels };
    if (isAutoToken(label)) return { auto: true };
    const textPixels = pixels(label);
    if (textPixels) return { auto: false, kind: "px", value: textPixels };
    if (/フル\s*hd|fhd|full\s*hd/i.test(`${dt} ${label}`)) {
      return { auto: false, kind: "px", value: 1080 };
    }
    const rate = bitrate(`${dt} ${label}`);
    if (rate != null && Number.isFinite(rate)) {
      return { auto: false, kind: "bitrate", value: rate };
    }
    return null;
  }

  function qualityOf(el) {
    return describe(el.getAttribute("data-type"), el.textContent);
  }

  function qualityOfText(text) {
    return describe("", text);
  }

  function pick(items) {
    const parsed = [];
    for (const el of items) {
      const q = qualityOf(el);
      if (q && !q.auto) parsed.push({ el, q });
    }
    const px = parsed.filter((item) => item.q.kind === "px");
    if (px.length) {
      const fullHd = px.find((item) => item.q.value === 1080);
      if (fullHd) return fullHd;
      return px.reduce((best, item) => (item.q.value > best.q.value ? item : best));
    }
    const rates = parsed.filter((item) => item.q.kind === "bitrate");
    if (!rates.length) return null;
    return rates.reduce((best, item) => (item.q.value > best.q.value ? item : best));
  }

  function isSelected(el) {
    if (!el) return false;
    if (el.getAttribute("aria-selected") === "true") return true;
    if (el.getAttribute("aria-checked") === "true") return true;
    if (el.classList.contains("jsp-check")) return true;
    for (const name of el.classList) {
      if (name === "selected" || name === "is-selected" || name === "checked") return true;
      if (/resolution/i.test(name) && /(focus|selected|current|checked)$/i.test(name)) return true;
    }
    return false;
  }

  function isCurrent(opener, target) {
    if (isSelected(target.el)) return true;
    if (!opener) return false;
    const shown = qualityOfText(opener.textContent);
    if (!shown || shown.auto) return false;
    return shown.kind === target.q.kind && shown.value === target.q.value;
  }

  function isShown(el) {
    if (!el || !el.isConnected) return false;
    for (let node = el; node && node.nodeType === 1; node = node.parentElement) {
      const style = getComputedStyle(node);
      if (style.display === "none" || style.visibility === "hidden" || style.visibility === "collapse") {
        return false;
      }
    }
    const root = el.getRootNode();
    if (root instanceof ShadowRoot && !isShown(root.host)) return false;
    if (getComputedStyle(el).pointerEvents === "none") return false;
    const rect = el.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  }

  function queryAllDeep(selector) {
    const found = [];
    const stack = [document];
    while (stack.length) {
      const node = stack.pop();
      if (!node || typeof node.querySelectorAll !== "function") continue;
      for (const el of node.querySelectorAll(selector)) found.push(el);
      for (const el of node.querySelectorAll("*")) {
        if (el.shadowRoot) stack.push(el.shadowRoot);
      }
    }
    return found;
  }

  function playerScope(el) {
    const closest = el.closest(".eqp-player, .jsp-player");
    if (closest) return closest;
    const root = el.getRootNode();
    if (root && typeof root.querySelector === "function") return root;
    return document;
  }

  function stateFor(key) {
    let state = states.get(key);
    if (!state) {
      state = {
        applied: null,
        opens: 0,
        selects: 0,
        lifetime: 0,
        resets: 0,
        gaveUp: false,
      };
      states.set(key, state);
    }
    return state;
  }

  function choose(opener, items) {
    const target = pick(items);
    if (!target || !opener) return;
    const state = stateFor(opener);
    const shown = qualityOfText(opener.textContent);
    if (
      state.applied &&
      shown &&
      !shown.auto &&
      (shown.kind !== state.applied.kind || shown.value !== state.applied.value) &&
      !isSelected(target.el)
    ) {
      if (state.resets < MAX_RESETS) {
        state.resets += 1;
        state.opens = 0;
        state.selects = 0;
        state.gaveUp = false;
        state.applied = null;
      }
    }
    if (isCurrent(opener, target)) {
      state.applied = { kind: target.q.kind, value: target.q.value };
      return;
    }
    if (state.gaveUp || state.selects >= MAX_SELECTS_PER_CYCLE || state.lifetime >= MAX_LIFETIME_SELECTS) {
      state.gaveUp = true;
      return;
    }
    if (!isShown(target.el)) {
      if (!opener.isConnected || state.opens >= MAX_OPENS_PER_CYCLE) return;
      state.opens += 1;
      opener.click();
      if (!isShown(target.el)) return;
    }
    if (!isShown(target.el)) return;
    state.selects += 1;
    state.lifetime += 1;
    target.el.click();
    if (isCurrent(opener, target)) {
      state.applied = { kind: target.q.kind, value: target.q.value };
    }
  }

  function eqpItems(scope) {
    const list = scope.querySelector(".eqp-resolution-balloon-list");
    if (!list) return [];
    return [...list.querySelectorAll(".eqp-resolution-item, .eqp-resolution-balloon-item")];
  }

  function scan() {
    if (scanning) return;
    scanning = true;
    try {
      const scopesWithEqpItems = new Set();
      for (const button of queryAllDeep(".eqp-content-resolution")) {
        const scope = playerScope(button);
        const items = eqpItems(scope);
        if (!items.length) continue;
        scopesWithEqpItems.add(scope);
        choose(button, items);
      }
      for (const box of queryAllDeep(".jsp-resolution-box")) {
        const scope = playerScope(box);
        const outer = typeof scope.closest === "function" ? scope.closest(".eqp-player") : null;
        if (scopesWithEqpItems.has(scope) || (outer && scopesWithEqpItems.has(outer))) continue;
        const base = scope.querySelector(".jsp-resolution-base");
        if (!base) continue;
        const items = [...base.querySelectorAll(".jsp-resolution-item")];
        if (!items.length) continue;
        choose(box, items);
      }
    } catch (err) {
      console.error("[asiandocs-1080p]", err);
    } finally {
      scanning = false;
    }
  }

  function scheduleScan() {
    if (scanTimer != null) return;
    scanTimer = setTimeout(() => {
      scanTimer = null;
      scan();
    }, 0);
  }

  function setWatching(on) {
    const root = document.documentElement;
    if (!root) return;
    if (on) root.dataset.ad1080Watching = "1";
    else delete root.dataset.ad1080Watching;
  }

  function disarm() {
    if (observer) observer.disconnect();
    observer = null;
    if (waitTimer != null) clearTimeout(waitTimer);
    waitTimer = null;
    setWatching(false);
  }

  function arm() {
    if (!document.documentElement) return;
    disarm();
    setWatching(true);
    observer = new MutationObserver(scheduleScan);
    observer.observe(document.documentElement, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["class", "hidden", "aria-selected", "aria-checked"],
    });
    waitTimer = setTimeout(disarm, WAIT_MS);
    scheduleScan();
  }

  document.addEventListener("asiandocs-1080p-nav", () => {
    arm();
  });

  function boot() {
    arm();
  }

  if (document.documentElement) boot();
  else {
    const ready = new MutationObserver(() => {
      if (!document.documentElement) return;
      ready.disconnect();
      boot();
    });
    ready.observe(document, { childList: true });
  }
})();
