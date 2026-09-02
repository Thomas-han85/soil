# -*- coding: utf-8 -*-
"""새 UI 손질 ② — 풀던 자리에서 이어가기

지금까지는 장만 기억했다. 앱을 다시 열면 그 장으로 들어가긴 하는데
칩(유형·절)은 풀려 버리고, 카드도 새로 뽑아 버려서 보던 카드가 사라졌다.

고침
  ① 「자리」 = 장 + 유형칩 + 절칩 + 지금 보던 카드 id + 정답을 봤는지
     이 넷을 한 덩어리로 저장한다 (toji_spot)
  ② 카드를 넘기거나 칩을 건드릴 때마다 자리를 갱신한다
  ③ 앱을 열면 그 자리를 그대로 복원한다. 보던 카드까지 다시 띄운다.
     그 카드가 사라졌거나(갱신으로) 조합이 비면 그때만 새로 뽑는다.
  ④ 장 선택 화면은 「한 번도 고른 적이 없을 때」만 먼저 뜬다.
     그 뒤로는 햄버거(☰)나 장 이름을 눌러야 나온다.
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


# ── ① 자리 저장·복원 함수
OLD = """  clearFilter: function(){
    this.fSec = ''; this.fTag = '';
    this.buildChips(); this.render();
  },
"""
NEW = """  clearFilter: function(){
    this.fSec = ''; this.fTag = '';
    this.buildChips(); this.render();
  },

  /* ---------- 풀던 자리 ----------
     장만 기억하면 다시 열었을 때 보던 카드가 사라진다.
     장·칩·카드·정답표시까지 한 덩어리로 남긴다. */
  saveSpot: function(){
    if(LOCK) return;                       /* 잠금화면은 자리를 건드리지 않는다 */
    try{
      Store.set('toji_spot', JSON.stringify({
        ch:  this.fCh,
        sec: this.fSec,
        tag: this.fTag,
        id:  this.cur ? this.cur.id : '',
        sh:  this.shown ? 1 : 0
      }));
    }catch(e){}
  },

  loadSpot: function(){
    try{ return JSON.parse(Store.get('toji_spot') || 'null'); }catch(e){ return null; }
  },

  /* 저장된 자리로 되돌아간다. 성공하면 true */
  resume: function(){
    var sp = this.loadSpot();
    if(!sp) return false;
    this.fCh = sp.ch || '';
    this.fSec = sp.sec || '';
    this.fTag = sp.tag || '';
    /* 장이 통째로 사라졌으면(카드 갱신) 자리를 버린다 */
    if(this.fCh && !DATA.some(function(c){ return c.ch === sp.ch; })) return false;
    /* 칩 조합이 비어 있으면 칩만 푼다 — 장은 살린다 */
    if(!this.pool().length){ this.fSec = ''; this.fTag = ''; }
    if(!this.pool().length){ this.fCh = ''; }
    if(!this.pool().length) return false;

    this.openBoard();
    this.hist = [];
    this.buildChips();

    var self = this;
    var card = sp.id ? DATA.filter(function(c){
      return c.id === sp.id && (!self.fCh || c.ch === self.fCh);
    })[0] : null;
    this.render(card || undefined);
    if(card && sp.sh) this.reveal();
    return true;
  },

  /* 카드 화면 켜기 — startCh 와 resume 이 같이 쓴다 */
  openBoard: function(){
    document.getElementById('menu').classList.remove('show');
    document.getElementById('cardBox').style.display = '';
    document.querySelector('.nav').style.display = '';
    document.getElementById('chipsTag').style.display = '';
    document.getElementById('chipsSec').style.display = '';
  },
"""
sub(OLD, NEW, "saveSpot / loadSpot / resume / openBoard 추가")


# ── ② startCh 를 openBoard 로 정리
OLD2 = """    Store.set('toji_ch', ch);
    document.getElementById('menu').classList.remove('show');
    document.getElementById('cardBox').style.display = '';
    document.querySelector('.nav').style.display = '';
    document.getElementById('chipsTag').style.display = '';
    document.getElementById('chipsSec').style.display = '';
    this.hist = [];
    this.buildChips();
    this.render();
  },"""
NEW2 = """    Store.set('toji_ch', ch);
    this.openBoard();
    this.hist = [];
    this.buildChips();
    this.render();
  },"""
sub(OLD2, NEW2, "startCh 정리")


# ── ③ 카드가 바뀔 때마다 자리 갱신
OLD3 = """    document.getElementById('tZoom').classList.toggle('on', !!(c.qsvg || c.svg));
    this.stats();
  },"""
NEW3 = """    document.getElementById('tZoom').classList.toggle('on', !!(c.qsvg || c.svg));
    this.stats();
    this.saveSpot();
  },"""
sub(OLD3, NEW3, "render() 끝에서 자리 저장")

OLD4 = """    document.getElementById('big').style.display = 'none';
    document.getElementById('grade').classList.add('show');
    r.scrollIntoView({ behavior:'smooth', block:'nearest' });
  },"""
NEW4 = """    document.getElementById('big').style.display = 'none';
    document.getElementById('grade').classList.add('show');
    r.scrollIntoView({ behavior:'smooth', block:'nearest' });
    this.saveSpot();
  },"""
sub(OLD4, NEW4, "정답을 본 상태도 저장")

# 빈 화면일 때도 자리는 남긴다 (칩 조합을 그대로 되살리려고)
OLD5 = """      document.getElementById('big').style.display = 'none';
      this.stats();
      return;"""
NEW5 = """      document.getElementById('big').style.display = 'none';
      this.stats();
      this.saveSpot();
      return;"""
sub(OLD5, NEW5, "빈 화면에서도 칩 자리 저장")


# ── ④ 시작할 때 자리부터 되살린다
OLD6 = """      var last = Store.get('toji_ch');
      if(last === null){ this.openMenu(); }
      else {
        this.fCh = last;
        if(this.pool().length) this.startCh(last, true);
        else this.openMenu();
      }"""
NEW6 = """      /* 풀던 자리가 있으면 그대로 되살린다 — 장 선택 화면은 건너뛴다.
         한 번도 장을 고른 적이 없을 때만 선택 화면으로 시작한다. */
      if(!this.resume()){
        var last = Store.get('toji_ch');
        if(last !== null && (this.fCh = last, this.pool().length)) this.startCh(last, true);
        else { this.fCh = ''; this.openMenu(); }
      }"""
sub(OLD6, NEW6, "시작 시 자리 복원 우선")


# ── ⑤ 카드가 갱신돼도 보던 자리를 잃지 않게
OLD7 = "          if(document.getElementById('menu').classList.contains('show')) self.openMenu();"
NEW7 = ("          if(document.getElementById('menu').classList.contains('show')) self.openMenu();\n"
        "          else self.resume();   /* 갱신 후에도 보던 카드로 돌아온다 */")
sub(OLD7, NEW7, "카드 갱신 뒤에도 자리 유지")

io.open(P, "w", encoding="utf-8").write(s)
print("\n✔ ui_new.html  %d → %d bytes (+%d)" % (n0, len(s), len(s) - n0))
