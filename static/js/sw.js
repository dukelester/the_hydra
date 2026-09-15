const CACHE_PAGES = "hydra-pages-v1";
const CACHE_ASSETS = "hydra-assets-v1";
const OFFLINE_URL = "/offline/";
const PRECACHE = [
  "/",
  OFFLINE_URL,
  "/static/css/app.css",
  "/static/js/nav.js",
  "/static/js/offline.js",
  "/static/img/mark.png",
];
const PAGE_LIMIT = 80;

function isBypass(url) {
  return (
    url.pathname.startsWith("/admin") ||
    url.pathname.startsWith("/admin_dashboard") ||
    url.pathname.startsWith("/media/") ||
    url.pathname.startsWith("/i18n/") ||
    url.pathname.startsWith("/access/") ||
    url.pathname.startsWith("/api/")
  );
}

async function trimPages() {
  const cache = await caches.open(CACHE_PAGES);
  const keys = await cache.keys();
  if (keys.length <= PAGE_LIMIT) {
    return;
  }
  await Promise.all(keys.slice(0, keys.length - PAGE_LIMIT).map(function (request) {
    return cache.delete(request);
  }));
}

async function fromNetwork(request) {
  const response = await fetch(request);
  if (response && response.ok && request.method === "GET") {
    const copy = response.clone();
    const cacheName = new URL(request.url).pathname.startsWith("/static/")
      ? CACHE_ASSETS
      : CACHE_PAGES;
    const cache = await caches.open(cacheName);
    await cache.put(request, copy);
    if (cacheName === CACHE_PAGES) {
      await trimPages();
    }
  }
  return response;
}

async function networkFirst(request) {
  try {
    return await fromNetwork(request);
  } catch (error) {
    const cached = await caches.match(request);
    if (cached) {
      return cached;
    }
    if (request.mode === "navigate") {
      const offline = await caches.match(OFFLINE_URL);
      if (offline) {
        return offline;
      }
    }
    throw error;
  }
}

async function staleWhileRevalidate(request) {
  const cached = await caches.match(request);
  const network = fromNetwork(request).catch(function () {
    return cached;
  });
  return cached || network;
}

self.addEventListener("install", function (event) {
  event.waitUntil(
    (async function () {
      const assets = await caches.open(CACHE_ASSETS);
      const pages = await caches.open(CACHE_PAGES);
      const assetUrls = PRECACHE.filter(function (url) {
        return url.startsWith("/static/");
      });
      const pageUrls = PRECACHE.filter(function (url) {
        return !url.startsWith("/static/");
      });
      await Promise.all(
        assetUrls.map(function (url) {
          return assets.add(url).catch(function () {});
        }).concat(
          pageUrls.map(function (url) {
            return pages.add(url).catch(function () {});
          })
        )
      );
      await self.skipWaiting();
    })()
  );
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys().then(function (names) {
      return Promise.all(
        names
          .filter(function (name) {
            return name !== CACHE_PAGES && name !== CACHE_ASSETS;
          })
          .map(function (name) {
            return caches.delete(name);
          })
      );
    }).then(function () {
      return self.clients.claim();
    })
  );
});

self.addEventListener("fetch", function (event) {
  const request = event.request;
  if (request.method !== "GET") {
    return;
  }
  const url = new URL(request.url);
  if (url.origin !== self.location.origin || isBypass(url)) {
    return;
  }
  if (request.mode === "navigate") {
    event.respondWith(networkFirst(request));
    return;
  }
  if (url.pathname.startsWith("/static/")) {
    event.respondWith(staleWhileRevalidate(request));
    return;
  }
  event.respondWith(networkFirst(request));
});
