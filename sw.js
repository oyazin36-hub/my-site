// ============================================================
// Service Worker - オフライン対応 & アプリ化(PWA)
// ============================================================
const CACHE = 'chohyo-v1';
const ASSETS = [
  './',
  './index.html',
  './css/style.css',
  './js/config.js',
  './js/forms/purchase.js',
  './js/app.js',
  './manifest.json',
  './icons/icon-192.png',
  './icons/icon-512.png',
];

// インストール: アプリ本体をキャッシュ
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

// 有効化: 古いキャッシュを掃除
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// 取得: アプリ本体はキャッシュ優先、データ通信(GAS)は常にネットワーク
self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = req.url;

  // GAS へのデータ通信・POST はキャッシュしない
  if (req.method !== 'GET' || url.includes('script.google') || url.includes('googleusercontent')) {
    return; // ブラウザ既定のネットワーク処理に任せる
  }

  event.respondWith(
    caches.match(req).then((cached) => {
      if (cached) return cached;
      return fetch(req)
        .then((res) => {
          // 同一オリジンの取得結果は動的にキャッシュ
          if (res && res.status === 200 && url.startsWith(self.location.origin)) {
            const copy = res.clone();
            caches.open(CACHE).then((c) => c.put(req, copy));
          }
          return res;
        })
        .catch(() => cached);
    })
  );
});
