import { test, expect, chromium } from "@playwright/test";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { startServer } from "./server.mjs";

const extensionPath = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

let server;

test.beforeAll(async () => {
  server = await startServer();
});

test.afterAll(async () => {
  await server.close();
});

async function launch() {
  const userDataDir = await fs.mkdtemp(path.join(os.tmpdir(), "ad1080-"));
  const context = await chromium.launchPersistentContext(userDataDir, {
    headless: false,
    viewport: { width: 960, height: 540 },
    ignoreDefaultArgs: ["--disable-extensions", "--disable-component-extensions-with-background-pages"],
    args: [
      `--disable-extensions-except=${extensionPath}`,
      `--load-extension=${extensionPath}`,
      "--headless=new",
      "--no-sandbox",
      "--disable-dev-shm-usage",
      "--disable-features=HttpsUpgrades,HTTPSFirstBalancedModeAutoEnable",
      `--host-resolver-rules=MAP test.asiandocs.co.jp 127.0.0.1,MAP player.stream.ne.jp 127.0.0.1`,
    ],
  });
  return { context, userDataDir };
}

function site(pathname) {
  return `http://test.asiandocs.co.jp:${server.port}${pathname}`;
}

async function openPage(pathname) {
  const launched = await launch();
  const page = await launched.context.newPage();
  const requests = [];
  page.on("request", (req) => requests.push(req.url()));
  page.on("pageerror", (err) => console.log("PAGEERROR", err.message));
  await page.goto(site(pathname), { waitUntil: "domcontentloaded" });
  return { page, requests, ...launched };
}

async function finish(launched) {
  await launched.context.close();
  await fs.rm(launched.userDataDir, { recursive: true, force: true });
}

async function label(page) {
  return page.evaluate(() => {
    const el = document.querySelector(".eqp-content-resolution span, .jsp-resolution-value");
    return el ? el.textContent.trim() : "";
  });
}

async function logOf(page) {
  return page.evaluate(() => window.__qlog || []);
}

test("direct eqp menu selects 1080p by data-type, not DOM index", async () => {
  const launched = await openPage("/direct");
  try {
    await expect.poll(() => label(launched.page)).toBe("1080p");
    await launched.page.waitForTimeout(400);
    const log = await logOf(launched.page);
    const selects = log.filter((row) => row.action === "select");
    const opens = log.filter((row) => row.action === "open");
    expect(selects.map((row) => row.type)).toEqual(["1080p"]);
    expect(opens).toHaveLength(1);
    expect(log.some((row) => row.action === "ignored")).toBe(false);
    expect(opens[0].t).toBeLessThan(selects[0].t);
    const domIndex = await launched.page.evaluate(() => {
      const items = [...document.querySelectorAll(".eqp-resolution-item")];
      return {
        indexOf1080: items.findIndex((el) => el.dataset.type === "1080p"),
        textAt5: items[5] ? items[5].dataset.type : null,
      };
    });
    expect(domIndex.indexOf1080).not.toBe(5);
    expect(domIndex.textAt5).toBe("240p");
    const urls = launched.requests.map((url) => new URL(url));
    expect(urls.every((url) => url.hostname === "test.asiandocs.co.jp")).toBe(true);
    expect(urls.map((url) => url.pathname).filter((pathname) => pathname !== "/favicon.ico")).toEqual([
      "/direct",
      "/fixture.js",
    ]);
  } finally {
    await finish(launched);
  }
});

test("player inserted after load is still switched", async () => {
  const launched = await openPage("/delayed");
  try {
    await expect.poll(() => label(launched.page), { timeout: 10_000 }).toBe("1080p");
    const log = await logOf(launched.page);
    expect(log.filter((row) => row.action === "select").map((row) => row.type)).toEqual(["1080p"]);
  } finally {
    await finish(launched);
  }
});

test("player inside a stream.ne.jp iframe is switched from that frame", async () => {
  const launched = await openPage("/iframe-parent");
  try {
    await expect.poll(() => launched.page.frames().some((frame) => /player\.stream\.ne\.jp/.test(frame.url()))).toBe(true);
    const frame = launched.page.frame({ url: /player\.stream\.ne\.jp/ });
    await expect.poll(() => frame.evaluate(() => {
      const el = document.querySelector(".eqp-content-resolution span");
      return el ? el.textContent.trim() : "";
    })).toBe("1080p");
    const log = await frame.evaluate(() => window.__qlog || []);
    expect(log.filter((row) => row.action === "select").map((row) => row.type)).toEqual(["1080p"]);
    const parentLog = await logOf(launched.page);
    expect(parentLog).toEqual([]);
  } finally {
    await finish(launched);
  }
});

test("missing 1080p selects the highest numeric quality and skips Auto", async () => {
  const launched = await openPage("/missing");
  try {
    await expect.poll(() => label(launched.page)).toBe("480p");
    await launched.page.waitForTimeout(400);
    const log = await logOf(launched.page);
    expect(log.filter((row) => row.action === "select").map((row) => row.type)).toEqual(["480p"]);
    expect(log.some((row) => row.type === "auto")).toBe(false);
  } finally {
    await finish(launched);
  }
});

