# -*- coding: utf-8 -*-
"""새 UI 손질 — 빈 조합이 만들어지지 않게 한다.

문제: [유형]과 [절]을 따로 고르다 보면 교집합이 0장인 조합이 생기고,
      그때 화면이 그냥 비어 버린다. (예: 그림 ∩ Darcy = 0장)
      카드가 없으니 App.speak() 도 첫 줄에서 되돌아나가 읽기가 안 된다.

고침 ① 칩마다 장수를 붙이고, 0장이 되는 칩은 눌리지 않게 흐린다.
고침 ② 그래도 빈 화면이 되면 무엇을 풀어야 하는지 알려 주고 되돌리는 버튼을 준다.
"""
import io, re, sys

P = "ui_new.html"
s = io.open(P, encoding="utf-8").read()
n0 = len(s)


def sub(old, new, why):
    global s
    if old not in s:
        sys.exit("! 못 찾음 — %s" % why)
    s = s.replace(old, new, 1)
    print("  ✔ %s" % why)


# ── ① 칩 다시 그리기
OLD = """    var tags = [];
    base.forEach(function(c){ if(tags.indexOf(c.tag) < 0) tags.push(c.tag); });
    tags.sort();
    var tw = document.getElementById('chipsTag');
    tw.innerHTML = '';
    [''].concat(tags).forEach(function(t){
      var b = document.createElement('button');
      b.className = 'chip' + (self.fTag === t ? ' on' : '');
      b.textContent = t ? t : '전체 유형';
      b.onclick = function(){ self.fTag = t; self.buildChips(); self.render(); };
      tw.appendChild(b);
    });

    var secs = [];
    base.forEach(function(c){ if(secs.indexOf(c.sec) < 0) secs.push(c.sec); });
    var sw = document.getElementById('chipsSec');
    sw.innerHTML = '';
    [''].concat(secs).forEach(function(s){
      var b = document.createElement('button');
      b.className = 'chip' + (self.fSec === s ? ' on' : '');
      b.textContent = s ? (s.length > 14 ? s.slice(0, 14) + '…' : s) : '전체';
      b.title = s || '전체';
      b.onclick = function(){ self.fSec = s; self.buildChips(); self.render(); };
      sw.appendChild(b);
    });
"""

NEW = """    /* 한쪽 칩의 장수는 「반대쪽 필터를 건 상태」에서 센다.
       그래야 0장이 될 칩을 미리 알아보고 막을 수 있다. */
    var cnt = function(tag, sec){
      var n = 0;
      for(var i = 0; i < base.length; i++){
        var c = base[i];
        if(tag && c.tag !== tag) continue;
        if(sec && c.sec !== sec) continue;
        n++;
      }
      return n;
    };

    var tags = [];
    base.forEach(function(c){ if(tags.indexOf(c.tag) < 0) tags.push(c.tag); });
    tags.sort();
    var tw = document.getElementById('chipsTag');
    tw.innerHTML = '';
    [''].concat(tags).forEach(function(t){
      var n = cnt(t, self.fSec);
      var b = document.createElement('button');
      b.className = 'chip' + (self.fTag === t ? ' on' : '') + (n ? '' : ' off');
      b.innerHTML = esc(t ? t : '전체 유형') + '<i>' + n + '</i>';
      b.title = (t || '전체 유형') + ' · ' + n + '장';
      if(!n){
        /* 0장인 칩 — 누르면 절 필터를 풀어서 그 유형만 본다 */
        b.onclick = function(){
          self.fTag = t; self.fSec = '';
          self.toast('절 필터를 풀었습니다');
          self.buildChips(); self.render();
        };
      } else {
        b.onclick = function(){ self.fTag = t; self.buildChips(); self.render(); };
      }
      tw.appendChild(b);
    });

    var secs = [];
    base.forEach(function(c){ if(secs.indexOf(c.sec) < 0) secs.push(c.sec); });
    var sw = document.getElementById('chipsSec');
    sw.innerHTML = '';
    [''].concat(secs).forEach(function(x){
      var n = cnt(self.fTag, x);
      var b = document.createElement('button');
      b.className = 'chip' + (self.fSec === x ? ' on' : '') + (n ? '' : ' off');
      b.innerHTML = esc(x ? (x.length > 12 ? x.slice(0, 12) + '…' : x) : '전체')
                  + '<i>' + n + '</i>';
      b.title = (x || '전체') + ' · ' + n + '장';
      if(!n){
        /* 0장인 절 — 누르면 유형 필터를 풀어서 그 절 전체를 본다 */
        b.onclick = function(){
          self.fSec = x; self.fTag = '';
          self.toast('유형 필터를 풀었습니다');
          self.buildChips(); self.render();
        };
      } else {
        b.onclick = function(){ self.fSec = x; self.buildChips(); self.render(); };
      }
      sw.appendChild(b);
    });
"""
sub(OLD, NEW, "칩에 장수 표시 · 0장 칩은 반대쪽 필터를 자동으로 푼다")


# ── ② 빈 화면 안내를 「다 끝냈다」와 「조합이 비었다」로 나눈다
OLD2 = """      el.innerHTML = '<div class="empty">이 범위는 다 끝냈습니다.<br>필터를 바꾸거나, 복습 예정일에 다시 오십시오.'
        + '<br><br><button class="bigbtn" style="max-width:240px;margin:0 auto" onclick="App.openMenu()">장 선택으로</button></div>';"""

NEW2 = """      var np = this.pool().length;
      el.innerHTML = np
        ? ('<div class="empty">이 범위 <b>' + np + '장</b>을 다 끝냈습니다.'
           + '<br>필터를 바꾸거나, 복습 예정일에 다시 오십시오.'
           + '<br><br><button class="bigbtn" style="max-width:240px;margin:0 auto" onclick="App.openMenu()">장 선택으로</button></div>')
        : ('<div class="empty"><b>' + esc(this.fTag || '전체 유형') + '</b> 과 <b>'
           + esc(this.fSec || '전체 절') + '</b> 이 겹치는 카드가 없습니다.'
           + '<br>둘 중 하나를 풀어야 합니다.'
           + '<br><br><button class="bigbtn" style="max-width:240px;margin:0 auto" onclick="App.clearFilter()">필터 모두 풀기</button></div>');"""
sub(OLD2, NEW2, "빈 화면 — 「다 끝냈다」와 「조합이 비었다」를 구분")


# ── ③ 필터 해제 함수
OLD3 = "  /* ---------- 장 선택 화면 ---------- */"
NEW3 = """  clearFilter: function(){
    this.fSec = ''; this.fTag = '';
    this.buildChips(); this.render();
  },

  /* ---------- 장 선택 화면 ---------- */"""
sub(OLD3, NEW3, "clearFilter() 추가")


# ── ④ 0장 칩 모양
OLD4 = ".chip.on{background:linear-gradient(120deg,var(--accent),#5a9bff);color:#fff}"
NEW4 = """.chip.on{background:linear-gradient(120deg,var(--accent),#5a9bff);color:#fff}
.chip i{font-style:normal;font-size:11px;font-weight:800;opacity:.55;margin-left:5px;font-variant-numeric:tabular-nums}
.chip.on i{opacity:.8}
.chip.off{opacity:.38}
.chip.off i{color:var(--bad)}"""
sub(OLD4, NEW4, "칩 장수 글자 · 0장 칩 흐리게")

io.open(P, "w", encoding="utf-8").write(s)
print("\n✔ ui_new.html  %d → %d bytes (+%d)" % (n0, len(s), len(s) - n0))
