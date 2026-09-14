from pathlib import Path

p=Path('/app/app.py') if Path('/app/app.py').exists() else Path('app.py')
s=p.read_text(encoding='utf-8')

needle='<div id="scanStatus" class="muted">尚未掃描</div>'
market='<div id="marketRegime" style="margin:8px 0 10px;padding:10px 12px;border:1px solid #2a3858;border-radius:10px;background:#0f172a"><b>市場環境：載入中</b><div class="muted" style="font-size:12px;margin-top:3px">將依加權/櫃買趨勢調整品質分數</div></div>'+needle
if needle in s and 'id="marketRegime"' not in s:
    s=s.replace(needle,market)

first='<label><input id="fFirst" type="checkbox"> 只看首次回測</label>'
extra=first+'<label><input id="fNoHeat" type="checkbox" checked> 排除過度延伸</label>'
if first in s and 'id="fNoHeat"' not in s:
    s=s.replace(first,extra)

s=s.replace("let lastScanResults=[];","let lastScanResults=[];function renderMarket(m){let box=document.getElementById('marketRegime');if(!box||!m)return;let cls=m.regime==='多頭'?'🟢':(m.regime==='防守'?'🔴':'🟡');box.innerHTML=`<b>${cls} 市場環境：${m.regime}</b><div class=\"muted\" style=\"font-size:12px;margin-top:3px\">${m.note||''}｜品質分數調整 ${Number(m.score_adjustment||0)>0?'+':''}${m.score_adjustment||0}</div>`;}")

old="first=document.getElementById('fFirst').checked;let rows=lastScanResults.filter(x=>{"
new="first=document.getElementById('fFirst').checked,noHeat=document.getElementById('fNoHeat')?document.getElementById('fNoHeat').checked:true;let rows=lastScanResults.filter(x=>{"
if old in s:s=s.replace(old,new)

old2="if(first&&!x.first_pullback)return false;return true"
new2="if(first&&!x.first_pullback)return false;if(noHeat&&x.overheated)return false;return true"
if old2 in s:s=s.replace(old2,new2)

s=s.replace("let j=await r.json();st.textContent=","let j=await r.json();renderMarket(j.market);st.textContent=")

# Enrich the compact scanner explanation line.
d=chr(36)
oldtxt='品質 '+d+'{x.quality_grade||"—"}｜失效價 '+d+'{x.invalidation_price||"—"}｜風險 '+d+'{x.risk_to_stop_pct||"—"}%'
newtxt='品質 '+d+'{x.quality_grade||"—"}｜建議失效 '+d+'{x.invalidation_price||"—"}｜風險 '+d+'{x.risk_to_stop_pct||"—"}%<br><span class="muted" style="font-size:12px">爆量前20日 '+d+'{x.pre_surge_20d_pct??"—"}%｜距MA60 '+d+'{x.distance_ma60_pct??"—"}%｜ATR '+d+'{x.atr_pct??"—"}%'+d+'{x.overheated?"｜⚠ 過度延伸":(x.warm?"｜偏熱":"")}</span>'
if oldtxt in s:s=s.replace(oldtxt,newtxt)

# Make the reset button restore the default overheat filter.
oldreset="document.getElementById('fFirst').checked=false;renderScanResults()"
newreset="document.getElementById('fFirst').checked=false;if(document.getElementById('fNoHeat'))document.getElementById('fNoHeat').checked=true;renderScanResults()"
if oldreset in s:s=s.replace(oldreset,newreset)

p.write_text(s,encoding='utf-8',newline='\n')
print('v0.9 frontend patch applied')
