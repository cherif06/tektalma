// Service worker : l'interface s'ouvre instantanément (et hors ligne) ; l'API passe toujours par le réseau.
const CACHE = "tektalma-v2";
const SHELL = ["/", "/index.html", "/style.css", "/app.js", "/manifest.json", "/icon.svg", "/icon-192.png", "/icon-512.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys()
    .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin || url.pathname.startsWith("/api/")) return;
  // Réseau d'abord (toujours la dernière version après un déploiement), cache en secours
  e.respondWith(fetch(e.request)
    .then((res) => {
      const copy = res.clone();
      caches.open(CACHE).then((c) => c.put(e.request, copy));
      return res;
    })
    .catch(() => caches.match(e.request).then((r) => r || caches.match("/"))));
});
