from __future__ import annotations

import math
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import pandas as pd
import requests
import yfinance as yf
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

app = FastAPI(title="QuantDinger Taiwan Edition", version="0.2.0")

POPULAR = {
    "2330": "台積電", "2317": "鴻海", "2454": "聯發科", "2382": "廣達", "3231": "緯創",
    "6669": "緯穎", "3017": "奇鋐", "3324": "雙鴻", "2308": "台達電", "2881": "富邦金",
    "2882": "國泰金", "2891": "中信金", "2603": "長榮", "2615": "萬海", "1301": "台塑",
    "1303": "南亞", "2002": "中鋼", "2303": "聯電", "2379": "瑞昱", "3711": "日月光投控",
    "3008": "大立光", "2345": "智邦", "2392": "正崴", "6278": "台表科", "2313": "華通",
    "2368": "金像電", "2059": "川湖", "3661": "世芯-KY", "3443": "創意", "6488": "環球晶",
    "0050": "元大台灣50", "0056": "元大高股息", "006208": "富邦台50", "00878": "國泰永續高股息",
    "00919": "群益台灣精選高息", "00929": "復華台灣科技優息", "00981A": "主動統一台股增長",
}

_resolve_cache: dict[str, tuple[float, str]] = {}
_YH = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/152 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
    "Referer": "https://finance.yahoo.com/",
}


def _clean_symbol(symbol: str) -> str:
    return str(symbol or "").strip().upper()


def _period_for_yahoo(period: str) -> str:
    p = str(period or "1y").lower()
    return {
        "5d": "5d", "1mo": "1mo", "3mo": "3mo", "6mo": "6mo",
        "9mo": "1y", "1y": "1y", "2y": "2y", "5y": "5y", "10y": "10y",
        "ytd": "ytd", "max": "max",
    }.get(p, "1y")


