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

def labelize(label, fallback):
    """살 라벨을 카드 주제로 다듬는다. 없거나 너무 길면 절 이름으로 돌아간다."""
    t = re.sub(r"^[^0-9A-Za-z가-힣]+", "", label)      # 앞의 이모지·기호
    t = re.sub(r"^(?:살|답안 골격|갭B)\s*[—-]\s*", "", t)
    t = re.sub(r"^G\d+\s*·\s*", "", t)
    t = re.sub(r"\s*\([^)]*\)\s*$", "", t)            # 끝의 괄호 주석
    t = re.sub(r"[★☆\s]+$", "", t)
    t = t.strip(" ·—-")
    if not t or len(t) > 44: return fallback
    return t

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
CHAPTERS = [("01", "제1장 흙의 성질", "01_흙의성질.html"),
            ("02", "제2장 지중응력", "02_지중응력.html"),
            ("03", "제3장 투수", "03_투수.html"),
            ("04", "제4장 압밀", "04_압밀.html")]

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

    # ───────────── ② 공식 — 본문 전역에서 식 하나씩. 쓰기/알아보기 양방향
    SYM = "γησρφΔΣ√±×÷≤≥≈∝⁰¹²³⁴ₐₑₒₓ₀₁₂₃₄₅₆₇₈₉·−"
    NOTF = ("가른다","이면","판별법","정도","이상","이하","쓴다","본다","한다","된다",
            "라고","이라","경우","때문","따라","니까","습니다","입니다","~","기준","구분")
    def is_formula(t):
        if "=" not in t: return False
        if len(t) < 6 or len(t) > 120: return False
        if t.count("=") > 3: return False
        L, R = t.split("=", 1)
        if len(L.strip()) > 28: return False
        if any(k in t for k in NOTF): return False
        import re as _re
        if _re.search(r"[가-힣]{4,}", R): return False
        return bool(_re.search(r"[+\-−×÷/()·]", R) or _re.search(r"[0-9]", R)
                    or any(c in R for c in SYM))

    seen_f = set()
    for sid, stitle, body in secs:
        # fx 블록 + 살/골격 안의 굵은 식까지
        sec_topic = stitle.split("—")[0].strip()
        chunks = []
        for m in re.finditer(r'<div class="fx sp"[^>]*>(.*?)</div>', body, re.S):
            chunks.append((bold(m.group(1)), sec_topic))
        for m in re.finditer(r'<div class="(?:sal|skel) sp"[^>]*>(.*?)</div>', body, re.S):
            lab = re.search(r'class="lab">(.*?)</span>', m.group(1), re.S)
            lb = labelize(clean(lab.group(1)), sec_topic) if lab else sec_topic
            inner = re.sub(r'<span class="lab">.*?</span>', "", m.group(1), flags=re.S)
            for bm in re.finditer(r"<b>(.*?)</b>", inner, re.S):
                chunks.append((bold(bm.group(1)), lb))
        for raw, lb in chunks:
            raw = re.sub(r"^▸[^|]*\|", "", raw)
            for ln in raw.split("|"):
                t = ln.strip().strip("·").strip()
                t = re.sub(r"^\*\*|\*\*$", "", t).strip()
                if not is_formula(t): continue
                key = re.sub(r"[\s*]", "", t)
                if key in seen_f: continue
                seen_f.add(key)
                lhs = re.sub(r"[*]", "", t.split("=")[0]).strip()
                lhs = re.sub(r"^[★▸]\s*", "", lhs)
                topic = lb
                rhs = t.split("=", 1)[1].strip().strip("·").strip()
                # 좌변을 주고 우변을 채운다 — Se = ? → Gs·w
                CARDS.append({"id": nid("F"), "ch": chname, "sec": stitle, "type": "formula",
                              "q": "[%s]\n\n%s = ?" % (topic, lhs),
                              "a": "**" + t + "**", "tag": "공식", "src": sid})
    # ───────────── ②-b 규칙 · 수치 — 식은 아니지만 외워야 하는 것
    seen_r = set()
    # 숫자 뒤에 단위·비교기호가 붙은 것만 = 외울 값이 있는 조각
    UNITNUM = re.compile(r"(?:[0-9][0-9.,~/]*\s*(?:%|mm|cm|m|μm|Å|℃|kN|kPa|MPa|t/m|g/cm|배|종|개|h|일))|(?:[≥≤<>=]\s*[0-9])|(?:[0-9]+\.[0-9])")
    for sid, stitle, body in secs:
        topic = stitle.split("—")[0].strip()
        # (1) fx 블록 중 식으로 안 잡힌 것 = 분류 규칙표 → 통으로 한 장
        for m in re.finditer(r'<div class="fx sp"[^>]*>(.*?)</div>', body, re.S):
            raw = bold(m.group(1))
            raw = re.sub(r"^▸[^|]*\|", "", raw)
            lines = [x.strip() for x in raw.split("|") if x.strip()]
            if not lines: continue
            if any(is_formula(re.sub(r"^\*\*|\*\*$", "", x).strip()) for x in lines):
                continue                              # 식은 위에서 이미 카드가 됐다
            head = re.sub(r"[*]", "", lines[0]).strip()
            head = re.sub(r"\s*[—-]\s*.*$", "", head).strip() or topic
            key = re.sub(r"[\s*]", "", raw)[:60]
            if key in seen_r: continue
            seen_r.add(key)
            CARDS.append({"id": nid("N"), "ch": chname, "sec": stitle, "type": "rule",
                          "q": "[%s]\n\n%s — 기준을 말해 보세요." % (topic, head),
                          "a": "|".join(lines), "tag": "기준", "src": sid})
        # (2) 살 안의 굵은 조각 중 "외워야 하는 수치" — 단위·비교기호를 동반한 것만
        if "실제 기출" in stitle: continue
        for m in re.finditer(r'<div class="(?:sal|gapb) sp"[^>]*>(.*?)</div>', body, re.S):
            lab = re.search(r'class="lab">(.*?)</span>', m.group(1), re.S)
            if not lab: continue
            label = clean(lab.group(1))
            mm = re.search(r"[—-]\s*(.+)$", label)
            head = re.sub(r"\(.*?\)$", "", mm.group(1) if mm else label).strip()
            inner = re.sub(r'<span class="lab">.*?</span>', "", m.group(1), flags=re.S)
            for bm in re.finditer(r"<b>(.*?)</b>", inner, re.S):
                t = bold(bm.group(1)).replace("**", "").strip(" ·")
                if not (8 <= len(t) <= 110): continue
                if is_formula(t) or t.count("=") > 2: continue
                if any(k in t for k in ("대표 기출", "교시", "회 ", "갈래", "칸 ", "단계")): continue
                if not UNITNUM.search(t): continue
                if t.count("(") != t.count(")"): continue     # 괄호 잘린 조각
                q = re.sub(r"[0-9][0-9.,~/]*", "◻︎", t)
                if len(q.replace("◻︎", "").strip(" ·/=<>≥≤")) < 6: continue
                key = re.sub(r"[\s]", "", q)          # 마스킹 결과가 같으면 중복
                if key in seen_r or key in seen_f: continue
                seen_r.add(key)
                # 살 제목에 답이 이미 적혀 있으면 절 이름으로 바꾼다
                nums = re.findall(r"[0-9][0-9.]*", t)
                hd = topic if (head and any(n in head for n in nums if len(n) > 1)) else (head or topic)
                CARDS.append({"id": nid("N"), "ch": chname, "sec": stitle, "type": "number",
                              "q": "[%s]\n\n이 수치를 채워 보세요.\n\n%s" % (hd, q),
                              "a": "**" + t + "**", "tag": "수치", "src": sid})
    # ───────────── ③ 그림 — 그리기 / 알아보기 양방향
    for sid, stitle, body in secs:
        for m in re.finditer(r"<figure>(.*?)</figure>", body, re.S):
            inner = m.group(1)
            num = re.search(r'fignum">(.*?)</span>', inner, re.S)
            svg = re.search(r"(<svg.*?</svg>)", inner, re.S)
            cap = re.search(r"<figcaption[^>]*>(.*?)</figcaption>", inner, re.S)
            if not (num and svg): continue
            title = clean(num.group(1))
            name = re.sub(r"^그림\s*\d+\s*·\s*", "", title)
            name = re.sub(r"\s*\(.*?\)\s*$", "", name).strip()
            note = bold(cap.group(1)) if cap else ""
            # ⓐ 그리기
            CARDS.append({"id": nid("G"), "ch": chname, "sec": stitle, "type": "figure",
                          "q": "%s\n\n백지에 그려 보세요." % name,
                          "a": note, "svg": svg.group(1), "tag": "그림", "src": sid})
            # ⓑ 알아보기 — 그림을 먼저 보여주고 무엇인지
            CARDS.append({"id": nid("G"), "ch": chname, "sec": stitle, "type": "figure_id",
                          "q": "이 그림은 무엇입니까?",
                          "qsvg": svg.group(1),
                          "a": "**%s**|%s" % (title, note), "tag": "그림", "src": sid})

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
import datetime as _dt
STAMP = _dt.date.today().isoformat()

