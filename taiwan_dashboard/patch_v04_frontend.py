from pathlib import Path

p=Path('/app/app.py') if Path('/app/app.py').exists() else Path('app.py')
s=p.read_text(encoding='utf-8')

old="let traces=[candle,[5,10,20,60].map(n=>({x,y:j.rows.map(v=>v['ma'+n]),type:'scatter',mode:'lines',name:'MA'+n,line:{width:1}}))].flat();"
new="let vc=j.rows.map(v=>(v.close??0)>=(v.open??0)?'#ff5b6e88':'#43d18d88');let vol={x,y:j.rows.map(v=>v.volume),type:'bar',name:'成交量',yaxis:'y2',marker:{color:vc},hovertemplate:'成交量：%{y:,}<extra></extra>'};let mas=[5,10,20,60].map(n=>({x,y:j.rows.map(v=>v['ma'+n]),type:'scatter',mode:'lines',name:'MA'+n,line:{width:1},yaxis:'y'}));candle.yaxis='y';let traces=[candle,...mas,vol];"
if old in s:s=s.replace(old,new)

old2="yaxis:{\n    gridcolor:'#1e2940',fixedrange:false,\n    showspikes:true,spikemode:'across',spikesnap:'cursor',spikedash:'dot',spikethickness:1\n  }"
new2="yaxis:{domain:[0.28,1],gridcolor:'#1e2940',fixedrange:false,showspikes:true,spikemode:'across',spikesnap:'cursor',spikedash:'dot',spikethickness:1},\n  yaxis2:{domain:[0,0.20],gridcolor:'#172033',fixedrange:false,title:'量'},bargap:0.15"
if old2 in s:s=s.replace(old2,new2)

qold='<div class="quote"><div><div id="title" style="font-size:20px;font-weight:700">2330 台積電</div><div class="muted" id="ticker">2330.TW</div></div><div id="price" class="price">—</div><div id="change">—</div></div>'
qnew='<div class="quote"><div><div id="title" style="font-size:20px;font-weight:700">2330 台積電</div><div class="muted" id="ticker">2330.TW</div></div><div id="price" class="price">—</div><div id="change">—</div><button id="watchBtn" class="secondary" style="margin-left:auto">＋ 自選</button></div>'
if qold in s:s=s.replace(qold,qnew)

anchor='</div><script>\nconst q=document.getElementById(\'q\'),results=document.getElementById(\'results\');let timer;'
insert='''</div>\n<div class="card" style="margin-top:16px"><div class="toolbar"><div><b>我的自選股</b><div class="muted" style="font-size:12px">儲存在這台瀏覽器</div></div><button id="clearWatch" class="secondary">清空</button></div><div id="watchlist" style="display:flex;gap:8px;flex-wrap:wrap"></div></div>\n<script>\nlet currentSymbol='2330';const WATCH_KEY='qd_tw_watchlist_v1';function getWatch(){try{return JSON.parse(localStorage.getItem(WATCH_KEY)||'[]')}catch(e){return []}}function setWatch(v){localStorage.setItem(WATCH_KEY,JSON.stringify([...new Set(v)]));renderWatch()}function renderWatch(){let w=getWatch(),box=document.getElementById('watchlist');box.innerHTML=w.length?w.map(s=>`<button class="secondary watch-chip" data-s="${s}">${s} ×</button>`).join(''):'<span class="muted">尚未加入自選股</span>';document.querySelectorAll('.watch-chip').forEach(el=>el.onclick=()=>loadStock(el.dataset.s));let b=document.getElementById('watchBtn');if(b)b.textContent=w.includes(currentSymbol)?'✓ 已自選':'＋ 自選'}document.getElementById('watchBtn').onclick=()=>{let w=getWatch();w=w.includes(currentSymbol)?w.filter(x=>x!==currentSymbol):[...w,currentSymbol];setWatch(w)};document.getElementById('clearWatch').onclick=()=>setWatch([]);\nconst q=document.getElementById('q'),results=document.getElementById('results');let timer;'''
if anchor in s:s=s.replace(anchor,insert)

sig="async function loadStock(s){document.getElementById('chart').classList.add('loading');"
if sig in s:s=s.replace(sig,"async function loadStock(s){currentSymbol=s;renderWatch();document.getElementById('chart').classList.add('loading');")

s=s.replace('先掃常用大型股/熱門ETF','可快速掃熱門股，或掃全上市櫃')
s=s.replace('<button id="scanBtn">重新掃描</button>','<div style="display:flex;gap:6px"><button id="popularScan" class="secondary">快速掃熱門股</button><button id="scanBtn">全市場掃描</button></div>')
s=s.replace("async function scan(){let b=document.getElementById('scanBtn'),st=document.getElementById('scanStatus');b.disabled=true;st.textContent='掃描中，第一次可能需要 20–60 秒…';try{let r=await fetch('/api/scanner');let j=await r.json();st.textContent=`找到 ${j.count} 檔符合條件`;","async function scan(scope='popular'){let b=document.getElementById('scanBtn'),pb=document.getElementById('popularScan'),st=document.getElementById('scanStatus');b.disabled=true;pb.disabled=true;st.textContent=scope==='all'?'全上市櫃掃描中，可能需要數分鐘…':'熱門股快速掃描中…';try{let r=await fetch('/api/scanner?scope='+scope);let j=await r.json();st.textContent=`已掃 ${j.scanned??'—'} 檔，找到 ${j.count} 檔符合條件`; ")
s=s.replace("}catch(e){st.textContent='掃描失敗：'+e.message}finally{b.disabled=false}}\ndocument.getElementById('scanBtn').onclick=scan;loadStock('2330');scan();","}catch(e){st.textContent='掃描失敗：'+e.message}finally{b.disabled=false;pb.disabled=false}}\ndocument.getElementById('scanBtn').onclick=()=>scan('all');document.getElementById('popularScan').onclick=()=>scan('popular');renderWatch();loadStock('2330');scan('popular');")

p.write_text(s,encoding='utf-8',newline='\n')
print('v0.4 frontend patch applied')
