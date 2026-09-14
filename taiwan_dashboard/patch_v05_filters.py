from pathlib import Path

p = Path('/app/app.py') if Path('/app/app.py').exists() else Path('app.py')
s = p.read_text(encoding='utf-8')
s = s.replace('version="0.4.0"', 'version="0.5.0"')
s = s.replace('"version": "0.4.0"', '"version": "0.5.0"')
s = s.replace('台股研究版 v0.4', '台股研究版 v0.5')

needle = '<div id="scanStatus" class="muted">尚未掃描</div>'
filters = '''<div style="display:grid;grid-template-columns:repeat(3,minmax(120px,1fr));gap:8px;margin:10px 0">
<input id="fKeyword" placeholder="代碼/名稱" style="background:#121a2f;border:1px solid #2a3858;border-radius:8px;padding:8px;color:white">
<input id="fPriceMin" type="number" step="0.1" placeholder="最低股價" style="background:#121a2f;border:1px solid #2a3858;border-radius:8px;padding:8px;color:white">
<input id="fPriceMax" type="number" step="0.1" placeholder="最高股價" style="background:#121a2f;border:1px solid #2a3858;border-radius:8px;padding:8px;color:white">
<input id="fVolMin" type="number" step="0.1" placeholder="最低量比" style="background:#121a2f;border:1px solid #2a3858;border-radius:8px;padding:8px;color:white">
<input id="fDistMax" type="number" step="0.1" value="2.5" placeholder="距20MA最大%" style="background:#121a2f;border:1px solid #2a3858;border-radius:8px;padding:8px;color:white">
<input id="fScoreMin" type="number" step="1" placeholder="最低分數" style="background:#121a2f;border:1px solid #2a3858;border-radius:8px;padding:8px;color:white">
</div><div style="display:flex;gap:8px;align-items:center;margin-bottom:8px"><label><input id="fFirst" type="checkbox"> 只看首次回測</label><button id="applyFilters" class="secondary">套用篩選</button><button id="resetFilters" class="secondary">重設</button><span id="filterStatus" class="muted" style="font-size:12px"></span></div>''' + needle
if needle in s and 'id="fKeyword"' not in s:
    s = s.replace(needle, filters)

old = "document.getElementById('scanRows').innerHTML=j.results.map(x=>`<tr class=\"click\" data-s=\"${x.symbol}\"><td><b>${x.symbol}</b><br><span class=\"muted\">${x.name}</span>${x.first_pullback?'<br><span class=\"pill\">首次回測</span>':''}</td><td>${x.last??'—'}</td><td>${x.distance_ma20_pct??'—'}%</td><td>${x.volume_ratio??'—'}x</td><td><b>${x.score??'—'}</b></td></tr>`).join('');document.querySelectorAll('tr.click').forEach(el=>el.onclick=()=>loadStock(el.dataset.s));"
new = "lastScanResults=j.results||[];renderScanResults();"
if old in s:
    s = s.replace(old, new)

anchor = "const q=document.getElementById('q'),results=document.getElementById('results');let timer;"
js = '''let lastScanResults=[];
function fv(id){let v=document.getElementById(id).value;return v===''?null:Number(v)}
function renderScanResults(){let kw=(document.getElementById('fKeyword').value||'').trim().toLowerCase(),pmin=fv('fPriceMin'),pmax=fv('fPriceMax'),vmin=fv('fVolMin'),dmax=fv('fDistMax'),smin=fv('fScoreMin'),first=document.getElementById('fFirst').checked;let rows=lastScanResults.filter(x=>{let label=((x.symbol||'')+' '+(x.name||'')).toLowerCase();if(kw&&!label.includes(kw))return false;if(pmin!==null&&Number(x.last)<pmin)return false;if(pmax!==null&&Number(x.last)>pmax)return false;if(vmin!==null&&Number(x.volume_ratio)<vmin)return false;if(dmax!==null&&Math.abs(Number(x.distance_ma20_pct))>dmax)return false;if(smin!==null&&Number(x.score)<smin)return false;if(first&&!x.first_pullback)return false;return true});document.getElementById('filterStatus').textContent=`顯示 ${rows.length} / ${lastScanResults.length} 檔`;document.getElementById('scanRows').innerHTML=rows.map(x=>`<tr class="click" data-s="${x.symbol}"><td><b>${x.symbol}</b><br><span class="muted">${x.name}</span>${x.first_pullback?'<br><span class="pill">首次回測</span>':''}</td><td>${x.last??'—'}</td><td>${x.distance_ma20_pct??'—'}%</td><td>${x.volume_ratio??'—'}x</td><td><b>${x.score??'—'}</b></td></tr>`).join('');document.querySelectorAll('tr.click').forEach(el=>el.onclick=()=>loadStock(el.dataset.s))}
function resetFilters(){['fKeyword','fPriceMin','fPriceMax','fVolMin','fScoreMin'].forEach(id=>document.getElementById(id).value='');document.getElementById('fDistMax').value='2.5';document.getElementById('fFirst').checked=false;renderScanResults()}
'''
if anchor in s and 'let lastScanResults=[];' not in s:
    s = s.replace(anchor, js + anchor)

end = "document.getElementById('scanBtn').onclick=()=>scan('all');document.getElementById('popularScan').onclick=()=>scan('popular');renderWatch();loadStock('2330');scan('popular');"
rep = "document.getElementById('scanBtn').onclick=()=>scan('all');document.getElementById('popularScan').onclick=()=>scan('popular');document.getElementById('applyFilters').onclick=renderScanResults;document.getElementById('resetFilters').onclick=resetFilters;renderWatch();loadStock('2330');scan('popular');"
if end in s:
    s = s.replace(end, rep)

p.write_text(s, encoding='utf-8', newline='\n')
print('v0.5 filter patch applied')
