const CACHE_NAME = 'weatherassist-v1';
const urlsToCache = [
  '/',
  '/static/manifest.json',
  '/static/logologo192.png', 
  '/static/logologo512.png'
];

// 1. osyaları hafızaya (cache) al
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Dosyalar önbelleğe alındı');
        return cache.addAll(urlsToCache);
      })
  );
});

// 2. İnternet yoksa hafızadakini göster
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        return response || fetch(event.request);
      })
  );
});

// 3. Eski önbellekleri temizle
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.filter(cacheName => {
          return cacheName !== CACHE_NAME;
        }).map(cacheName => {
          return caches.delete(cacheName);
        })
      );
    })
  );
});