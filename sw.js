/* 토질 틈틈봇 — 오프라인 캐시. VER를 올리면 새 버전이 즉시 반영된다. */
var VER = 'toji-bot-v4';
var FILES = ['./', './index.html', './manifest.webmanifest', './icon-192.png', './icon-512.png'];
self.addEventListener('install', function(e){
  self.skipWaiting();
  e.waitUntil(caches.open(VER).then(function(c){ return c.addAll(FILES); }).catch(function(){}));
});
self.addEventListener('activate', function(e){
  e.waitUntil(caches.keys().then(function(ks){
    return Promise.all(ks.filter(function(k){ return k !== VER; }).map(function(k){ return caches.delete(k); }));
  }).then(function(){ return self.clients.claim(); }));
});
self.addEventListener('fetch', function(e){
  if(e.request.method !== 'GET') return;
  /* 네트워크 우선 — 푸시하면 바로 최신본이 뜬다. 실패하면 캐시 */
  e.respondWith(
    fetch(e.request).then(function(r){
      var cp = r.clone();
      caches.open(VER).then(function(c){ c.put(e.request, cp); }).catch(function(){});
      return r;
    }).catch(function(){ return caches.match(e.request); })
  );
});
