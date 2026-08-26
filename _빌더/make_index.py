# -*- coding: utf-8 -*-
"""토질_틈틈봇.html → index.html (PWA 태그 + Service Worker 등록 주입)"""
import io, os
HERE = os.path.dirname(os.path.abspath(__file__))
BOT = os.path.dirname(HERE)
s = io.open(os.path.join(BOT, "토질_틈틈봇.html"), encoding="utf-8").read()
s = s.replace("</head>",
  '<link rel="manifest" href="manifest.webmanifest">'
  '<meta name="theme-color" content="#1e3450">'
  '<link rel="apple-touch-icon" href="icon-192.png">'
  '<meta name="apple-mobile-web-app-capable" content="yes">'
  '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">'
  '</head>')
s = s.replace("</body>",
  "<script>if('serviceWorker' in navigator){"
  "window.addEventListener('load',function(){navigator.serviceWorker.register('sw.js').catch(function(){});});}"
  "</script></body>")
p = os.path.join(BOT, "index.html")
io.open(p, "w", encoding="utf-8").write(s)
print("✔ index.html %d bytes" % len(s.encode("utf-8")))
