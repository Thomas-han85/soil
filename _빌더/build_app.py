# -*- coding: utf-8 -*-
"""틈틈봇 단일 HTML 학습 엔진 — PMP 틈틈봇 방식
  · 카드 1장씩 강제 노출 → 3초 생각 → 답 확인 → ○/✗ 자가평가
  · 오답은 간격 반복(3일 → 7일), localStorage 저장
  · 절/태그 필터, 진도바, 오늘의 N장, 키보드 단축키
  · 인터넷 없이 파일 하나로 동작 (바탕화면 바로가기)
사용: python -X utf8 build_app.py
"""
import os, io, json, html

HERE = os.path.dirname(os.path.abspath(__file__))
BOT = os.path.dirname(HERE)
CARDS = json.load(io.open(os.path.join(BOT, "cards.json"), encoding="utf-8"))

# 질문 문구 다듬기
FIX = {
    "◆ 1장 = 이 한 줄 — 말해 보세요": "1장을 한 줄로 요약하면? (사질토 vs 점성토)",
    "이 장의 척추 — 말해 보세요": "1장의 척추는?",
}
for c in CARDS:
    c["q"] = FIX.get(c["q"], c["q"])
    c["q"] = c["q"].replace("— 말해 보세요", "— 설명해 보세요")

CSS = """
:root{
  --bg:#faf8f4;--card:#fff;--ink:#1b1d21;--sub:#5f6672;--line:#e2ddd4;
  --blue:#1f5fa8;--blueF:#e8f0f9;--rust:#a8452a;--rustF:#fbeee9;
  --ok:#2c6e49;--okF:#e7f2ea;--gold:#8a6a1f;--goldF:#fbf3dd;
  --mono:ui-monospace,"Cascadia Mono",Consolas,monospace;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI","Malgun Gothic","Apple SD Gothic Neo","Noto Sans KR",sans-serif;
}
@media (prefers-color-scheme:dark){:root{
  --bg:#14161a;--card:#1c1f25;--ink:#e8e6e1;--sub:#9aa2ae;--line:#2e333c;
  --blue:#6fa8e8;--blueF:#1a2735;--rust:#e08b6c;--rustF:#2e211c;
  --ok:#6fc08e;--okF:#18271e;--gold:#d6b25e;--goldF:#2a2417;}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
  font-size:17px;line-height:1.75;-webkit-text-size-adjust:100%;
  min-height:100vh;display:flex;flex-direction:column}
header{background:linear-gradient(135deg,#1e3450,#2c5782);color:#fff;padding:12px 16px 10px;flex-shrink:0}
header .row{max-width:820px;margin:0 auto;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
header h1{margin:0;font-size:1.05rem;letter-spacing:-.01em}
header .st{font-family:var(--mono);font-size:.76rem;opacity:.9;margin-left:auto}
.pbar{max-width:820px;margin:8px auto 0;height:5px;background:rgba(255,255,255,.22);border-radius:3px;overflow:hidden}
.pbar i{display:block;height:100%;background:#8ec9a4;width:0;transition:width .3s}
main{flex:1;display:flex;align-items:center;justify-content:center;padding:18px 14px}
.card{width:100%;max-width:820px;background:var(--card);border:1px solid var(--line);
  border-radius:16px;padding:26px 26px 22px;box-shadow:0 6px 26px rgba(0,0,0,.07)}
.meta{display:flex;gap:7px;align-items:center;flex-wrap:wrap;margin-bottom:14px}
.bdg{font-family:var(--mono);font-size:.68rem;font-weight:700;border-radius:5px;padding:2px 8px}
.b-t{background:var(--blueF);color:var(--blue)}
.b-s{background:var(--rustF);color:var(--rust)}
.b-g{background:var(--okF);color:var(--ok)}
.b-c{background:var(--goldF);color:var(--gold)}
.b-n{background:var(--bg);color:var(--sub);border:1px solid var(--line)}
.q{font-size:1.3rem;font-weight:700;line-height:1.6;margin:0 0 6px}
.hint{font-size:.82rem;color:var(--sub);font-family:var(--mono)}
.timer{font-family:var(--mono);font-size:2.6rem;font-weight:700;color:var(--blue);
  text-align:center;margin:22px 0 8px;letter-spacing:.05em}
.timer.go{color:var(--ok)}
.a{border-top:1px dashed var(--line);margin-top:18px;padding-top:16px;font-size:1.02rem;line-height:1.8}
.a b{color:var(--rust)}
.a .ln{margin:5px 0}
.a table{border-collapse:collapse;width:100%;font-size:.9rem;margin-top:6px}
.a td{border:1px solid var(--line);padding:5px 8px;vertical-align:top}
.a tr:first-child td{background:var(--blueF);color:var(--blue);font-weight:700}
.acts{display:flex;gap:10px;margin-top:20px;flex-wrap:wrap}
.acts button{flex:1;min-width:130px;border:1px solid var(--line);background:var(--card);color:var(--ink);
  border-radius:12px;padding:14px 16px;font-size:1rem;font-family:var(--sans);font-weight:700;cursor:pointer}
.acts .show{background:var(--blue);border-color:var(--blue);color:#fff}
.acts .ok{background:var(--ok);border-color:var(--ok);color:#fff}
.acts .mid{background:var(--gold);border-color:var(--gold);color:#fff}
.acts .ng{background:var(--rust);border-color:var(--rust);color:#fff}
.acts .skip{font-weight:400;color:var(--sub);flex:0 0 auto;min-width:0;padding:14px 18px}
footer{flex-shrink:0;padding:10px 14px 16px;border-top:1px solid var(--line);background:var(--card)}
footer .row{max-width:820px;margin:0 auto;display:flex;gap:7px;flex-wrap:wrap;align-items:center}
.chip{border:1px solid var(--line);background:var(--bg);color:var(--sub);border-radius:16px;
  padding:5px 12px;font-size:.78rem;cursor:pointer;font-family:var(--sans);white-space:nowrap}
.chip.on{background:var(--blue);border-color:var(--blue);color:#fff;font-weight:600}
.cnt{font-family:var(--mono);font-size:.75rem;color:var(--sub);margin-left:auto}
.kb{font-family:var(--mono);font-size:.7rem;color:var(--sub);opacity:.8}
.done{text-align:center;padding:40px 20px}
.done h2{font-size:1.4rem;margin:0 0 10px}
.done p{color:var(--sub)}
body.lock{background:transparent}
body.lock header{background:transparent;padding:6px 12px 2px}
body.lock header h1{font-size:.9rem;opacity:.85}
body.lock .card{background:rgba(255,255,255,.97);border:0;box-shadow:0 10px 40px rgba(0,0,0,.4)}
@media (prefers-color-scheme:dark){body.lock .card{background:rgba(28,31,37,.97)}}
body.lock .q{font-size:1.36rem}
body.lock main{padding:8px 10px}
@media(max-width:560px){
  .card{padding:20px 18px 18px;border-radius:13px}
  .q{font-size:1.15rem} .timer{font-size:2.1rem;margin:16px 0 6px}
  .acts button{min-width:0;font-size:.94rem;padding:13px 10px}
  .kb{display:none}
}
"""

