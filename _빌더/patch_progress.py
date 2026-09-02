# -*- coding: utf-8 -*-
"""새 UI 손질 ④ — 진도가 실제로 움직이게

실장님: "옆으로 문제 넘겨도 0/70으로 계속 바뀌지 않아.
         이걸 계속 바꿔야지 얼마나 풀었는지 인지하자"

원인
  머리의 숫자는 done() 을 세고 있었다.
      done = 「막힘없이」로 21일 간격까지 통과한 카드
  그런데 채점하면 반드시 다음 복습일이 잡히므로, 21일을 다 통과하기 전에는
  아무리 풀어도 0 이다. 세 주가 지나야 처음으로 1 이 된다.
  진도 표시로는 쓸 수 없는 숫자였다.

고침
  머리 숫자를 「한 번이라도 푼 카드 / 전체」로 바꾼다. 채점할 때마다 오른다.
  옆에 오늘 푼 장수를 따로 붙인다. 오늘 얼마나 했는지가 제일 궁금한 숫자다.
  다 익힌 카드(21일 통과)는 없어지지 않고 ✓ 로 따로 센다.
  장 선택 화면의 막대도 같은 기준으로 바꾼다 — 거기도 0% 로 붙어 있었다.
"""
import io, sys

P = "ui_new.html"
s = io.open(P, encoding="utf-8").read()
n0 = len(s)


def sub(old, new, why):
    global s
    if old not in s:
        sys.exit("! 못 찾음 — %s" % why)
    s = s.replace(old, new, 1)
    print("  ✔ %s" % why)


# ── ① 「푼 카드」와 「다 익힌 카드」를 나눈다
sub("  done: function(c){ var v = this.st(c.id); return !!(v && v.s === 'o' && !v.n); },",
    """  /* 다 익힘 — 「막힘없이」로 21일 간격까지 통과. 세 주는 걸린다 */
  done: function(c){ var v = this.st(c.id); return !!(v && v.s === 'o' && !v.n); },
  /* 푼 것 — 한 번이라도 채점한 카드. 진도는 이걸로 센다 */
  seen: function(c){ return !!this.st(c.id); },""",
    "seen() 추가 — 한 번이라도 푼 카드")


# ── ② 오늘 푼 장수
sub("function save(){ Store.set(LS, JSON.stringify(S)); }",
    """function save(){ Store.set(LS, JSON.stringify(S)); }

/* 오늘 푼 장수 — 날짜가 바뀌면 저절로 0 부터 */
var DAY = { d:'', n:0 };
try{ DAY = JSON.parse(Store.get('toji_day') || 'null') || { d:'', n:0 }; }catch(e){}
function dayN(){ return DAY.d === today() ? DAY.n : 0; }
function dayUp(){
  if(DAY.d !== today()){ DAY.d = today(); DAY.n = 0; }
  DAY.n++;
  try{ Store.set('toji_day', JSON.stringify(DAY)); }catch(e){}
}""",
    "오늘 푼 장수 세기")

sub("""    this.lastSec = c.sec;
    this.sessN++;""",
    """    this.lastSec = c.sec;
    this.sessN++;
    dayUp();""",
    "채점할 때 오늘 장수 올리기")


# ── ③ 머리 숫자를 진도로
sub("""    var nd = p.filter(function(c){ return self.done(c); }).length;
    var ndue = p.filter(function(c){ return self.due(c); }).length;
    var nf = p.filter(function(c){ return self.fresh(c); }).length;
    document.getElementById('sDue').textContent = ndue + nf;
    document.getElementById('sAll').textContent = p.length;
    document.getElementById('hCount').textContent = nd + ' / ' + p.length;
    document.getElementById('verb').textContent = 'v' + VER_LOCAL;""",
    """    var nseen = p.filter(function(c){ return self.seen(c); }).length;
    var nd = p.filter(function(c){ return self.done(c); }).length;
    var ndue = p.filter(function(c){ return self.due(c); }).length;
    var nf = p.filter(function(c){ return self.fresh(c); }).length;
    document.getElementById('sDue').textContent = ndue + nf;
    document.getElementById('sAll').textContent = p.length;
    /* 진도는 「푼 것」으로 센다. 「다 익힘」은 21일이 지나야 오르므로
       하루하루의 진도로는 쓸 수 없다 — 그건 ✓ 로 따로 보여준다 */
    document.getElementById('hCount').innerHTML =
        '<b>' + nseen + '</b><span class="of">/' + p.length + '</span>'
      + '<span class="sub">오늘 ' + dayN() + (nd ? ' · ✓' + nd : '') + '</span>';
    var bar = document.getElementById('hBar');
    if(bar) bar.style.width = (p.length ? (nseen / p.length * 100) : 0) + '%';
    document.getElementById('verb').textContent = 'v' + VER_LOCAL;""",
    "머리 숫자 = 푼 것 / 전체 · 오늘 N · ✓다익힘")


# ── ④ 진도 막대를 카드 머리에
sub("""      <button class="tarrow" id="tnext" onclick="App.skip()">→</button>
    </div>""",
    """      <button class="tarrow" id="tnext" onclick="App.skip()">→</button>
    </div>
    <div class="hbar"><span id="hBar"></span></div>""",
    "카드 머리에 진도 막대")

sub(".cardhead .count{min-width:64px;text-align:center}",
    """.cardhead .count{min-width:64px;text-align:center;line-height:1.15}
.cardhead .count b{font-size:17px;color:var(--accent)}
.cardhead .count .of{font-size:13px}
.cardhead .count .sub{display:block;font-size:10px;font-weight:700;opacity:.7;white-space:nowrap}
.hbar{height:3px;background:var(--line)}
.hbar span{display:block;height:100%;width:0;background:linear-gradient(90deg,var(--accent),#5a9bff);
  border-radius:0 3px 3px 0;transition:width .35s ease}""",
    "진도 막대·숫자 모양")


# ── ⑤ 장 선택 화면 막대도 같은 기준으로
sub("""      var nd = pool.filter(function(x){ return self.done(x); }).length;
      var pct = pool.length ? Math.round(nd / pool.length * 100) : 0;""",
    """      var nd = pool.filter(function(x){ return self.seen(x); }).length;
      var nm = pool.filter(function(x){ return self.done(x); }).length;
      var pct = pool.length ? Math.round(nd / pool.length * 100) : 0;""",
    "장 선택 막대도 「푼 것」 기준")

sub("""        + '<div class="cdone">' + (pool.length && nd >= pool.length ? '✓' : '') + '</div>';""",
    """        + '<div class="cdone">' + (pool.length && nm >= pool.length ? '✓' : '') + '</div>';""",
    "장 선택 ✓ 는 다 익힌 것만")

io.open(P, "w", encoding="utf-8").write(s)
print("\n✔ ui_new.html  %d → %d bytes (+%d)" % (n0, len(s), len(s) - n0))
