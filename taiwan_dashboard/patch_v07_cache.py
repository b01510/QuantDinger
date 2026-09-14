from pathlib import Path

p=Path('/app/app.py') if Path('/app/app.py').exists() else Path('app.py')
s=p.read_text(encoding='utf-8')
s=s.replace('version="0.6.0"','version="0.7.0"').replace('"version": "0.6.0"','"version": "0.7.0"').replace('台股研究版 v0.6','台股研究版 v0.7')

imports='''\nfrom datetime import datetime, timedelta, timezone\nfrom zoneinfo import ZoneInfo\nimport threading\nfrom cache_store import load_bars, upsert_bars, cache_info, mark_checked, clean_symbol\n'''
needle='from fastapi.responses import HTMLResponse\n'
if imports.strip() not in s:
    s=s.replace(needle, needle+imports)

anchor='''def _f(v: Any, ndigits: int = 2):'''
cache_layer=r'''_network_download = _download
_RAM_BAR_CACHE = {}
_RAM_CACHE_TTL = 120
_DOWNLOAD_LOCK = threading.Lock()
_LAST_NETWORK_AT = 0.0
_CACHE_STATS = {"ram_hits":0,"sqlite_hits":0,"network_full":0,"network_incremental":0,"stale_fallback":0,"errors":0}


def _required_rows(period: str) -> int:
    return {"5d":2,"1mo":15,"3mo":45,"6mo":90,"9mo":120,"1y":180,"2y":360,"5y":900,"10y":1800,"max":180}.get(str(period).lower(),180)


def _cache_limit(period: str) -> int:
    need=_required_rows(period)
    return max(260, min(2600, need+120))


def _expected_latest_date() -> str:
    now=datetime.now(ZoneInfo("Asia/Taipei"))
    d=now.date()
    if now.hour<14 or (now.hour==14 and now.minute<30):
        d=d-timedelta(days=1)
    while d.weekday()>=5:
        d=d-timedelta(days=1)
    return d.isoformat()


def _checked_recently(info: dict, minutes: int=120) -> bool:
    raw=info.get("last_checked")
    if not raw: return False
    try:
        dt=datetime.fromisoformat(raw)
        if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc)-dt < timedelta(minutes=minutes)
    except Exception:
        return False


def _throttle():
    global _LAST_NETWORK_AT
    with _DOWNLOAD_LOCK:
        now=time.time(); wait=max(0.0,0.12-(now-_LAST_NETWORK_AT))
        if wait: time.sleep(wait)
        _LAST_NETWORK_AT=time.time()


def _read_cached(symbol: str, period: str):
    df=load_bars(symbol,limit=_cache_limit(period))
    if df is None or df.empty: return df
    need=_required_rows(period)
    return df.tail(max(need,260)) if len(df)>max(need,260) else df


def _download(symbol: str, period: str="1y", interval: str="1d"):
    if interval!="1d":
        return _network_download(symbol,period=period,interval=interval)
    code=clean_symbol(symbol); key=(code,str(period).lower())
    ram=_RAM_BAR_CACHE.get(key)
    if ram and ram[0]>time.time():
        _CACHE_STATS["ram_hits"]+=1
        return ram[1],ram[2].copy()

    cached=_read_cached(code,period); info=cache_info(code); need=_required_rows(period)
    enough=cached is not None and len(cached)>=need
    fresh=enough and info.get("last_date") and info["last_date"]>=_expected_latest_date()
    if enough and (fresh or _checked_recently(info)):
        ticker=(info.get("symbol") or code)+(".TWO" if str(symbol).upper().endswith('.TWO') else '.TW')
        try: ticker=resolve_ticker(symbol)
        except Exception: pass
        _CACHE_STATS["sqlite_hits"]+=1
        _RAM_BAR_CACHE[key]=(time.time()+_RAM_CACHE_TTL,ticker,cached.copy())
        return ticker,cached

    try:
        if enough:
            _throttle(); ticker,inc=_network_download(symbol,period="5d",interval="1d")
            upsert_bars(code,ticker,inc,source="yahoo")
            mark_checked(code,"yahoo",None)
            merged=_read_cached(code,period)
            _CACHE_STATS["network_incremental"]+=1
            _RAM_BAR_CACHE[key]=(time.time()+_RAM_CACHE_TTL,ticker,merged.copy())
            return ticker,merged
        _throttle(); ticker,full=_network_download(symbol,period=period,interval="1d")
        upsert_bars(code,ticker,full,source="yahoo")
        mark_checked(code,"yahoo",None)
        merged=_read_cached(code,period)
        _CACHE_STATS["network_full"]+=1
        _RAM_BAR_CACHE[key]=(time.time()+_RAM_CACHE_TTL,ticker,merged.copy())
        return ticker,merged
    except Exception as exc:
        _CACHE_STATS["errors"]+=1
        mark_checked(code,"yahoo",str(exc)[:240])
        if enough:
            _CACHE_STATS["stale_fallback"]+=1
            ticker=str(symbol).upper() if str(symbol).upper().endswith((".TW",".TWO")) else code+".TW"
            _RAM_BAR_CACHE[key]=(time.time()+60,ticker,cached.copy())
            return ticker,cached
        raise


@app.get("/api/cache/status/{symbol}")
def cache_status(symbol: str):
    return cache_info(symbol)


@app.get("/api/cache/stats")
def cache_stats():
    return {"stats":dict(_CACHE_STATS),"database":"/app/data/taiwan_market.db","expected_latest":_expected_latest_date()}


'''
if anchor in s and '_network_download = _download' not in s:
    s=s.replace(anchor,cache_layer+anchor)

# Add cache information to stock history payload without changing existing consumers.
old='''        "volume": int(float(latest_vol)) if pd.notna(latest_vol) else 0,\n        "rows": rows,\n    }'''
new='''        "volume": int(float(latest_vol)) if pd.notna(latest_vol) else 0,\n        "cache": cache_info(code),\n        "rows": rows,\n    }'''
if old in s and '"cache": cache_info(code)' not in s:
    s=s.replace(old,new)

# Include cache counters in scanner response.
s=s.replace('return {"count": len(results), "scanned": len(universe), "results": results[:80], "definition": {','return {"count": len(results), "scanned": len(universe), "cache_stats": dict(_CACHE_STATS), "results": results[:80], "definition": {')

p.write_text(s,encoding='utf-8',newline='\n')
print('v0.7 cache patch applied')
