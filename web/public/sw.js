/*
 * ANSIT service worker.
 *
 * Registered as /sw.js?v=<build id>, so every deployment is a new worker with
 * its own caches. A new worker waits until the user accepts the update (the
 * page sends SKIP_WAITING); it never takes over mid-recording.
 *
 * What is cached:
 * - the app shell pages and the offline page (on install);
 * - build assets, fonts and icons (cache first; their URLs are content-hashed);
 * - pages the user has visited and their route data (network first, cache as
 *   the fallback).
 *
 * What is never touched: any non-GET request (audio uploads, feedback), and
 * any other origin (the API, recitation audio, portraits). Recognition always
 * needs the network, and the offline page says so.
 */
const VERSION = new URL(self.location.href).searchParams.get("v") || "dev";
const SHELL = `ansit-shell-${VERSION}`;
const PAGES = `ansit-pages-${VERSION}`;
const OFFLINE_URL = "/offline";
const PRECACHE = [
  "/",
  "/listen",
  "/reciters",
  "/mushaf",
  "/history",
  "/settings",
  OFFLINE_URL,
  "/icons/icon-192.png",
];
const MAX_PAGES = 80;

/** Store a page and the build assets it needs, so it can run offline unvisited. */
async function precachePage(cache, url) {
  const response = await fetch(new Request(url, { cache: "reload" }));
  if (!response.ok) return;
  await cache.put(url, response.clone());
  const type = response.headers.get("content-type") || "";
  if (!type.includes("text/html")) return;
  const html = await response.text();
  const assets = new Set(html.match(/\/_next\/static\/[^"'\\\s)<>]+/g) || []);
  await Promise.all(
    [...assets].map((asset) => cache.add(asset).catch(() => undefined)),
  );
}

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(SHELL).then((cache) =>
      // One missing page must not block the offline page from being stored.
      Promise.all(
        PRECACHE.map((url) => precachePage(cache, url).catch(() => undefined)),
      ),
    ),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter(
              (key) =>
                key.startsWith("ansit-") && key !== SHELL && key !== PAGES,
            )
            .map((key) => caches.delete(key)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "SKIP_WAITING") self.skipWaiting();
});

function isStaticAsset(url) {
  return (
    url.pathname.startsWith("/_next/static/") ||
    url.pathname.startsWith("/icons/") ||
    url.pathname === "/manifest.webmanifest"
  );
}

async function trim(cacheName, limit) {
  const cache = await caches.open(cacheName);
  const keys = await cache.keys();
  await Promise.all(
    keys
      .slice(0, Math.max(0, keys.length - limit))
      .map((key) => cache.delete(key)),
  );
}

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  if (response.ok) {
    const cache = await caches.open(SHELL);
    await cache.put(request, response.clone());
  }
  return response;
}

/** Network first; the stored copy, then the offline page, when there is none. */
async function networkFirst(request, { fallbackToOffline }) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(PAGES);
      await cache.put(request, response.clone());
      trim(PAGES, MAX_PAGES);
    }
    return response;
  } catch (error) {
    const cached =
      (await caches.match(request)) ||
      (await caches.match(request, { ignoreSearch: true }));
    if (cached) return cached;
    if (fallbackToOffline) {
      const offline = await caches.match(OFFLINE_URL);
      if (offline) return offline;
    }
    throw error;
  }
}

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (isStaticAsset(url)) {
    event.respondWith(cacheFirst(request));
    return;
  }
  if (request.mode === "navigate") {
    event.respondWith(networkFirst(request, { fallbackToOffline: true }));
    return;
  }
  // Route data fetched by in-app navigation.
  if (request.headers.get("RSC") === "1") {
    event.respondWith(networkFirst(request, { fallbackToOffline: false }));
  }
});