JS = r"""
var CARDS = __DATA__;
var LS = 'toji_bot_v1', S = {};
try{ S = JSON.parse(localStorage.getItem(LS) || '{}'); }catch(e){}
function save(){ try{ localStorage.setItem(LS, JSON.stringify(S)); }catch(e){} }
function ymd(d){ return d.getFullYear()+'-'+('0'+(d.getMonth()+1)).slice(-2)+'-'+('0'+d.getDate()).slice(-2); }
function today(){ return ymd(new Date()); }
function plus(n){ var d=new Date(); d.setDate(d.getDate()+n); return ymd(d); }

var fSec='', fTag='', cur=null, shown=false, tmr=null, left=0, lastSec='', sessN=0;
/* 잠금화면 모드 — LockScreenActivity가 ?lock=1 로 연다.
   카드 한 장만 크게 보여주고 필터·푸터를 숨긴다 */
var LOCK = /[?&]lock=1/.test(location.search);
/* 안드로이드 네이티브 TTS — 손을 못 쓸 때 질문을 읽어준다 */
var TTS = (typeof AndroidTTS !== 'undefined' && AndroidTTS.available && AndroidTTS.available());
function say(t){
  if(!TTS) return;
  try{ AndroidTTS.speak(String(t).replace(/\*\*/g,'').replace(/<[^>]+>/g,' ')); }catch(e){}
}
function hush(){ if(TTS){ try{ AndroidTTS.stop(); }catch(e){} } }
/* 간격 반복 — 24시간 뒤 복습이 가장 중요(Karpicke & Roediger 2008). 1 → 3 → 7 → 21일 */
var STEPS = [1, 3, 7, 21];

function st(id){ return S[id]||null; }
function done(c){ var v=st(c.id); return !!(v && v.s==='o' && !v.n); }
function due(c){ var v=st(c.id); return !!(v && v.n && v.n<=today()); }
function fresh(c){ return !st(c.id); }
function pool(){
  return CARDS.filter(function(c){
    if(fSec && c.sec!==fSec) return false;
    if(fTag && c.tag!==fTag) return false;
    return true;
  });
}
function rnd(a){ return a[Math.floor(Math.random()*a.length)]; }
/* 교차연습 — 직전 카드와 다른 절을 우선한다 (Rohrer 2020 · d=0.83)
   블록으로 풀면 연습 중엔 잘 되지만 시험에서 무너진다 */
function cross(a){
  if(a.length < 2) return a.length ? a[0] : null;
  var other = a.filter(function(c){ return c.sec !== lastSec; });
  return rnd(other.length ? other : a);
}
function pick(){
  var p = pool();
  var d = p.filter(due);
  var f = p.filter(fresh);
  var r = p.filter(function(c){ return !done(c) && !due(c) && !fresh(c); });
  /* 복습이 밀리면 먼저 턴다. 아니면 복습:새것 = 1:2 로 섞는다 */
  if(d.length >= 8) return cross(d);
  if(d.length && f.length) return cross(Math.random() < 0.34 ? d : f);
  if(d.length) return cross(d);
  if(f.length) return cross(f);
  if(r.length) return cross(r);
  return null;
}

function fmtAns(a){
  if(a.indexOf('|') >= 0 && a.split('|').length > 3){
    var parts = a.split('|').filter(function(x){ return x.trim(); });
    var isTbl = parts.filter(function(x){ return x.indexOf('  ')>=0 || x.split(' | ').length>1; }).length > 1;
    if(a.indexOf('**') === 0 && parts.length > 2){
      var rows = a.split('||').filter(function(x){return x.trim();});
      var out = '<table>';
      rows.forEach(function(r){
        var cs = r.replace(/^\|/,'').replace(/\|$/,'').split('|').map(function(x){return x.trim();}).filter(function(x){return x;});
        if(!cs.length) return;
        out += '<tr>' + cs.map(function(x){ return '<td>'+bold(x)+'</td>'; }).join('') + '</tr>';
      });
      return out + '</table>';
    }
    return parts.map(function(x){ return '<div class="ln">'+bold(x.trim())+'</div>'; }).join('');
  }
  return '<div class="ln">'+bold(a)+'</div>';
}
function bold(x){
  return x.replace(/\*\*(.+?)\*\*/g, '<b>$1</b>').replace(/\*\*/g,'');
}

function render(){
  var el = document.getElementById('stage');
  cur = pick(); shown = false;
  if(tmr){ clearInterval(tmr); tmr=null; }
  if(!cur){
    el.innerHTML = '<div class="card done"><h2>이 범위는 다 끝냈습니다</h2>'
      + '<p>필터를 바꾸거나, 복습 예정일에 다시 오십시오.</p>'
      + '<div class="acts"><button class="show" onclick="resetFilter()">전체 보기</button></div></div>';
    stats(); return;
  }
  var bc = {'인출':'b-t','살':'b-s','골격':'b-g','비교표':'b-c','갭B':'b-n'}[cur.tag] || 'b-n';
  var v = st(cur.id);
  var mark = v ? (v.s==='x' ? '<span class="bdg b-s">복습</span>' : (v.n ? '<span class="bdg b-c">확인</span>' : '')) : '';
  el.innerHTML =
    '<div class="card">'
    + '<div class="meta"><span class="bdg '+bc+'">'+cur.tag+'</span>'
    + '<span class="bdg b-n">'+cur.sec+'</span>'+mark
    + '<span class="hint" style="margin-left:auto">'+cur.id+'</span></div>'
    + '<p class="q">'+cur.q+'</p>'
    + '<p class="hint">소리 내어 답해 보세요. 막혀도 버티는 게 효과입니다.</p>'
    + '<div class="timer" id="tm">3</div>'
    + '<div id="ans"></div>'
    + '<div class="acts" id="acts">'
    +   '<button class="show" onclick="reveal()">답 보기 <span class="kb">(Space)</span></button>'
    +   '<button class="skip" onclick="render()">건너뛰기</button>'
    + '</div></div>';
  say(cur.q);
  left = 3;
  tmr = setInterval(function(){
    left--;
    var t = document.getElementById('tm');
    if(!t){ clearInterval(tmr); return; }
    if(left > 0){ t.textContent = left; }
    else { t.textContent = '지금 답하세요'; t.classList.add('go'); t.style.fontSize='1.2rem'; clearInterval(tmr); tmr=null; }
  }, 1000);
  stats();
}

function reveal(){
  if(shown || !cur) return;
  shown = true; hush();
  if(tmr){ clearInterval(tmr); tmr=null; }
  var t=document.getElementById('tm'); if(t) t.style.display='none';
  document.getElementById('ans').innerHTML = '<div class="a">'+fmtAns(cur.a)+'</div>';
  document.getElementById('acts').innerHTML =
      '<button class="ok" onclick="mark(2)">막힘없이 <span class="kb">(1)</span></button>'
    + '<button class="mid" onclick="mark(1)">겨우 떠올림 <span class="kb">(2)</span></button>'
    + '<button class="ng" onclick="mark(0)">못 했다 <span class="kb">(3)</span></button>';
}

/* g=2 막힘없이 / g=1 겨우 / g=0 못 함
   "겨우 떠올림"을 따로 둔 이유 — 읽으면 아는 것 같은 유창성 착각을 걸러내기 위함.
   막힘없이 답한 것만 간격을 늘린다. */
function mark(g){
  if(!cur) return;
  var v = st(cur.id) || {i:-1, w:0};
  var i = (typeof v.i === 'number') ? v.i : -1;
  if(g === 0){ i = -1; }                          /* 못 했다 → 처음으로 */
  else if(g === 1){ i = Math.max(0, i); }         /* 겨우   → 간격 유지 */
  else { i = Math.min(i + 1, STEPS.length - 1); } /* 막힘없이 → 다음 간격 */
  var nx = plus(STEPS[Math.max(0, i)]);
  var fin = (g === 2 && i >= STEPS.length - 1);   /* 21일까지 통과 = 완료 */
  S[cur.id] = { s:(g===0?'x':'o'), n:(fin?null:nx), i:i, w:(g===0?1:(v.w||0)) };
  lastSec = cur.sec; sessN++;
  save(); render();
}

function stats(){
  var p = pool();
  var nd = p.filter(done).length, ndue = p.filter(due).length, nf = p.filter(fresh).length;
  document.getElementById('st').textContent = nd + ' / ' + p.length + ' 완료';
  document.getElementById('pb').style.width = (p.length ? nd/p.length*100 : 0) + '%';
  document.getElementById('cnt').textContent =
    '이번 세션 ' + sessN + '장 · 새 카드 ' + nf + ' · 복습 ' + ndue + ' · 남음 ' + (p.length - nd);
}

function resetFilter(){
  fSec=''; fTag='';
  document.querySelectorAll('.chip').forEach(function(c){ c.classList.remove('on'); });
  document.querySelector('.chip[data-v=""][data-f="sec"]').classList.add('on');
  document.querySelector('.chip[data-v=""][data-f="tag"]').classList.add('on');
  render();
}
function resetAll(){
  if(!confirm('학습 기록을 모두 지웁니다. 계속할까요?')) return;
  S = {}; save(); render();
}

document.addEventListener('keydown', function(e){
  if(e.key === ' ' || e.key === 'Enter'){ e.preventDefault(); if(!shown) reveal(); }
  else if(e.key === '1' && shown) mark(2);
  else if(e.key === '2' && shown) mark(1);
  else if(e.key === '3' && shown) mark(0);
  else if(e.key === 'n' || e.key === 'N') render();
});

window.addEventListener('DOMContentLoaded', function(){
  if(LOCK){
    document.body.classList.add('lock');
    var f = document.querySelector('footer'); if(f) f.style.display = 'none';
  }
  document.querySelectorAll('.chip').forEach(function(c){
    c.onclick = function(){
      var f = c.dataset.f;
      document.querySelectorAll('.chip[data-f="'+f+'"]').forEach(function(x){ x.classList.remove('on'); });
      c.classList.add('on');
      if(f === 'sec') fSec = c.dataset.v; else fTag = c.dataset.v;
      render();
    };
  });
  render();
});
"""

