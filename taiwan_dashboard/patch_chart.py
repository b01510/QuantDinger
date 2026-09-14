from pathlib import Path

p = Path('/app/app.py') if Path('/app/app.py').exists() else Path('app.py')
s = p.read_text(encoding='utf-8')

s = s.replace('version="0.2.0"', 'version="0.3.0"')
s = s.replace('"version": "0.2.0"', '"version": "0.3.0"')
s = s.replace('台股研究版 v0.2', '台股研究版 v0.3')

old = "Plotly.newPlot('chart',traces,{paper_bgcolor:'#10182a',plot_bgcolor:'#10182a',font:{color:'#cbd5e1'},margin:{l:55,r:20,t:35,b:40},xaxis:{rangeslider:{visible:false},gridcolor:'#1e2940'},yaxis:{gridcolor:'#1e2940'}},{responsive:true,displaylogo:false})"
new = r'''let gd=document.getElementById('chart');
let layout={
  paper_bgcolor:'#10182a',plot_bgcolor:'#10182a',font:{color:'#cbd5e1'},margin:{l:55,r:20,t:35,b:40},
  dragmode:'pan',hovermode:'x unified',uirevision:j.symbol,
  hoverlabel:{bgcolor:'#0f172a',bordercolor:'#64748b',font:{color:'#f8fafc'}},
  xaxis:{
    rangeslider:{visible:false},gridcolor:'#1e2940',fixedrange:false,
    showspikes:true,spikemode:'across',spikesnap:'cursor',spikedash:'dot',spikethickness:1,
    tickformat:'%Y年%m月%d日',hoverformat:'%Y年%m月%d日'
  },
  yaxis:{
    gridcolor:'#1e2940',fixedrange:false,
    showspikes:true,spikemode:'across',spikesnap:'cursor',spikedash:'dot',spikethickness:1
  }
};
let config={responsive:true,displaylogo:false,displayModeBar:true,scrollZoom:false,doubleClick:false};
Plotly.newPlot(gd,traces,layout,config).then(()=>{
  gd.style.cursor='grab';
  gd.on('plotly_relayout',()=>{ gd.style.cursor='grab'; });
  gd.addEventListener('mousedown',()=>{gd.style.cursor='grabbing'});
  window.addEventListener('mouseup',()=>{gd.style.cursor='grab'},{once:true});

  if(gd.__twWheelHandler) gd.removeEventListener('wheel',gd.__twWheelHandler);
  gd.__twWheelHandler=(ev)=>{
    if(!gd._fullLayout || !gd._fullLayout.xaxis) return;
    ev.preventDefault();
    ev.stopPropagation();
    const xa=gd._fullLayout.xaxis;
    const r=xa.range;
    if(!r || r.length<2) return;
    let a=new Date(r[0]).getTime(), b=new Date(r[1]).getTime();
    if(!Number.isFinite(a)||!Number.isFinite(b)||a===b) return;
    const rect=gd.getBoundingClientRect();
    let t=(ev.clientX-rect.left)/Math.max(rect.width,1);
    t=Math.max(0,Math.min(1,t));
    const focus=a+(b-a)*t;
    const factor=ev.deltaY<0?0.82:1.22;
    const na=focus-(focus-a)*factor;
    const nb=focus+(b-focus)*factor;
    Plotly.relayout(gd,{'xaxis.autorange':false,'xaxis.range':[new Date(na).toISOString(),new Date(nb).toISOString()]});
  };
  gd.addEventListener('wheel',gd.__twWheelHandler,{passive:false});

  if(gd.__twDoubleHandler) gd.removeEventListener('dblclick',gd.__twDoubleHandler,true);
  gd.__twDoubleHandler=(ev)=>{
    ev.preventDefault();
    ev.stopPropagation();
    Plotly.relayout(gd,{'xaxis.autorange':true,'yaxis.autorange':true});
  };
  gd.addEventListener('dblclick',gd.__twDoubleHandler,true);
});'''

if old not in s:
    # Accept the previously locally patched form as well.
    old2 = "Plotly.newPlot('chart',traces,{paper_bgcolor:'#10182a',plot_bgcolor:'#10182a',font:{color:'#cbd5e1'},margin:{l:55,r:20,t:35,b:40},dragmode:'pan',xaxis:{rangeslider:{visible:false},gridcolor:'#1e2940',fixedrange:false},yaxis:{gridcolor:'#1e2940',fixedrange:false}},{responsive:true,displaylogo:false,scrollZoom:true,doubleClick:'reset'})"
    if old2 in s:
        s = s.replace(old2, new)
    elif new not in s:
        raise SystemExit('Could not locate Plotly chart constructor to patch')
else:
    s = s.replace(old, new)

needle = "let traces=[candle,"
if needle in s and "candle.hovertext=j.rows.map" not in s:
    hover = r'''candle.hovertext=j.rows.map(v=>`${v.date.replace(/-/g,'/')}<br>開：${v.open ?? '—'}<br>高：${v.high ?? '—'}<br>低：${v.low ?? '—'}<br>收：${v.close ?? '—'}<br>量：${(v.volume ?? 0).toLocaleString()}`);candle.hoverinfo='text';let traces=[candle,'''
    s = s.replace(needle, hover)

p.write_text(s, encoding='utf-8', newline='\n')
print('chart patch applied')