# ── 수록 범위 : 수식 · 그림 · 개념 리뷰 질문 셋만
#    나머지(살·답안골격·수치·기준·비교표)는 뽑는 코드를 남겨 두되 넣지 않는다.
#    낭독본으로 흐름을 잡고, 틈틈봇은 손이 기억해야 하는 것만 묻는다.
KEEP = {"formula", "figure", "figure_id", "recall"}
CARDS = [c for c in CARDS if c["type"] in KEEP]

ORDER = {"answer": 0, "formula": 1, "figure": 2, "figure_id": 2,
         "number": 3, "rule": 4, "recall": 5, "table": 6, "sal": 7}
CARDS.sort(key=lambda c: (ORDER.get(c["type"], 9), c["id"]))

out = os.path.join(BOT, "cards.json")
prev = 0
try:
    prev = json.load(io.open(out, encoding="utf-8")).get("ver", 0)
except Exception:
    pass
VER = prev + 1                      # 내용이 줄어드는 갱신도 있으니 번호는 무조건 올린다
json.dump({"ver": VER, "built": STAMP, "cards": CARDS},
          io.open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

from collections import Counter
print("✔ cards.json  v%d · 카드 %d장" % (VER, len(CARDS)))
print("   유형:", dict(Counter(c["type"] for c in CARDS)))
print("   태그:", dict(Counter(c["tag"] for c in CARDS)))
