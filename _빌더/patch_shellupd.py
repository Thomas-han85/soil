# -*- coding: utf-8 -*-
"""새 UI 손질 ③ — [업데이트] 버튼이 화면까지 갱신하게

실장님: "업데이트 눌렀는데 그대로 같은데?"

원인
  갱신이 두 갈래로 나뉘어 있었다.
    · 카드(cards.json)  ← JS 의 checkUpdate() = [업데이트] 버튼
    · 화면(index.html)  ← Kotlin 의 Shell.refresh() = 앱을 켤 때 뒤에서 내려받기
  껍데기는 「이미 저장돼 있던 것」을 띄우고 새 것은 뒤에서 받으므로,
  새 화면은 다음 번에 앱을 켜야 나온다. 그래서 버튼을 눌러도 그대로였다.

고침
  버튼이 카드와 화면을 함께 본다. 화면이 바뀌었으면 그 자리에서 갈아 끼운다.
  주소(origin)가 그대로라 학습기록은 남고, 풀던 자리도 되살아난다.

안전장치는 Kotlin 과 같게 둔다 — 길이·표식·닫는 태그가 온전할 때만 교체한다.
깨진 것을 올려도 지금 화면이 그대로 살아 있다.
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


# ── ① 화면 판번호 자리 + 원격 주소
sub("var SRC = 'https://raw.githubusercontent.com/Thomas-han85/soil/main/cards.json';",
    """var SRC = 'https://raw.githubusercontent.com/Thomas-han85/soil/main/cards.json';
/* 화면(껍데기) 판번호 — 빌드할 때 채워 넣는다. 원격 것과 다르면 화면을 갈아 끼운다 */
var UI_BUILD = '__UI_BUILD__';
var UI_SRC = 'https://raw.githubusercontent.com/Thomas-han85/soil/main/index.html';""",
    "UI_BUILD 판번호 · 화면 원격주소 추가")


# ── ② checkUpdate 가 화면도 본다
OLD = """      .catch(function(){ if(!silent) self.toast('오프라인입니다'); });
  },"""
NEW = """      .catch(function(){ if(!silent) self.toast('오프라인입니다'); });
    this.checkShell(silent);
  },

  /* 화면(껍데기) 갱신 — 카드와 따로 돈다.
     Kotlin 쪽 Shell.refresh() 는 「다음 실행」에 반영되는 구조라,
     버튼을 눌렀을 때 눈앞에서 바뀌게 하려면 여기서 직접 갈아 끼워야 한다. */
  checkShell: function(silent){
    var self = this;
    if(this._shellBusy) return;
    this._shellBusy = true;
    fetch(UI_SRC + '?t=' + Date.now(), { cache:'no-store' })
      .then(function(r){ return r.text(); })
      .then(function(html){
        self._shellBusy = false;
        /* Kotlin 과 같은 안전장치 — 온전할 때만 교체한다 */
        if(html.length < 50000) return;
        if(html.indexOf('function checkUpdate') < 0
           && html.indexOf('checkUpdate: function') < 0) return;
        if(html.replace(/\s+$/, '').slice(-7) !== '</html>') return;
        var m = html.match(/var UI_BUILD = '([^']*)'/);
        if(!m || m[1] === UI_BUILD) return;           /* 같은 판이면 둘 것 */
        self.saveSpot();                              /* 풀던 자리를 남기고 */
        self.stopSpeak();
        if(!silent) self.toast('새 화면을 적용합니다…');
        setTimeout(function(){
          try{
            document.open(); document.write(html); document.close();
          }catch(e){ try{ location.reload(); }catch(e2){} }
        }, silent ? 0 : 700);
      })
      .catch(function(){ self._shellBusy = false; });
  },"""
sub(OLD, NEW, "checkShell() 추가 — 화면이 바뀌었으면 그 자리에서 교체")


# ── ③ 판번호를 화면에 보이게 (뭘 쓰고 있는지 확인할 수 있어야 한다)
OLD3 = """      <button class="upd" onclick="App.checkUpdate()">↻ 업데이트</button></div>"""
NEW3 = """      <button class="upd" onclick="App.checkUpdate()">↻ 업데이트</button>
      <div class="uiver" id="uiver"></div></div>"""
sub(OLD3, NEW3, "판번호 표시 자리")

sub(".topstrip .upd{border:none;background:transparent;color:var(--accent);font-size:12px;font-weight:800;cursor:pointer;padding:2px 6px}",
    """.topstrip .upd{border:none;background:transparent;color:var(--accent);font-size:12px;font-weight:800;cursor:pointer;padding:2px 6px}
.topstrip .uiver{font-size:10px;color:var(--sub);opacity:.55;text-align:right;letter-spacing:.2px}""",
    "판번호 글자 모양")

sub("    setTimeout(function(){ App.checkUpdate(true); }, 800);",
    """    var uv = document.getElementById('uiver');
    if(uv) uv.textContent = '화면 ' + UI_BUILD + ' · 카드 v' + VER_LOCAL;

    setTimeout(function(){ App.checkUpdate(true); }, 800);""",
    "시작할 때 판번호 찍기")

io.open(P, "w", encoding="utf-8").write(s)
print("\n✔ ui_new.html  %d → %d bytes (+%d)" % (n0, len(s), len(s) - n0))
