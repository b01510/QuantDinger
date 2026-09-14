from pathlib import Path

p=Path('/app/app.py') if Path('/app/app.py').exists() else Path('app.py')
s=p.read_text(encoding='utf-8')
s=s.replace('version="0.9.0"','version="0.9.1"').replace('"version": "0.9.0"','"version": "0.9.1"').replace('台股研究版 v0.9','台股研究版 v0.9.1')

old='''def _expected_latest_date() -> str:\n    now=datetime.now(ZoneInfo("Asia/Taipei"))\n    d=now.date()\n    if now.hour<14 or (now.hour==14 and now.minute<30):\n        d=d-timedelta(days=1)\n    while d.weekday()>=5:\n        d=d-timedelta(days=1)\n    return d.isoformat()'''
new='''_TRADING_DAY_CACHE={"ts":0.0,"date":None}\n\ndef _roc_date_to_iso(raw: str):\n    try:\n        text=str(raw or "").strip().replace("-","/")\n        parts=text.split("/")\n        if len(parts)!=3: return None\n        y,m,d=(int(parts[0]),int(parts[1]),int(parts[2]))\n        if y<1911: y+=1911\n        return f"{y:04d}-{m:02d}-{d:02d}"\n    except Exception:\n        return None\n\ndef _expected_latest_date() -> str:\n    now=datetime.now(ZoneInfo("Asia/Taipei"))\n    if _TRADING_DAY_CACHE.get("date") and time.time()-float(_TRADING_DAY_CACHE.get("ts") or 0)<1800:\n        return _TRADING_DAY_CACHE["date"]\n    candidate=now.date()\n    if now.hour<14 or (now.hour==14 and now.minute<30):\n        candidate=candidate-timedelta(days=1)\n    found=[]\n    month_starts=[]\n    for back in (0,35):\n        x=candidate-timedelta(days=back)\n        month_starts.append(x.replace(day=1))\n    for month_start in month_starts:\n        try:\n            r=requests.get(\n                "https://www.twse.com.tw/rwd/zh/afterTrading/FMTQIK",\n                params={"date":month_start.strftime("%Y%m%d"),"response":"json"},\n                headers=_YH,timeout=8,\n            )\n            if not r.ok: continue\n            payload=r.json() or {}\n            for row in payload.get("data") or []:\n                if not row: continue\n                iso=_roc_date_to_iso(row[0])\n                if iso and iso<=candidate.isoformat(): found.append(iso)\n        except Exception:\n            pass\n    if found:\n        latest=max(found)\n    else:\n        d=candidate\n        while d.weekday()>=5: d=d-timedelta(days=1)\n        latest=d.isoformat()\n    _TRADING_DAY_CACHE.update({"ts":time.time(),"date":latest})\n    return latest'''
if old in s:
    s=s.replace(old,new)

old_ram='''    ram=_RAM_BAR_CACHE.get(key)\n    if ram and ram[0]>time.time():\n        _CACHE_STATS["ram_hits"]+=1\n        return ram[1],ram[2].copy()'''
new_ram='''    ram=_RAM_BAR_CACHE.get(key)\n    if ram and ram[0]>time.time():\n        try:\n            ram_last=pd.Timestamp(ram[2].index[-1]).strftime("%Y-%m-%d") if ram[2] is not None and not ram[2].empty else ""\n        except Exception:\n            ram_last=""\n        if ram_last>=_expected_latest_date():\n            _CACHE_STATS["ram_hits"]+=1\n            return ram[1],ram[2].copy()\n        _RAM_BAR_CACHE.pop(key,None)'''
if old_ram in s:
    s=s.replace(old_ram,new_ram)

s=s.replace('if enough and (fresh or _checked_recently(info)):', 'if enough and fresh:')
s=s.replace('_network_download(symbol,period="5d",interval="1d")','_network_download(symbol,period="1mo",interval="1d")')

old_payload='''        "cache": cache_info(code),\n        "rows": rows,\n    }'''
new_payload='''        "cache": cache_info(code),\n        "data_as_of": pd.Timestamp(df.index[-1]).strftime("%Y-%m-%d"),\n        "expected_latest": _expected_latest_date(),\n        "data_fresh": pd.Timestamp(df.index[-1]).strftime("%Y-%m-%d") >= _expected_latest_date(),\n        "rows": rows,\n    }'''
if old_payload in s:
    s=s.replace(old_payload,new_payload)

# Add a visible data-date indicator beside the ticker.
quote_old='<div class="muted" id="ticker">2330.TW</div>'
quote_new='<div class="muted" id="ticker">2330.TW</div><div id="dataFreshness" class="muted" style="font-size:12px;margin-top:3px">行情資料：載入中</div>'
if quote_old in s and 'id="dataFreshness"' not in s:
    s=s.replace(quote_old,quote_new)

js_old="document.getElementById('ticker').textContent=j.ticker;"
js_new="document.getElementById('ticker').textContent=j.ticker;let df=document.getElementById('dataFreshness');if(df){df.textContent=`行情截至 ${j.data_as_of||'—'}${j.data_fresh?' ✓ 最新':' ⚠ 尚未更新至 '+(j.expected_latest||'最新交易日')}`;df.style.color=j.data_fresh?'#72e6a6':'#f7c66a';}"
if js_old in s:
    s=s.replace(js_old,js_new)

p.write_text(s,encoding='utf-8',newline='\n')
print('v0.9.1 freshness patch applied')
