# -*- coding: utf-8 -*-
"""1교시 용어답안 틀 카드를 틈틈봇에 붙인다.

지금 카드 1,460장은 전부 낭독본에서 뽑은 것이라 「아는가」를 묻는다.
그런데 1교시에서 잃는 점수는 몰라서가 아니다 — 128회에서 10문제를 다 골라 쓰고도
문항마다 10점 만점에 3.7~7.3점을 받았다. 0점도 만점도 없이 전부 절반이다.
한 페이지를 무엇으로 채울지가 정해져 있지 않아서다.

게다가 기출 1교시 용어 766개 중 96%가 딱 한 번 나오고 다시 안 나온다.
그래서 용어를 외우는 카드가 아니라, **처음 보는 용어를 유형으로 알아보고
틀을 꺼내 쓰는** 카드를 붙인다.

카드는 「1교시 용어 틀」이라는 별도의 장으로 들어간다 —
낭독본 13개 장과 섞이면 공부하는 성격이 달라 서로 방해가 된다.

사용: python -X utf8 add_frames.py
"""
import os, io, json

HERE = os.path.dirname(os.path.abspath(__file__))
BOT = os.path.dirname(HERE)
SRC = os.path.join(os.path.dirname(os.path.dirname(BOT)),
                   "with AI", "차량학습_이론서", "_빌더", "_용어틀.json")
CARDS = os.path.join(BOT, "cards.json")
CH = "1교시 용어 틀"


def bar(xs):
    return "|".join(xs)


def build(f):
    """틀 하나 → 카드 두 장 (틀 꺼내기 / 대비축 고르기)"""
    out = []
    fid, ty = f["id"], f["type"]
    frame = bar(f.get("frame", []))
    must = " · ".join(f.get("must", []))
    axis = f.get("axis", [])

    # ① 틀 꺼내기 — 유형을 보고 다섯 칸을 말할 수 있나
    q = "**%s**\n\n%s\n\n이 유형의 답안 뼈대를 말해 보세요." % (ty, f.get("when", ""))
    a = frame
    if must:
        a += "|**반드시** " + must
    if f.get("trap"):
        a += "|⚠ " + f["trap"]
    out.append({"id": fid + "-F", "ch": CH, "sec": ty, "type": "frame",
                "q": q, "a": a, "tag": "용어", "src": fid})

    # ② 대비축 — 이 카드의 핵심. 처음 보는 용어를 무엇과 대비시킬 것인가
    if axis:
        out.append({"id": fid + "-A", "ch": CH, "sec": ty, "type": "frame",
                    "q": "**%s**\n\n%s\n\n이 유형에서 쓸 수 있는 **대비축**을 들어 보세요."
                         % (ty, f.get("cue", "대비축이 없으면 줄글이 되고 반쪽이 됩니다.")),
                    "a": bar(["· " + x for x in axis]
                             + (["", "보기 — " + f["example"]] if f.get("example") else [])),
                    "tag": "용어", "src": fid})
    return out


def main():
    if not os.path.exists(SRC):
        raise SystemExit("! 아직 _용어틀.json 이 없습니다: %s" % SRC)
    frames = json.load(io.open(SRC, encoding="utf-8"))
    new = []
    for f in frames:
        new += build(f)

    d = json.load(io.open(CARDS, encoding="utf-8"))
    # 다시 돌려도 겹치지 않게 — 이 장 카드는 통째로 갈아 끼운다
    keep = [c for c in d["cards"] if c.get("ch") != CH]
    d["cards"] = keep + new
    d["ver"] = int(d.get("ver", 0)) + 1
    json.dump(d, io.open(CARDS, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))

    print("✔ cards.json  ver %d · 카드 %d장" % (d["ver"], len(d["cards"])))
    print("   틀 %d개 → 용어 카드 %d장 (낭독본 카드 %d장은 그대로)"
          % (len(frames), len(new), len(keep)))
    for f in frames:
        print("     %-4s %s" % (f["id"], f["type"]))


main()
