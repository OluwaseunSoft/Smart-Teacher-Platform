const CACHE = "suhail-v2";
const PRECACHE = ["/", "/index.html", "/manifest.webmanifest", "/icon.svg"];
const FALLBACK_HTML = "/index.html";

function cacheResponse(request, response) {
  if (!response || response.status !== 200 || response.type !== "basic") {
    return;
  }

  const copy = response.clone();
  caches.open(CACHE).then((cache) => cache.put(request, copy));
}

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE)
      .then((cache) => cache.addAll(PRECACHE))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys.filter((key) => key !== CACHE).map((key) => caches.delete(key)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (url.pathname.startsWith("/api/")) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.ok) cacheResponse(request, response);
          return response;
        })
        .catch(() => caches.match(request).then((cached) => cached || new Response(null, { status: 503 }))),
    );
    return;
  }

  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.ok) cacheResponse(request, response);
          return response;
        })
        .catch(() => caches.match(FALLBACK_HTML)),
    );
    return;
  }

  event.respondWith(
    caches.match(request).then((cached) => {
      const fetched = fetch(request)
        .then((response) => {
          if (response.ok) cacheResponse(request, response);
          return response;
        })
        .catch(() => cached || caches.match(FALLBACK_HTML));

      return cached || fetched;
    }),
  );
});
