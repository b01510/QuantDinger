from pathlib import Path
p=Path('/app/app.py') if Path('/app/app.py').exists() else Path('app.py')
s=p.read_text(encoding='utf-8')
marker='@app.get("/api/scanner")\ndef scanner(scope: str="popular"):'
block='''@app.get("/api/scanner/progress/view", response_class=HTMLResponse)\ndef scanner_progress_view():\n    p=scanner_progress()\n    pct=float(p.get("percent") or 0)\n    done=int(p.get("completed") or 0)\n    total=int(p.get("total") or 0)\n    matched=int(p.get("matched") or 0)\n    eta=p.get("eta_seconds")\n    extra=(f" / ETA {int(float(eta))}s" if eta is not None and p.get("running") else "")\n    html=f"<html><body style='margin:0;background:transparent;color:#94a3b8;font:12px sans-serif'><progress max='100' value='{pct}' style='width:100%'></progress><div>{pct:.1f}% / {done} of {total} / matched {matched}{extra}</div></body></html>"\n    headers={"Refresh":"1"} if p.get("running") else {}\n    return HTMLResponse(html,headers=headers)\n\n'''
if marker in s and 'def scanner_progress_view()' not in s:
    s=s.replace(marker,block+marker)
p.write_text(s,encoding='utf-8',newline='\n')
print('v0.8 progress view patch applied')
