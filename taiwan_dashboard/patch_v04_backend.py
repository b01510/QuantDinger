from pathlib import Path

p = Path('/app/app.py') if Path('/app/app.py').exists() else Path('app.py')
s = p.read_text(encoding='utf-8')
s = s.replace('version="0.3.0"', 'version="0.4.0"').replace('"version": "0.3.0"', '"version": "0.4.0"').replace('台股研究版 v0.3', '台股研究版 v0.4')

marker='@app.get("/api/scanner")\ndef scanner():'
helper='''_market_universe_cache={"ts":0.0,"rows":[]}\n\ndef get_tw_market_universe():\n    now=time.time()\n    if _market_universe_cache["rows"] and now-_market_universe_cache["ts"]<21600:\n        return _market_universe_cache["rows"]\n    out=[];seen=set()\n    for market,url,suffix in [("TWSE","https://openapi.twse.com.tw/v1/opendata/t187ap03_L",".TW"),("TPEX","https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O",".TWO")]:\n        try:\n            r=requests.get(url,timeout=15,headers=_YH)\n            if not r.ok: continue\n            for row in (r.json() or []):\n                code=str(row.get("公司代號") or row.get("Code") or "").strip().upper()\n                name=str(row.get("公司簡稱") or row.get("公司名稱") or row.get("CompanyName") or code).strip()\n                if not code or code in seen: continue\n                seen.add(code);out.append({"symbol":code,"name":name or code,"market":market,"ticker":code+suffix})\n        except Exception:\n            pass\n    if not out:\n        out=[{"symbol":c,"name":n,"market":"LOCAL","ticker":c} for c,n in POPULAR.items()]\n    _market_universe_cache.update({"ts":now,"rows":out})\n    return out\n\n@app.get("/api/universe")\ndef universe(q: str="", limit: int=200):\n    rows=get_tw_market_universe();kw=str(q or "").strip().upper()\n    if kw: rows=[x for x in rows if kw in x["symbol"].upper() or kw in str(x.get("name") or "").upper()]\n    return {"count":len(rows),"results":rows[:max(1,min(limit,2000))]}\n\n'''
if marker in s and 'def get_tw_market_universe' not in s:
    s=s.replace(marker,helper+marker)

old='''@app.get("/api/scanner")\ndef scanner():\n    results = []\n    universe = list(POPULAR.keys())'''
new='''@app.get("/api/scanner")\ndef scanner(scope: str="popular"):\n    results = []\n    if str(scope).lower()=="all":\n        universe = [x["symbol"] for x in get_tw_market_universe()]\n    else:\n        universe = list(POPULAR.keys())'''
if old in s:
    s=s.replace(old,new)

s=s.replace('return {"count": len(results), "results": results[:30], "definition": {','return {"count": len(results), "scanned": len(universe), "results": results[:80], "definition": {')
p.write_text(s,encoding='utf-8',newline='\n')
print('v0.4 backend patch applied')
