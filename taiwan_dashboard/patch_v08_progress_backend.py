from pathlib import Path

p=Path('/app/app.py') if Path('/app/app.py').exists() else Path('app.py')
s=p.read_text(encoding='utf-8')
s=s.replace('version="0.7.0"','version="0.8.0"').replace('"version": "0.7.0"','"version": "0.8.0"').replace('台股研究版 v0.7','台股研究版 v0.8')

marker='@app.get("/api/scanner")\ndef scanner(scope: str="popular"):'
block='''_SCAN_PROGRESS={"running":False,"scope":"","completed":0,"total":0,"matched":0,"current":"","started_at":None,"finished_at":None}\n_SCAN_PROGRESS_LOCK=threading.Lock()\n\ndef _set_scan_progress(**kwargs):\n    with _SCAN_PROGRESS_LOCK:\n        _SCAN_PROGRESS.update(kwargs)\n\n@app.get("/api/scanner/progress")\ndef scanner_progress():\n    with _SCAN_PROGRESS_LOCK:\n        p=dict(_SCAN_PROGRESS)\n    total=int(p.get("total") or 0)\n    completed=int(p.get("completed") or 0)\n    p["percent"]=round(completed/total*100,1) if total else 0.0\n    elapsed=0.0\n    eta=None\n    if p.get("started_at"):\n        elapsed=max(0.0,time.time()-float(p["started_at"]))\n        if completed>0 and total>completed:\n            eta=elapsed/completed*(total-completed)\n    p["elapsed_seconds"]=round(elapsed,1)\n    p["eta_seconds"]=round(eta,1) if eta is not None else None\n    return p\n\n'''
if marker in s and 'def scanner_progress()' not in s:
    s=s.replace(marker,block+marker)

old='''def scanner(scope: str="popular"):\n    results = []\n    if str(scope).lower()=="all":\n        universe = [x["symbol"] for x in get_tw_market_universe()]\n    else:\n        universe = list(POPULAR.keys())'''
new=old+'\n    _set_scan_progress(running=True,scope=str(scope).lower(),completed=0,total=len(universe),matched=0,current="",started_at=time.time(),finished_at=None)'
if old in s:
    s=s.replace(old,new)

old_loop='''        for f in as_completed(futures):\n            row = f.result()\n            if row:\n                results.append(row)'''
new_loop='''        for f in as_completed(futures):\n            code=futures[f]\n            row = f.result()\n            if row:\n                results.append(row)\n            with _SCAN_PROGRESS_LOCK:\n                _SCAN_PROGRESS["completed"] += 1\n                _SCAN_PROGRESS["matched"] = len(results)\n                _SCAN_PROGRESS["current"] = code'''
if old_loop in s:
    s=s.replace(old_loop,new_loop)

ret='return {"count": len(results), "scanned": len(universe), "cache_stats": dict(_CACHE_STATS), "results": results[:80], "definition": {'
if ret in s and '_set_scan_progress(running=False' not in s:
    s=s.replace(ret,'_set_scan_progress(running=False,completed=len(universe),total=len(universe),matched=len(results),current="",finished_at=time.time())\n    '+ret)

p.write_text(s,encoding='utf-8',newline='\n')
print('v0.8 progress backend patch applied')