test("jsp menu opens from the resolution box and selects 1080p", async () => {
  const launched = await openPage("/jsp");
  try {
    await expect.poll(() => label(launched.page)).toBe("1080p");
    await launched.page.waitForTimeout(400);
    const log = await logOf(launched.page);
    expect(log.filter((row) => row.action === "open")).toHaveLength(1);
    expect(log.filter((row) => row.action === "select").map((row) => row.type)).toEqual(["1080p"]);
    expect(log.every((row) => row.ui === "jsp")).toBe(true);
  } finally {
    await finish(launched);
  }
});

test("jsp bitrate list without 1080p picks the highest bitrate", async () => {
  const launched = await openPage("/jsp-mbps");
  try {
    await expect.poll(() => label(launched.page)).toBe("2.4Mbps");
    const log = await logOf(launched.page);
    expect(log.filter((row) => row.action === "select").map((row) => row.type)).toEqual(["2.4Mbps"]);
  } finally {
    await finish(launched);
  }
});

test("already-selected 1080p is not clicked again", async () => {
  const launched = await openPage("/already");
  try {
    await expect.poll(() => launched.page.evaluate(() => document.documentElement.dataset.ad1080Watching || "")).toBe("1");
    await launched.page.waitForTimeout(1000);
    expect(await label(launched.page)).toBe("1080p");
    expect(await logOf(launched.page)).toEqual([]);
  } finally {
    await finish(launched);
  }
});

test("eqp-resolution-balloon-item variant is selected", async () => {
  const launched = await openPage("/balloon");
  try {
    await expect.poll(() => label(launched.page)).toBe("1080p");
    const selected = await launched.page.evaluate(() => {
      const el = document.querySelector('[data-type="1080p"]');
      return el ? el.className : "";
    });
    expect(selected).toContain("eqp-resolution-balloon-item-focus");
  } finally {
    await finish(launched);
  }
});

test("open shadow root player is switched", async () => {
  const launched = await openPage("/shadow");
  try {
    await expect.poll(() => launched.page.evaluate(() => {
      const span = document.getElementById("host").shadowRoot.querySelector(".eqp-content-resolution span");
      return span ? span.textContent.trim() : "";
    })).toBe("1080p");
  } finally {
    await finish(launched);
  }
});

test("eqp controls win when a nested jsp menu is also present", async () => {
  const launched = await openPage("/both");
  try {
    await expect.poll(() => label(launched.page)).toBe("1080p");
    await launched.page.waitForTimeout(400);
    const log = await logOf(launched.page);
    expect(log.filter((row) => row.ui === "eqp" && row.action === "select").map((row) => row.type)).toEqual(["1080p"]);
    expect(log.some((row) => row.ui === "jsp")).toBe(false);
  } finally {
    await finish(launched);
  }
});

test("a new player after in-page navigation is switched", async () => {
  const launched = await openPage("/spa");
  try {
    await expect.poll(() => label(launched.page)).toBe("1080p");
    await launched.page.click("#next");
    await expect.poll(() => launched.page.evaluate(() => {
      const el = document.querySelector("#player-b .eqp-content-resolution span");
      return el ? el.textContent.trim() : "";
    })).toBe("1080p");
    const log = await logOf(launched.page);
    const selects = log.filter((row) => row.action === "select");
    expect(selects.map((row) => `${row.id}:${row.type}`)).toEqual(["a:1080p", "b:1080p"]);
  } finally {
    await finish(launched);
  }
});

test("unrelated hosts are left alone", async () => {
  const launched = await launch();
  const page = await launched.context.newPage();
  try {
    await page.goto(`http://127.0.0.1:${server.port}/direct`, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(1000);
    expect(await label(page)).toBe("360p");
    expect(await logOf(page)).toEqual([]);
    expect(await page.evaluate(() => document.documentElement.dataset.ad1080Watching || "")).toBe("");
  } finally {
    await finish({ ...launched, page });
  }
});

test("observer disconnects after 30s and a later history change rearms it", async () => {
  test.setTimeout(60_000);
  const launched = await openPage("/empty");
  try {
    await expect.poll(() => launched.page.evaluate(() => document.documentElement.dataset.ad1080Watching || "")).toBe("1");
    await launched.page.waitForFunction(() => document.documentElement.dataset.ad1080Watching !== "1", null, {
      timeout: 45_000,
    });
    await launched.page.evaluate(() => {
      history.pushState({}, "", "/contents/2");
      window.insertPlayer();
    });
    await expect.poll(() => label(launched.page), { timeout: 10_000 }).toBe("1080p");
    const log = await logOf(launched.page);
    expect(log.filter((row) => row.action === "select").map((row) => row.type)).toEqual(["1080p"]);
  } finally {
    await finish(launched);
  }
});
