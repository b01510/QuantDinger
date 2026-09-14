from pathlib import Path
p=Path('/app/app.py') if Path('/app/app.py').exists() else Path('app.py')
s=p.read_text(encoding='utf-8')
needle='<div id="scanStatus" class="muted">尚未掃描</div>'
replacement=needle+'<iframe src="/api/scanner/progress/view" title="掃描進度" style="width:100%;height:42px;border:0;margin:8px 0;background:transparent"></iframe>'
if needle in s and '/api/scanner/progress/view' not in s:
    s=s.replace(needle,replacement)
p.write_text(s,encoding='utf-8',newline='\n')
print('v0.8 progress iframe embedded')
