# -*- coding: utf-8 -*-
"""틈틈봇 카드 빌더 — 낭독본에서 학습 카드 추출

카드 유형 (우선순위 순)
  answer  : 기출 문제 → 답안에 넣을 것 (🖼️공식·그림·살·⚖만점조건)  ★ 가장 중요
  formula : 공식 하나 = 카드 하나                                ★ 암기 대상
  figure  : 시험작도용 그림 (SVG + 작도 요령)                      ★ 암기 대상
  recall  : 인출 프롬프트
  sal     : 살 서술
  table   : 비교표

사용: python -X utf8 build_cards.py
"""
import os, re, io, json, html

HERE = os.path.dirname(os.path.abspath(__file__))
BOT = os.path.dirname(HERE)
ROOT = os.path.dirname(BOT)
CHDIR = os.path.join(ROOT, "차량학습_이론서")

def clean(x):
    x = re.sub(r"<br\s*/?>", " / ", x)
    x = re.sub(r"<[^>]+>", "", x)
    return re.sub(r"\s+", " ", html.unescape(x)).replace("&nbsp;", " ").strip()

def bold(x):
    """굵게만 ** 로 남긴다 — 카드에서 핵심어 강조"""
    x = re.sub(r"<br\s*/?>", "|", x)
    x = re.sub(r"</?(b|strong)>", "**", x)
    x = re.sub(r"<[^>]+>", "", x)
    x = html.unescape(x).replace("&nbsp;", " ")
    return re.sub(r"[ \t]+", " ", x).strip()

CARDS = []
CHAPTERS = [("01", "제1장 흙의 성질", "01_흙의성질.html")]

