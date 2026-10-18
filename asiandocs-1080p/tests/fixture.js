/* Fake J-Stream controls for the Playwright harness. Not part of the extension. */
(function () {
  const CSS = `
    .eqp-resolution-balloon { display: none; }
    .eqp-player.eqp-quality-visible .eqp-resolution-balloon { display: block; }
    .eqp-content-resolution, .eqp-resolution-item, .eqp-resolution-balloon-item,
    .jsp-resolution-box, .jsp-resolution-item {
      display: block;
      min-width: 88px;
      min-height: 28px;
      color: #fff;
      background: #222;
      margin: 2px;
      padding: 2px 6px;
    }
    .jsp-resolution-base { display: none; }
    .jsp-player.resolution-shown .jsp-resolution-base { display: flex; flex-direction: column; }
  `;

  function log(entry) {
    const row = Object.assign({ t: performance.now() }, entry);
    window.__qlog = window.__qlog || [];
    window.__qlog.push(row);
  }

  function ensureStyle(node) {
    const root = node.getRootNode();
    const parent = root === document ? document.head || document.documentElement : root;
    if (!parent || typeof parent.querySelector !== "function") return;
    if (parent.querySelector("style[data-ad-fixture]")) return;
    const style = document.createElement("style");
    style.dataset.adFixture = "1";
    style.textContent = CSS;
    parent.appendChild(style);
  }

  function labelFor(type) {
    return type === "auto" ? "Auto" : type;
  }

  window.EQP_QUALITIES = [
    { type: "360p", index: 2, label: "360p" },
    { type: "1080p", index: 5, label: "1080p" },
    { type: "auto", index: 0, label: "Auto" },
    { type: "480p", index: 3, label: "480p" },
    { type: "720p", index: 4, label: "720p" },
    { type: "240p", index: 1, label: "240p" },
  ];

  window.EQP_NO_1080 = [
    { type: "auto", index: 0, label: "Auto" },
    { type: "360p", index: 2, label: "360p" },
    { type: "480p", index: 3, label: "480p" },
  ];

  window.installEqp = function installEqp(player, options) {
    const opts = options || {};
    const qualities = opts.qualities || window.EQP_QUALITIES;
    const initial = opts.initial || "360p";
    const variant = opts.variant || "item";
    const itemClass = variant === "balloon" ? "eqp-resolution-balloon-item" : "eqp-resolution-item";
    const focusClass = variant === "balloon" ? "eqp-resolution-balloon-item-focus" : "eqp-resolution-item-focus";
    ensureStyle(player);
    player.classList.add("eqp-player");
    const items = qualities
      .map((quality) => {
        const focus = quality.type === initial ? focusClass : "";
        return `<div class="${itemClass} ${focus}" data-type="${quality.type}" data-index="${quality.index}">${quality.label}</div>`;
      })
      .join("");
    player.innerHTML = `
      <div class="eqp-icon-resolution">
        <div class="eqp-content-resolution" role="button"><span>${labelFor(initial)}</span></div>
      </div>
      <div class="eqp-resolution-balloon">
        <div class="eqp-resolution-balloon-list">${items}</div>
      </div>`;
    const button = player.querySelector(".eqp-content-resolution");
    let open = false;
    const paint = () => player.classList.toggle("eqp-quality-visible", open);
    paint();
    button.addEventListener("click", () => {
      log({ id: opts.id || "eqp", action: "open", type: null, ui: "eqp" });
      open = !open;
      paint();
    });
    player.querySelectorAll("." + itemClass).forEach((item) => {
      item.addEventListener("click", () => {
        if (!open) {
          log({ id: opts.id || "eqp", action: "ignored", type: item.dataset.type, ui: "eqp" });
          return;
        }
        log({ id: opts.id || "eqp", action: "select", type: item.dataset.type, ui: "eqp" });
        player.querySelectorAll("." + itemClass).forEach((el) => el.classList.remove(focusClass));
        item.classList.add(focusClass);
        button.querySelector("span").textContent = labelFor(item.dataset.type);
        open = false;
        paint();
      });
    });
  };

  window.installJsp = function installJsp(player, options) {
    const opts = options || {};
    const mode = opts.mode || "px";
    const qualities = mode === "mbps"
      ? [
          { type: "0.8Mbps", label: "0.8Mbps" },
          { type: "auto", label: "auto" },
          { type: "1.2Mbps", label: "1.2Mbps" },
          { type: "2.4Mbps", label: "2.4Mbps" },
        ]
      : [
          { type: "auto", label: "Auto" },
          { type: "360p", label: "360p" },
          { type: "1080p", label: "1080p" },
          { type: "480p", label: "480p" },
        ];
    const initial = opts.initial || (mode === "mbps" ? "0.8Mbps" : "360p");
    ensureStyle(player);
    player.classList.add("jsp-player");
    const items = qualities
      .map((quality) => {
        const check = quality.type === initial ? "jsp-check" : "";
        const dataType = mode === "px" ? ` data-type="${quality.type}"` : "";
        return `<div class="jsp-resolution-item ${check}"${dataType}>${quality.label}</div>`;
      })
      .join("");
    player.innerHTML = `
      <div class="jsp-resolution-box" role="button">
        <span class="jsp-resolution-label">画質</span>
        <span class="jsp-resolution-value">${initial === "auto" ? "auto" : initial}</span>
      </div>
      <div class="jsp-resolution-base">${items}</div>`;
    const box = player.querySelector(".jsp-resolution-box");
    const value = player.querySelector(".jsp-resolution-value");
    box.addEventListener("click", () => {
      log({ id: opts.id || "jsp", action: "open", type: null, ui: "jsp" });
      player.classList.toggle("resolution-shown");
    });
    player.querySelectorAll(".jsp-resolution-item").forEach((item) => {
      item.addEventListener("click", () => {
        if (!player.classList.contains("resolution-shown")) {
          log({ id: opts.id || "jsp", action: "ignored", type: item.textContent.trim(), ui: "jsp" });
          return;
        }
        const type = item.dataset.type || item.textContent.trim();
        log({ id: opts.id || "jsp", action: "select", type, ui: "jsp" });
        player.querySelectorAll(".jsp-resolution-item").forEach((el) => el.classList.remove("jsp-check"));
        item.classList.add("jsp-check");
        value.textContent = item.textContent.trim();
        player.classList.remove("resolution-shown");
      });
    });
  };
})();
