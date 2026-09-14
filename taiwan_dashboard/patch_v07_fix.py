from pathlib import Path
p=Path('/app/app.py') if Path('/app/app.py').exists() else Path('app.py')
s=p.read_text(encoding='utf-8')
old='''    if enough and (fresh or _checked_recently(info)):\n        ticker=(info.get("symbol") or code)+(".TWO" if str(symbol).upper().endswith('.TWO') else '.TW')\n        try: ticker=resolve_ticker(symbol)\n        except Exception: pass\n        _CACHE_STATS["sqlite_hits"]+=1'''
new='''    if enough and (fresh or _checked_recently(info)):\n        ticker=info.get("ticker") or (str(symbol).upper() if str(symbol).upper().endswith((".TW",".TWO")) else code+".TW")\n        _CACHE_STATS["sqlite_hits"]+=1'''
if old not in s:
    raise SystemExit('v0.7 cache-hit block not found')
s=s.replace(old,new)
p.write_text(s,encoding='utf-8',newline='\n')
print('v0.7 cache-hit fix applied')