for chno, chname, fn in CHAPTERS:
    p = os.path.join(CHDIR, fn)
    if not os.path.exists(p):
        print("  ! 없음:", fn); continue
    s = io.open(p, encoding="utf-8").read()
    b = re.sub(r"<script>.*?</script>", "", s.split("</style>", 1)[1], flags=re.S)

    secs = []
    for m in re.finditer(r'<section id="([^"]+)">(.*?)</section>', b, re.S):
        t = re.search(r"<h2[^>]*>(.*?)</h2>", m.group(2), re.S)
        title = re.sub(r"^\d+[a-z]?", "", clean(t.group(1)) if t else m.group(1)).strip()
        secs.append((m.group(1), title, m.group(2)))
    n = [0]
    def nid(k):
        n[0] += 1
        return "%s-%s%02d" % (chno, k, n[0])

    # ───────────── ① 기출 → 넣을 것  (§11 skel 블록)
    for sid, stitle, body in secs:
        if "실제 기출" not in stitle: continue
        for m in re.finditer(r'<div class="skel sp"[^>]*>(.*?)</div>', body, re.S):
            inner = m.group(1)
            lab = re.search(r'class="lab">(.*?)</span>', inner, re.S)
            if not lab: continue
            head = clean(lab.group(1))                       # 예: G1 · 점토광물 · 동형치환 · 판별법
            rest = re.sub(r'<span class="lab">.*?</span>', "", inner, flags=re.S)
            _c = clean(rest)
            _m = re.search(r"대표\s*기출\s*[—-]\s*(\d+)\s*회\s*(\d+)\s*교시\s*(\d+)\s*번", _c)
            code = ("%s회 %s교시 %s번" % _m.groups()) if _m else ""
            # 항목별로 쪼갠다 (🖼️ 🔢 🔧 ⚖)
            items = []
            for ln in re.split(r"<br\s*/?>|</div>|\n", rest):
                t = bold(ln)
                if len(t) > 6 and re.match(r"^[🖼🔢🔧⚖📖]", t): items.append(t)
            if not items:
                t = bold(rest)
                t = re.sub(r"^대표 기출.*?(?=[🖼🔢🔧⚖📖])", "", t)
                items = [x for x in re.split(r"(?=[🖼🔢🔧⚖📖])", t) if len(x.strip()) > 6]
            if not items: continue
            body_txt = "|".join(x.strip() for x in items)
            topic = " · ".join(x.strip() for x in head.split("·")[1:]).strip() or head
            if code:
                q = "[%s] %s\n\n이 문제, 답안에 무엇을 넣습니까?" % (code, topic)
            else:
                q = "%s\n\n답안에 무엇을 넣습니까?" % topic
            CARDS.append({"id": nid("A"), "ch": chname, "sec": "기출→넣을 것",
                          "type": "answer", "q": q, "a": body_txt,
                          "tag": "기출", "src": sid, "axis": head.split("·")[0].strip()})

    # ───────────── ② 공식
    for sid, stitle, body in secs:
        for m in re.finditer(r'<div class="fx sp"[^>]*>(.*?)</div>', body, re.S):
            t = bold(m.group(1))
            t = re.sub(r"^▸[^|]*\|", "", t).strip()
            if len(t) < 8: continue
            lines = [x.strip() for x in t.split("|") if x.strip()]
            head = lines[0]
            # 제목처럼 생긴 첫 줄이면 질문으로, 아니면 절 이름으로
            if len(lines) > 1 and ("—" in head or head.endswith("다") or head.endswith("준")):
                q = "%s — 식을 써 보세요" % head.split("—")[0].strip()
                a = "|".join(lines[1:])
            else:
                q = "%s — 관련 식을 써 보세요" % stitle.split("—")[0].strip()
                a = "|".join(lines)
            CARDS.append({"id": nid("F"), "ch": chname, "sec": stitle,
                          "type": "formula", "q": q, "a": a, "tag": "공식", "src": sid})

    # ───────────── ③ 그림 (SVG 그대로 담는다)
    for sid, stitle, body in secs:
        for m in re.finditer(r"<figure>(.*?)</figure>", body, re.S):
            inner = m.group(1)
            num = re.search(r'fignum">(.*?)</span>', inner, re.S)
            svg = re.search(r"(<svg.*?</svg>)", inner, re.S)
            cap = re.search(r"<figcaption[^>]*>(.*?)</figcaption>", inner, re.S)
            if not (num and svg): continue
            title = clean(num.group(1))
            CARDS.append({"id": nid("G"), "ch": chname, "sec": stitle,
                          "type": "figure",
                          "q": "%s\n\n백지에 그려 보세요." % title,
                          "a": bold(cap.group(1)) if cap else "",
                          "svg": svg.group(1), "tag": "그림", "src": sid})

    # ───────────── ④ 인출 프롬프트
    for sid, stitle, body in secs:
        for m in re.finditer(r'<div class="rc">(.*?)</details>\s*</div>', body, re.S):
            q = re.search(r'class="sp rq"[^>]*>(.*?)</span>', m.group(1), re.S)
            a = re.search(r'class="sp ra"[^>]*>(.*?)</span>', m.group(1), re.S)
            if not (q and a): continue
            CARDS.append({"id": nid("R"), "ch": chname, "sec": stitle,
                          "type": "recall", "q": clean(q.group(1)), "a": bold(a.group(1)),
                          "tag": "인출", "src": sid})

    # ───────────── ⑤ 살 / 갭B
    for sid, stitle, body in secs:
        if "실제 기출" in stitle: continue
        for m in re.finditer(r'<div class="(sal|gapb) sp"[^>]*>(.*?)</div>', body, re.S):
            inner = m.group(2)
            lab = re.search(r'class="lab">(.*?)</span>', inner, re.S)
            if not lab: continue
            label = clean(lab.group(1))
            content = bold(re.sub(r'<span class="lab">.*?</span>', "", inner, flags=re.S))
            if len(content) < 25: continue
            mm = re.search(r"[—-]\s*(.+)$", label)
            head = re.sub(r"\(.*?\)$", "", mm.group(1) if mm else label).strip()
            CARDS.append({"id": nid("S"), "ch": chname, "sec": stitle, "type": "sal",
                          "q": head if head.endswith("?") else "%s — 설명해 보세요" % head,
                          "a": content, "tag": "살" if m.group(1) == "sal" else "갭B", "src": sid})

    # ───────────── ⑥ 비교표
    for sid, stitle, body in secs:
        for m in re.finditer(r"<table>(.*?)</table>", body, re.S):
            hdr = [clean(h) for h in re.findall(r"<th[^>]*>(.*?)</th>", m.group(1), re.S)]
            rows = []
            for r in re.findall(r"<tr>(.*?)</tr>", m.group(1), re.S):
                cs = [clean(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
                if cs: rows.append(cs)
            if len(rows) < 2: continue
            head = " vs ".join(hdr[1:3]) if len(hdr) >= 3 else (hdr[0] if hdr else stitle)
            a = ("**" + " | ".join(hdr) + "**||" if hdr else "") + "||".join("|".join(r) for r in rows[:9])
            CARDS.append({"id": nid("T"), "ch": chname, "sec": stitle, "type": "table",
                          "q": "%s — 비교표를 채워 보세요" % head, "a": a, "tag": "비교표", "src": sid})

# 우선순위 정렬 — 기출·공식·그림이 먼저
ORDER = {"answer": 0, "formula": 1, "figure": 2, "recall": 3, "table": 4, "sal": 5}
CARDS.sort(key=lambda c: (ORDER.get(c["type"], 9), c["id"]))

out = os.path.join(BOT, "cards.json")
json.dump({"ver": 2, "built": "2026-08-26", "cards": CARDS},
          io.open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

from collections import Counter
print("✔ cards.json  카드 %d장" % len(CARDS))
print("   유형:", dict(Counter(c["type"] for c in CARDS)))
print("   태그:", dict(Counter(c["tag"] for c in CARDS)))
