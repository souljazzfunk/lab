/* Notifies the isolated content script when the site changes the URL
   without a full load. History methods live in the page world, so the
   wrapper has to live there too. This file does not read the DOM,
   cookies, storage, or the network. */
(function () {
  if (window.__asiandocs1080Nav) return;
  window.__asiandocs1080Nav = true;

  function notify() {
    document.dispatchEvent(new CustomEvent("asiandocs-1080p-nav"));
  }

  function wrap(name) {
    const original = history[name];
    if (typeof original !== "function") return;
    history[name] = function () {
      const result = original.apply(this, arguments);
      notify();
      return result;
    };
  }

  wrap("pushState");
  wrap("replaceState");
  window.addEventListener("popstate", notify);
  window.addEventListener("hashchange", notify);
})();
