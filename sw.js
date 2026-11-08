/* 历史长卷 Service Worker
 * 策略：核心资源预缓存（cache-first），跨域字体运行时缓存。
 * 更新 CACHE 版本号即可触发旧缓存清理、客户端下次打开即换新。 */
const CACHE = 'atlas-v1';
const PRECACHE = [
  './',
  './index.html',
  './scroll.css',
  './view-switch.css',
  './scroll-app.js',
  './emperor-data.js',
  './atlas.css',
  './atlas-timeline-ui.css',
  './atlas-app.js',
  './atlas-ui.js',
  './atlas-bridge.js',
  './jiangshan-atlas.html',
  './atlas-dynasty.js',
  './atlas-lore.js',
  './atlas-terrain.webp',
  './js/atlas_snapshots.js',
  './manifest.json',
  './apple-touch-icon.png',
  './icon-512.png',
  './favicon-32.png'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE)
      .then((c) => Promise.allSettled(PRECACHE.map((u) => c.add(u))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.protocol !== 'http:' && url.protocol !== 'https:') return;

  e.respondWith(
    caches.match(req, { ignoreSearch: url.origin !== location.origin }).then((hit) => {
      if (hit) return hit;
      return fetch(req).then((res) => {
        if (res && (res.status === 200 || res.type === 'opaque')) {
          const clone = res.clone();
          caches.open(CACHE).then((c) => c.put(req, clone));
        }
        return res;
      }).catch(() => {
        // 离线且未缓存：导航请求退回长卷首页
        if (req.mode === 'navigate') return caches.match('./index.html');
        return Response.error();
      });
    })
  );
});
