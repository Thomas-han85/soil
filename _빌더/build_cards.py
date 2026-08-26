# -*- coding: utf-8 -*-
"""틈틈봇 카드 빌더 — 낭독본의 【살】과 인출 프롬프트를 학습 카드로 변환

출력: 틈틈봇/cards.json
  [{id, ch, sec, type, q, a, tag, src}]
    type : recall(인출 프롬프트) · sal(살 → 빈칸/단답) · table(비교표)
사용: python -X utf8 build_cards.py
"""
import os, re, io, json, html

HERE = os.path.dirname(os.path.abspath(__file__))
BOT = os.path.dirname(HERE)
ROOT = os.path.dirname(BOT)
CH = os.path.join(ROOT, "차량학습_이론서")

def clean(x):
    x = re.sub(r"<br\s*/?>", " / ", x)
    x = re.sub(r"<[^>]+>", "", x)
    x = html.unescape(x)
    return re.sub(r"\s+", " ", x).replace("&nbsp;", " ").strip()

def keep_bold(x):
    """굵게만 남기고 나머지 태그 제거 — 카드에서 핵심어 강조 유지"""
    x = re.sub(r"<br\s*/?>", "|", x)
    x = re.sub(r"</?b>", "**", x)
    x = re.sub(r"</?strong>", "**", x)
    x = re.sub(r"<[^>]+>", "", x)
    x = html.unescape(x)
    return re.sub(r"[ \t]+", " ", x).replace("&nbsp;", " ").strip()

CARDS = []
CHAPTERS = [("01", "제1장 흙의 성질", "01_흙의성질.html")]

for chno, chname, fn in CHAPTERS:
    p = os.path.join(CH, fn)
    if not os.path.exists(p):
        print("  ! 없음:", fn); continue
    s = io.open(p, encoding="utf-8").read()
    b = re.sub(r"<script>.*?</script>", "", s.split("</style>", 1)[1], flags=re.S)

    # 절 경계
    secs = []
    for m in re.finditer(r'<section id="([^"]+)">(.*?)</section>', b, re.S):
        t = re.search(r"<h2[^>]*>(.*?)</h2>", m.group(2), re.S)
        title = clean(t.group(1)) if t else m.group(1)
        title = re.sub(r"^\d+[a-z]?", "", title).strip()
        secs.append((m.group(1), title, m.group(2)))

    n = 0
    for sid, stitle, body in secs:
        # ① 인출 프롬프트 → recall 카드
        for m in re.finditer(r'<div class="rc">(.*?)</details>\s*</div>', body, re.S):
            q = re.search(r'class="sp rq"[^>]*>(.*?)</span>', m.group(1), re.S)
            a = re.search(r'class="sp ra"[^>]*>(.*?)</span>', m.group(1), re.S)
            if not (q and a): continue
            n += 1
            CARDS.append({"id": "%s-R%02d" % (chno, n), "ch": chname, "sec": stitle,
                          "type": "recall", "q": clean(q.group(1)), "a": keep_bold(a.group(1)),
                          "tag": "인출", "src": sid})

        # ② 살 → sal 카드 (라벨을 질문으로, 본문을 답으로)
        for m in re.finditer(r'<div class="(sal|skel|gapb) sp"[^>]*>(.*?)</div>', body, re.S):
            inner = m.group(2)
            lab = re.search(r'class="lab">(.*?)</span>', inner, re.S)
            if not lab: continue
            label = clean(lab.group(1))
            content = keep_bold(re.sub(r'<span class="lab">.*?</span>', "", inner, flags=re.S))
            if len(content) < 25: continue
            # 라벨의 "살 — XXX" 부분을 질문으로
            mm = re.search(r"[—-]\s*(.+)$", label)
            head = mm.group(1).strip() if mm else label
            head = re.sub(r"\(.*?\)$", "", head).strip()
            q = head if head.endswith("?") else ("%s — 말해 보세요" % head)
            n += 1
            kind = {"sal": "살", "skel": "골격", "gapb": "갭B"}[m.group(1)]
            CARDS.append({"id": "%s-S%02d" % (chno, n), "ch": chname, "sec": stitle,
                          "type": "sal", "q": q, "a": content, "tag": kind, "src": sid})

        # ③ 비교표 → table 카드
        for m in re.finditer(r"<table>(.*?)</table>", body, re.S):
            hdr = re.findall(r"<th[^>]*>(.*?)</th>", m.group(1), re.S)
            rows = re.findall(r"<tr>(?!.*<th)(.*?)</tr>", m.group(1), re.S)
            if len(hdr) < 2 or len(rows) < 2: continue
            cells = []
            for r in rows:
                cs = [clean(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
                if cs: cells.append(cs)
            if not cells: continue
            n += 1
            head = " vs ".join(clean(h) for h in hdr[1:3]) if len(hdr) >= 3 else clean(hdr[0])
            lines = ["| " + " | ".join(c) + " |" for c in cells[:9]]
            CARDS.append({"id": "%s-T%02d" % (chno, n), "ch": chname, "sec": stitle,
                          "type": "table", "q": "%s — 비교표를 채워 보세요 (%s)" % (stitle, head),
                          "a": "**" + " | ".join(clean(h) for h in hdr) + "**|" + "|".join(lines),
                          "tag": "비교표", "src": sid})

os.makedirs(BOT, exist_ok=True)
out = os.path.join(BOT, "cards.json")
json.dump(CARDS, io.open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

from collections import Counter
c = Counter(x["type"] for x in CARDS)
t = Counter(x["tag"] for x in CARDS)
print("✔ cards.json  카드 %d장" % len(CARDS))
print("   유형:", dict(c))
print("   태그:", dict(t))
print("   절별:", dict(Counter(x["sec"][:14] for x in CARDS)))