secs, tags = [], []
for c in CARDS:
    if c["sec"] not in secs: secs.append(c["sec"])
    if c["tag"] not in tags: tags.append(c["tag"])

chips_sec = '<button class="chip on" data-f="sec" data-v="">전체 절</button>' + "".join(
    '<button class="chip" data-f="sec" data-v="%s">%s</button>' % (html.escape(s, True), html.escape(s.split("—")[0].strip()[:12]))
    for s in secs)
chips_tag = '<button class="chip on" data-f="tag" data-v="">전체</button>' + "".join(
    '<button class="chip" data-f="tag" data-v="%s">%s</button>' % (html.escape(t, True), html.escape(t)) for t in tags)

body = (
 '<header><div class="row"><h1>토질 틈틈봇</h1>'
 '<span class="bdg b-n" style="background:rgba(255,255,255,.16);color:#fff">제1장 · 살 %d장</span>'
 '<span class="st" id="st"></span></div>'
 '<div class="pbar"><i id="pb"></i></div></header>'
 '<main id="stage"></main>'
 '<footer><div class="row">%s</div>'
 '<div class="row" style="margin-top:6px">%s'
 '<button class="chip" onclick="resetAll()">기록 초기화</button>'
 '<span class="cnt" id="cnt"></span></div></footer>'
) % (len(CARDS), chips_tag, chips_sec)

js = JS.replace("__DATA__", json.dumps(CARDS, ensure_ascii=False))
out = ('<!doctype html><html lang="ko"><head><meta charset="utf-8">'
       '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
       '<title>토질 틈틈봇</title><style>%s</style></head><body>%s<script>%s</script></body></html>'
       % (CSS, body, js))

p = os.path.join(BOT, "토질_틈틈봇.html")
io.open(p, "w", encoding="utf-8").write(out)
print("✔ %s  %d bytes · 카드 %d장 · 절 %d · 태그 %d"
      % (os.path.basename(p), len(out.encode("utf-8")), len(CARDS), len(secs), len(tags)))
