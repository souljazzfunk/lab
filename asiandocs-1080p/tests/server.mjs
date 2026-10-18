import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const fixturePath = path.join(path.dirname(fileURLToPath(import.meta.url)), "fixture.js");

function page(title, body) {
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>${title}</title>
  <script src="/fixture.js"></script>
</head>
<body>
${body}
</body>
</html>`;
}

function scriptPage(title, bodyHtml, inline) {
  return page(
    title,
    `${bodyHtml}
<script>
${inline}
</script>`,
  );
}

function handler(req, res) {
  const url = new URL(req.url || "/", "http://fixture.local");
  const host = req.headers.host || "";
  const port = (host.match(/:(\d+)$/) || [])[1] || "80";
  if (url.pathname === "/fixture.js") {
    res.writeHead(200, { "content-type": "text/javascript; charset=utf-8", "cache-control": "no-store" });
    res.end(fs.readFileSync(fixturePath));
    return;
  }

  let html = "";
  if (url.pathname === "/direct" || url.pathname === "/iframe-player") {
    html = scriptPage(
      "direct",
      `<div id="player"></div>`,
      `installEqp(document.getElementById("player"), { id: "direct" });`,
    );
  } else if (url.pathname === "/delayed") {
    html = scriptPage(
      "delayed",
      `<div id="mount"></div>`,
      `setTimeout(() => {
        const player = document.createElement("div");
        player.id = "player";
        document.getElementById("mount").appendChild(player);
        installEqp(player, { id: "delayed" });
      }, 800);`,
    );
  } else if (url.pathname === "/missing") {
    html = scriptPage(
      "missing",
      `<div id="player"></div>`,
      `installEqp(document.getElementById("player"), { id: "missing", initial: "360p", qualities: EQP_NO_1080 });`,
    );
  } else if (url.pathname === "/jsp") {
    html = scriptPage(
      "jsp",
      `<div id="player"></div>`,
      `installJsp(document.getElementById("player"), { id: "jsp", mode: "px" });`,
    );
  } else if (url.pathname === "/jsp-mbps") {
    html = scriptPage(
      "jsp-mbps",
      `<div id="player"></div>`,
      `installJsp(document.getElementById("player"), { id: "jsp-mbps", mode: "mbps" });`,
    );
  } else if (url.pathname === "/already") {
    html = scriptPage(
      "already",
      `<div id="player"></div>`,
      `installEqp(document.getElementById("player"), { id: "already", initial: "1080p" });`,
    );
  } else if (url.pathname === "/balloon") {
    html = scriptPage(
      "balloon",
      `<div id="player"></div>`,
      `installEqp(document.getElementById("player"), { id: "balloon", variant: "balloon" });`,
    );
  } else if (url.pathname === "/shadow") {
    html = scriptPage(
      "shadow",
      `<div id="host"></div>`,
      `const host = document.getElementById("host");
      const shadow = host.attachShadow({ mode: "open" });
      const player = document.createElement("div");
      shadow.appendChild(player);
      installEqp(player, { id: "shadow" });`,
    );
  } else if (url.pathname === "/both") {
    html = scriptPage(
      "both",
      `<div id="player"></div>`,
      `const player = document.getElementById("player");
      installEqp(player, { id: "both-eqp" });
      const inner = document.createElement("div");
      player.appendChild(inner);
      installJsp(inner, { id: "both-jsp", mode: "px" });`,
    );
  } else if (url.pathname === "/spa") {
    html = scriptPage(
      "spa",
      `<div id="mount"></div><button id="next" type="button">next</button>`,
      `function mount(id) {
        const slot = document.getElementById("mount");
        slot.replaceChildren();
        const player = document.createElement("div");
        player.id = "player-" + id;
        slot.appendChild(player);
        installEqp(player, { id });
      }
      mount("a");
      document.getElementById("next").addEventListener("click", () => {
        history.pushState({}, "", "/contents/2000");
        mount("b");
      });`,
    );
  } else if (url.pathname === "/empty") {
    html = scriptPage(
      "empty",
      `<div id="mount"></div>`,
      `window.insertPlayer = function () {
        const slot = document.getElementById("mount");
        slot.replaceChildren();
        const player = document.createElement("div");
        player.id = "player";
        slot.appendChild(player);
        installEqp(player, { id: "after-nav" });
      };`,
    );
  } else if (url.pathname === "/iframe-parent") {
    html = page(
      "iframe-parent",
      `<iframe id="player-frame" title="player" width="640" height="360" src="http://player.stream.ne.jp:${port}/iframe-player"></iframe>`,
    );
  } else {
    res.writeHead(404, { "content-type": "text/plain" });
    res.end("not found");
    return;
  }

  res.writeHead(200, { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" });
  res.end(html);
}

export function startServer() {
  return new Promise((resolve) => {
    const server = http.createServer(handler);
    server.listen(0, "127.0.0.1", () => {
      const { port } = server.address();
      resolve({
        port,
        close() {
          return new Promise((done, reject) => server.close((err) => (err ? reject(err) : done())));
        },
      });
    });
  });
}