def _yahoo_chart(candidate: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{candidate}"
    r = requests.get(
        url,
        params={"range": _period_for_yahoo(period), "interval": interval, "includePrePost": "false", "events": "div,splits"},
        headers=_YH,
        timeout=12,
    )
    if not r.ok:
        return pd.DataFrame()
    payload = r.json() or {}
    result = ((payload.get("chart") or {}).get("result") or [])
    if not result:
        return pd.DataFrame()
    item = result[0] or {}
    ts = item.get("timestamp") or []
    quote = (((item.get("indicators") or {}).get("quote") or [{}])[0]) or {}
    if not ts:
        return pd.DataFrame()
    n = len(ts)
    def col(name: str):
        values = quote.get(name) or []
        return list(values) + [None] * max(0, n - len(values))
    df = pd.DataFrame({
        "Open": col("open")[:n],
        "High": col("high")[:n],
        "Low": col("low")[:n],
        "Close": col("close")[:n],
        "Volume": col("volume")[:n],
    }, index=pd.to_datetime(ts, unit="s", utc=True).tz_convert("Asia/Taipei"))
    return df.dropna(subset=["Open", "High", "Low", "Close"])


def _candidate_works(candidate: str) -> bool:
    try:
        df = _yahoo_chart(candidate, period="5d")
        if not df.empty:
            return True
    except Exception:
        pass
    try:
        hist = yf.Ticker(candidate).history(period="5d", interval="1d", auto_adjust=False)
        return hist is not None and not hist.empty
    except Exception:
        return False


def resolve_ticker(symbol: str) -> str:
    s = _clean_symbol(symbol)
    if not s:
        raise ValueError("股票代碼不可為空")
    if s.endswith((".TW", ".TWO")):
        return s
    cached = _resolve_cache.get(s)
    if cached and cached[0] > time.time():
        return cached[1]
    for candidate in (f"{s}.TW", f"{s}.TWO"):
        if _candidate_works(candidate):
            _resolve_cache[s] = (time.time() + 21600, candidate)
            return candidate
    raise ValueError(f"找不到台股代碼 {s}")


def _download(symbol: str, period: str = "1y", interval: str = "1d") -> tuple[str, pd.DataFrame]:
    ticker = resolve_ticker(symbol)
    df = pd.DataFrame()
    try:
        df = _yahoo_chart(ticker, period=period, interval=interval)
    except Exception:
        df = pd.DataFrame()
    if df.empty:
        try:
            df = yf.download(ticker, period=period, interval=interval, auto_adjust=False, progress=False, threads=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [c[0] for c in df.columns]
        except Exception:
            df = pd.DataFrame()
    if df is None or df.empty:
        raise ValueError(f"{symbol} 暫時沒有行情資料")
    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    if df.empty:
        raise ValueError(f"{symbol} 暫時沒有行情資料")
    return ticker, df


def _f(v: Any, ndigits: int = 2):
    try:
        x = float(v)
        if math.isnan(x):
            return None
        return round(x, ndigits)
    except Exception:
        return None


def history_payload(symbol: str, period: str = "1y") -> dict:
    ticker, df = _download(symbol, period=period)
    for n in (5, 10, 20, 60):
        df[f"MA{n}"] = df["Close"].rolling(n).mean()
    rows = []
    for idx, row in df.tail(260).iterrows():
        vol = row.get("Volume", 0)
        rows.append({
            "date": pd.Timestamp(idx).strftime("%Y-%m-%d"),
            "open": _f(row["Open"]), "high": _f(row["High"]), "low": _f(row["Low"]),
            "close": _f(row["Close"]), "volume": int(float(vol)) if pd.notna(vol) else 0,
            "ma5": _f(row.get("MA5")), "ma10": _f(row.get("MA10")),
            "ma20": _f(row.get("MA20")), "ma60": _f(row.get("MA60")),
        })
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    change = float(latest["Close"] - prev["Close"])
    change_pct = change / float(prev["Close"]) * 100 if float(prev["Close"]) else 0
    code = _clean_symbol(symbol).replace(".TW", "").replace(".TWO", "")
    latest_vol = latest.get("Volume", 0)
    return {
        "symbol": code,
        "name": POPULAR.get(code, code),
        "ticker": ticker,
        "last": _f(latest["Close"]), "change": _f(change), "change_pct": _f(change_pct),
        "volume": int(float(latest_vol)) if pd.notna(latest_vol) else 0,
        "rows": rows,
    }


def scan_one(code: str) -> dict | None:
    try:
        ticker, df = _download(code, period="9mo")
        if len(df) < 80:
            return None
        d = df.copy()
        d["MA20"] = d["Close"].rolling(20).mean()
        d["VMA20"] = d["Volume"].rolling(20).mean()
        d["RET"] = d["Close"].pct_change()
        recent = d.iloc[-16:-1].copy()
        cond = (recent["Volume"] >= recent["VMA20"] * 1.8) & (recent["RET"] >= 0.03) & (recent["Close"] > recent["Open"])
        hits = recent[cond]
        if hits.empty:
            return None
        surge_idx = hits.index[-1]
        surge_row = d.loc[surge_idx]
        after = d.loc[surge_idx:].iloc[1:]
        if after.empty:
            return None
        latest = d.iloc[-1]
        ma20 = float(latest["MA20"])
        close = float(latest["Close"])
        low = float(latest["Low"])
        if not ma20 or math.isnan(ma20):
            return None
        proximity = abs(close - ma20) / ma20
        touching = low <= ma20 * 1.02 and close >= ma20 * 0.98 and proximity <= 0.025
        if not touching:
            return None
        prior = after.iloc[:-1]
        prior_touch = False
        if not prior.empty:
            prior_touch = bool(((prior["Low"] <= prior["MA20"] * 1.02) & (prior["Close"] >= prior["MA20"] * 0.98)).any())
        first_pullback = not prior_touch
        volume_ratio = float(surge_row["Volume"] / surge_row["VMA20"]) if surge_row["VMA20"] else 0
        trend20 = (close / float(d.iloc[-21]["Close"]) - 1) * 100
        score = 50 + min(volume_ratio, 5) * 8 + max(0, 20 - proximity * 800) + max(0, min(trend20, 20))
        if first_pullback:
            score += 15
        return {
            "symbol": code, "name": POPULAR.get(code, code), "ticker": ticker,
            "last": _f(close), "ma20": _f(ma20), "distance_ma20_pct": _f((close / ma20 - 1) * 100),
            "surge_date": pd.Timestamp(surge_idx).strftime("%Y-%m-%d"), "volume_ratio": _f(volume_ratio),
            "trend20_pct": _f(trend20), "first_pullback": first_pullback, "score": _f(score, 1),
        }
    except Exception:
        return None


@app.get("/", response_class=HTMLResponse)
def home():
    return HTMLResponse(INDEX_HTML)


@app.get("/api/health")
def health():
    return {"ok": True, "service": "QuantDinger Taiwan Edition", "version": "0.2.0"}


@app.get("/api/search")
def search(q: str = Query(..., min_length=1, max_length=40)):
    raw = q.strip()
    upper = raw.upper()
    local = [
        {"symbol": code, "name": name}
        for code, name in POPULAR.items()
        if upper in code.upper() or raw in name
    ][:12]
    if len(local) >= 8:
        return local
    try:
        r = requests.get(
            "https://query2.finance.yahoo.com/v1/finance/search",
            params={"q": raw, "quotesCount": 15, "newsCount": 0}, timeout=7,
            headers=_YH,
        )
        if r.ok:
            seen = {x["symbol"] for x in local}
            for x in r.json().get("quotes", []):
                sym = str(x.get("symbol") or "").upper()
                if not sym.endswith((".TW", ".TWO")):
                    continue
                code = sym.split(".")[0]
                if code in seen:
                    continue
                name = x.get("shortname") or x.get("longname") or code
                local.append({"symbol": code, "name": name})
                seen.add(code)
                if len(local) >= 12:
                    break
    except Exception:
        pass
    return local


@app.get("/api/history/{symbol}")
def history(symbol: str, period: str = "1y"):
    try:
        return history_payload(symbol, period=period)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/api/scanner")
def scanner():
    results = []
    universe = list(POPULAR.keys())
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(scan_one, code): code for code in universe}
        for f in as_completed(futures):
            row = f.result()
            if row:
                results.append(row)
    results.sort(key=lambda x: (bool(x["first_pullback"]), float(x["score"] or 0)), reverse=True)
    return {"count": len(results), "results": results[:30], "definition": {
        "近期": "最近15個交易日", "爆量": "成交量 >= 20日均量1.8倍",
        "上漲": "單日漲幅 >= 3% 且收紅", "回測": "收盤距20MA 2.5%內，低點碰到20MA附近",
        "第一次回測": "爆量日之後尚未出現過相同20MA回測條件"
    }}


INDEX_HTML = r'''<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>QuantDinger Taiwan Edition</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#0b1020;color:#e8edf7;font-family:Inter,"Noto Sans TC",system-ui,sans-serif}.wrap{max-width:1500px;margin:auto;padding:22px}.top{display:flex;gap:14px;align-items:center;flex-wrap:wrap}.brand{font-size:24px;font-weight:800}.tag{background:#17335f;color:#9fd0ff;padding:5px 10px;border-radius:999px;font-size:12px}.searchbox{position:relative;flex:1;min-width:300px}.searchbox input{width:100%;background:#121a2f;border:1px solid #2a3858;border-radius:12px;padding:13px 15px;color:white;font-size:16px}.results{position:absolute;z-index:10;left:0;right:0;background:#121a2f;border:1px solid #2a3858;border-radius:10px;margin-top:4px;overflow:hidden}.result{padding:10px 12px;cursor:pointer}.result:hover{background:#1b2744}.grid{display:grid;grid-template-columns:2fr 1fr;gap:16px;margin-top:18px}.card{background:#10182a;border:1px solid #202c47;border-radius:16px;padding:16px}.quote{display:flex;gap:16px;align-items:baseline}.price{font-size:36px;font-weight:800}.muted{color:#8d9ab3}.up{color:#ff5b6e}.down{color:#43d18d}button{border:0;border-radius:10px;padding:10px 14px;background:#2d6cdf;color:white;cursor:pointer;font-weight:700}button.secondary{background:#24304a}table{width:100%;border-collapse:collapse;font-size:14px}th,td{padding:10px 8px;border-bottom:1px solid #202c47;text-align:right}th:first-child,td:first-child{text-align:left}tr.click{cursor:pointer}tr.click:hover{background:#16223a}.pill{padding:3px 7px;border-radius:999px;background:#1d3b2d;color:#72e6a6;font-size:12px}.toolbar{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:10px}.defs{font-size:12px;line-height:1.7;color:#9aa7be}.loading{opacity:.65}@media(max-width:980px){.grid{grid-template-columns:1fr}.wrap{padding:12px}}
</style></head><body><div class="wrap">
<div class="top"><div class="brand">QuantDinger Taiwan Edition</div><div class="tag">台股研究版 v0.2</div><div class="searchbox"><input id="q" placeholder="搜尋 2330、台積電、0050…" autocomplete="off"><div id="results" class="results" style="display:none"></div></div></div>
<div class="grid"><div class="card"><div class="quote"><div><div id="title" style="font-size:20px;font-weight:700">2330 台積電</div><div class="muted" id="ticker">2330.TW</div></div><div id="price" class="price">—</div><div id="change">—</div></div><div id="chart" style="height:600px"></div></div>
<div class="card"><div class="toolbar"><div><b>爆量回測 20MA 掃描器</b><div class="muted" style="font-size:12px">先掃常用大型股/熱門ETF</div></div><button id="scanBtn">重新掃描</button></div><div id="scanStatus" class="muted">尚未掃描</div><div style="overflow:auto;max-height:610px"><table><thead><tr><th>股票</th><th>現價</th><th>距20MA</th><th>量比</th><th>分數</th></tr></thead><tbody id="scanRows"></tbody></table></div><div id="defs" class="defs" style="margin-top:12px"></div></div></div>
</div><script>
const q=document.getElementById('q'),results=document.getElementById('results');let timer;
q.addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(async()=>{if(!q.value.trim()){results.style.display='none';return}let r=await fetch('/api/search?q='+encodeURIComponent(q.value));let j=await r.json();results.innerHTML=j.map(x=>`<div class="result" data-s="${x.symbol}"><b>${x.symbol}</b> ${x.name}</div>`).join('');results.style.display=j.length?'block':'none';document.querySelectorAll('.result').forEach(el=>el.onclick=()=>{loadStock(el.dataset.s);q.value='';results.style.display='none'})},250)});
async function loadStock(s){document.getElementById('chart').classList.add('loading');try{let r=await fetch('/api/history/'+encodeURIComponent(s));let j=await r.json();if(!r.ok)throw new Error(j.detail||'讀取失敗');document.getElementById('title').textContent=`${j.symbol} ${j.name}`;document.getElementById('ticker').textContent=j.ticker;document.getElementById('price').textContent=j.last?.toLocaleString()??'—';let c=document.getElementById('change');c.textContent=`${j.change>=0?'+':''}${j.change} (${j.change_pct>=0?'+':''}${j.change_pct}%)`;c.className=j.change>=0?'up':'down';let x=j.rows.map(v=>v.date);let candle={x,open:j.rows.map(v=>v.open),high:j.rows.map(v=>v.high),low:j.rows.map(v=>v.low),close:j.rows.map(v=>v.close),type:'candlestick',name:'K線',increasing:{line:{color:'#ff5b6e'}},decreasing:{line:{color:'#43d18d'}}};let traces=[candle,[5,10,20,60].map(n=>({x,y:j.rows.map(v=>v['ma'+n]),type:'scatter',mode:'lines',name:'MA'+n,line:{width:1}}))].flat();Plotly.newPlot('chart',traces,{paper_bgcolor:'#10182a',plot_bgcolor:'#10182a',font:{color:'#cbd5e1'},margin:{l:55,r:20,t:35,b:40},xaxis:{rangeslider:{visible:false},gridcolor:'#1e2940'},yaxis:{gridcolor:'#1e2940'}},{responsive:true,displaylogo:false})}catch(e){alert(e.message)}finally{document.getElementById('chart').classList.remove('loading')}}
async function scan(){let b=document.getElementById('scanBtn'),st=document.getElementById('scanStatus');b.disabled=true;st.textContent='掃描中，第一次可能需要 20–60 秒…';try{let r=await fetch('/api/scanner');let j=await r.json();st.textContent=`找到 ${j.count} 檔符合條件`;document.getElementById('scanRows').innerHTML=j.results.map(x=>`<tr class="click" data-s="${x.symbol}"><td><b>${x.symbol}</b><br><span class="muted">${x.name}</span>${x.first_pullback?'<br><span class="pill">首次回測</span>':''}</td><td>${x.last??'—'}</td><td>${x.distance_ma20_pct??'—'}%</td><td>${x.volume_ratio??'—'}x</td><td><b>${x.score??'—'}</b></td></tr>`).join('');document.querySelectorAll('tr.click').forEach(el=>el.onclick=()=>loadStock(el.dataset.s));document.getElementById('defs').innerHTML=Object.entries(j.definition).map(([k,v])=>`<b>${k}</b>：${v}`).join('<br>')}catch(e){st.textContent='掃描失敗：'+e.message}finally{b.disabled=false}}
document.getElementById('scanBtn').onclick=scan;loadStock('2330');scan();
</script></body></html>'''