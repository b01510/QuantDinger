from pathlib import Path

p=Path('/app/app.py') if Path('/app/app.py').exists() else Path('app.py')
s=p.read_text(encoding='utf-8')
s=s.replace('<th>分數</th>','<th>品質分數</th>')
d=chr(36)
needle='<span class="muted">'+d+'{x.name}</span>'
extra='<span class="muted">'+d+'{x.name}</span><br><span class="muted" style="font-size:11px">'+d+'{(x.reasons||[]).join("｜")}</span><br><span style="font-size:11px">品質 '+d+'{x.quality_grade||"—"}｜失效價 '+d+'{x.invalidation_price||"—"}｜風險 '+d+'{x.risk_to_stop_pct||"—"}%</span>'
if needle not in s: raise SystemExit('result label not found')
s=s.replace(needle,extra)
p.write_text(s,encoding='utf-8',newline='\n')
print('v0.6 frontend patch applied')
