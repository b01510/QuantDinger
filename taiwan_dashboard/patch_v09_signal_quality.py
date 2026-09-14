from pathlib import Path

p = Path('/app/app.py') if Path('/app/app.py').exists() else Path('app.py')
s = p.read_text(encoding='utf-8')
s = s.replace('version="0.8.1"', 'version="0.9.0"')
s = s.replace('"version": "0.8.1"', '"version": "0.9.0"')
s = s.replace('台股研究版 v0.8.1', '台股研究版 v0.9')

marker = '@app.get("/api/scanner")\ndef scanner(scope: str="popular"):'
block = r'''_REGIME_CACHE={"ts":0.0,"value":None}
_scan_one_v08 = scan_one


def get_market_regime():
    now=time.time()
    if _REGIME_CACHE["value"] and now-_REGIME_CACHE["ts"]<600:
        return _REGIME_CACHE["value"]
    items=[]
    for ticker,label in [("^TWII","加權指數"),("^TWOII","櫃買指數")]:
        try:
            d=_yahoo_chart(ticker,period="6mo",interval="1d")
            if d is None or len(d)<65: continue
            close=float(d["Close"].iloc[-1]); ma20=float(d["Close"].rolling(20).mean().iloc[-1]); ma60=float(d["Close"].rolling(60).mean().iloc[-1])
            ma20_old=float(d["Close"].rolling(20).mean().iloc[-6])
            points=(1 if close>ma20 else -1)+(1 if close>ma60 else -1)+(1 if ma20>ma20_old else -1)
            items.append({"ticker":ticker,"name":label,"close":_f(close),"ma20":_f(ma20),"ma60":_f(ma60),"points":points})
        except Exception:
            pass
    avg=sum(x["points"] for x in items)/len(items) if items else 0
    regime="多頭" if avg>=1.5 else ("防守" if avg<=-1 else "中性")
    adj=5 if regime=="多頭" else (-8 if regime=="防守" else 0)
    note="可正常找回測機會" if regime=="多頭" else ("降低部位，僅保留高品質訊號" if regime=="防守" else "提高選股門檻")
    value={"regime":regime,"score_adjustment":adj,"note":note,"indices":items}
    _REGIME_CACHE.update({"ts":now,"value":value})
    return value


def scan_one(code: str):
    row=_scan_one_v08(code)
    if not row: return None
    try:
        _,d=_download(code,period="9mo",interval="1d")
        if d is None or len(d)<65: return row
        d=d.copy(); close=float(d["Close"].iloc[-1])
        d["MA60"]=d["Close"].rolling(60).mean()
        ma60=float(d["MA60"].iloc[-1]) if pd.notna(d["MA60"].iloc[-1]) else None
        dist60=(close/ma60-1)*100 if ma60 else 0.0
        tr=pd.concat([(d["High"]-d["Low"]),(d["High"]-d["Close"].shift()).abs(),(d["Low"]-d["Close"].shift()).abs()],axis=1).max(axis=1)
        atr=float(tr.rolling(14).mean().iloc[-1]) if pd.notna(tr.rolling(14).mean().iloc[-1]) else 0.0
        atr_pct=atr/close*100 if close else 0.0
        surge_date=str(row.get("surge_date") or "")
        idxs=[i for i,x in enumerate(d.index) if pd.Timestamp(x).strftime("%Y-%m-%d")==surge_date]
        si=idxs[-1] if idxs else max(20,len(d)-10)
        pre_i=max(0,si-20)
        pre20=(float(d["Close"].iloc[si])/float(d["Close"].iloc[pre_i])-1)*100 if si>pre_i else 0.0
        surge_low=float(d["Low"].iloc[si])
        swing_slice=d["Low"].iloc[max(0,len(d)-11):max(1,len(d)-1)]
        swing_low=float(swing_slice.min()) if len(swing_slice) else surge_low
        structural=max(surge_low,swing_low)
        stop=max(0.01,structural-0.35*atr)
        risk=max(0.0,(close-stop)/close*100) if close else 0.0
        high60=float(d["High"].tail(60).max())
        near_high=(close/high60-1)*100 if high60 else 0.0
        overheated=bool(pre20>35 or dist60>30)
        warm=bool(not overheated and (pre20>20 or dist60>18))
        regime=get_market_regime(); adj=float(regime.get("score_adjustment") or 0)
        penalty=(10 if overheated else (5 if warm else 0))+(6 if risk>8 else (3 if risk>6 else 0))+(4 if atr_pct>6 else 0)
        score=max(0,min(100,float(row.get("score") or 0)+adj-penalty))
        row.update({"name":POPULAR.get(code,row.get("name") or code),"distance_ma60_pct":_f(dist60),"pre_surge_20d_pct":_f(pre20),"near_60d_high_pct":_f(near_high),"atr14":_f(atr),"atr_pct":_f(atr_pct),"structural_floor":_f(structural),"invalidation_price":_f(stop),"risk_to_stop_pct":_f(risk),"overheated":overheated,"warm":warm,"market_regime":regime["regime"],"score":_f(score,1),"quality_grade":"A" if score>=80 else ("B" if score>=65 else ("C" if score>=50 else "D"))})
        reasons=list(row.get("reasons") or [])
        reasons.append("市場"+regime["regime"])
        if overheated: reasons.append("過度延伸")
        elif warm: reasons.append("漲幅偏熱")
        if risk>8: reasons.append("停損距離偏大")
        row["reasons"]=reasons
    except Exception:
        pass
    return row


@app.get("/api/market/regime")
def market_regime_api():
    return get_market_regime()

'''
if marker in s and '_scan_one_v08 = scan_one' not in s:
    s = s.replace(marker, block + marker)

needle='return {"count": len(results), "scanned": len(universe), "cache_stats": dict(_CACHE_STATS), "results": results[:80], "definition": {'
if needle in s:
    s=s.replace(needle,'return {"count": len(results), "scanned": len(universe), "market": get_market_regime(), "cache_stats": dict(_CACHE_STATS), "results": results[:80], "definition": {')

p.write_text(s,encoding='utf-8',newline='\n')
print('v0.9 signal quality patch applied')
