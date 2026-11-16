// Çevrimdışı çalışma: oyunlar internet olmadan da açılır; video listesi her seferinde önce internetten denenir.
const SURUM = 'boncuk-v1';
const DOSYALAR = [
  './', 'index.html', 'videolar.html', 'gizlilik.html', 'ortak.css', 'ortak.js', 'videolar.js', 'oyun.css',
  'oyunlar/toplar.html', 'oyunlar/golge.html', 'oyunlar/kule.html',
  'fonts/Baloo2.ttf', 'img/boncuk.png', 'img/boncuk-mutlu.png', 'img/ikon-192.png',
  'img/boncuk-red.png', 'img/boncuk-orange.png', 'img/boncuk-yellow.png', 'img/boncuk-green.png',
  'img/boncuk-blue.png', 'img/boncuk-purple.png', 'img/boncuk-pink.png', 'veri/hayvanlar.json',
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(SURUM).then((c) => c.addAll(DOSYALAR)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((k) => Promise.all(k.filter((a) => a !== SURUM).map((a) => caches.delete(a)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin) return;
  if (url.pathname.endsWith('.json') || url.pathname.includes('/rapor/')) {
    e.respondWith(fetch(e.request).then((r) => { const k = r.clone(); caches.open(SURUM).then((c) => c.put(e.request, k)); return r; }).catch(() => caches.match(e.request)));
    return;
  }
  e.respondWith(caches.match(e.request).then((h) => h || fetch(e.request).then((r) => {
    if (r.ok) { const k = r.clone(); caches.open(SURUM).then((c) => c.put(e.request, k)); }
    return r;
  })));
});
