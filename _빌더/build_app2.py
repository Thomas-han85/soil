# -*- coding: utf-8 -*-
"""틈틈봇 앱 빌드 v2 — PMP 틈틈봇 UI 사용

ui_new.html 의 `var CARDS = /*__CARDS__*/[];` 자리에 cards.json 을 끼워 넣는다.
카드 데이터와 화면을 분리해 두어, 카드가 늘어도 UI 파일은 그대로 둔다.

사용: python -X utf8 build_app2.py
"""
import os, io, json, re

HERE = os.path.dirname(os.path.abspath(__file__))
BOT = os.path.dirname(HERE)
UI = os.path.join(HERE, "ui_new.html")
CARDS = os.path.join(BOT, "cards.json")
OUT = os.path.join(BOT, "토질_틈틈봇.html")

ui = io.open(UI, encoding="utf-8").read()
data = json.load(io.open(CARDS, encoding="utf-8"))

MARK = "var CARDS = /*__CARDS__*/[];"
if MARK not in ui:
    # 자리표시자를 조금 다르게 썼을 수 있으니 느슨하게 찾는다
    m = re.search(r"var\s+CARDS\s*=\s*/\*__CARDS__\*/\s*\[\s*\]\s*;", ui)
    if not m:
        raise SystemExit("! ui_new.html 에 카드 자리표시자가 없습니다")
    MARK = m.group(0)

payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
ui = ui.replace(MARK, "var CARDS = %s;" % payload, 1)

# 화면 판번호 — 카드를 뺀 나머지(=화면 자체)의 지문.
# 이게 달라져야 앱이 화면을 갈아 끼운다. 카드만 바뀌면 화면은 그대로 둔다.
import hashlib, datetime
shell = io.open(UI, encoding="utf-8").read().replace(MARK, "")
sig = hashlib.sha1(shell.encode("utf-8")).hexdigest()[:7]
stamp = datetime.date.today().strftime("%m%d") + "-" + sig
if "__UI_BUILD__" not in ui:
    raise SystemExit("! ui_new.html 에 __UI_BUILD__ 자리가 없습니다")
ui = ui.replace("__UI_BUILD__", stamp)

io.open(OUT, "w", encoding="utf-8").write(ui)

from collections import Counter
cs = data["cards"]
print("✔ 토질_틈틈봇.html  %d bytes" % len(ui))
print("   카드 %d장 · ver %d · 화면 %s" % (len(cs), data.get("ver", 0), stamp))
print("   장별:", dict(Counter(c["ch"] for c in cs)))
print("   유형:", dict(Counter(c["type"] for c in cs)))
print("   절 %d개" % len(set(c["sec"] for c in cs)))

# ── 배포 ───────────────────────────────────────────────────────────
# index.html 이 실제로 배포되는 파일이다. 껍데기(안드로이드)는 이 파일을
# 원격에서 받아 쓰므로, 여기까지 해야 폰에 새 UI가 뜬다.
import shutil

ROOTS = [os.path.join(BOT, "index.html"),
         os.path.join(BOT, "android", "app", "src", "main", "assets", "index.html")]
for p in ROOTS:
    if os.path.isdir(os.path.dirname(p)):
        shutil.copy(OUT, p)
        print("   → %s" % os.path.relpath(p, BOT))

# 첫 실행용 씨앗 카드도 같이 (앱은 켜지면 원격에서 다시 받는다)
seed = os.path.join(BOT, "android", "app", "src", "main", "assets", "cards.json")
if os.path.isdir(os.path.dirname(seed)):
    shutil.copy(CARDS, seed)
    print("   → android assets/cards.json (씨앗 %d장)" % len(cs))

# 서비스워커 캐시 판번호 — 올려야 PWA 가 옛 화면을 붙들지 않는다
sw = os.path.join(BOT, "sw.js")
if os.path.exists(sw):
    t = io.open(sw, encoding="utf-8").read()
    m = re.search(r"var VER = 'toji-bot-v(\d+)'", t)
    if m:
        v = int(m.group(1)) + 1
        t = t.replace(m.group(0), "var VER = 'toji-bot-v%d'" % v)
        io.open(sw, "w", encoding="utf-8", newline="\n").write(t)
        print("   → sw.js 캐시 v%d" % v)
