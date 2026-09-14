from pathlib import Path

p = Path('/app/app.py') if Path('/app/app.py').exists() else Path('app.py')
s = p.read_text(encoding='utf-8')

s = s.replace('version="0.8.0"', 'version="0.8.1"')
s = s.replace('"version": "0.8.0"', '"version": "0.8.1"')
s = s.replace('台股研究版 v0.8', '台股研究版 v0.8.1')

old = 'universe = [x["symbol"] for x in get_tw_market_universe()]'
new = 'market_rows = get_tw_market_universe()\n        for item in market_rows:\n            code = str(item.get("symbol") or "").strip().upper()\n            name = str(item.get("name") or code).strip()\n            if code:\n                POPULAR[code] = name or code\n        universe = [x["symbol"] for x in market_rows]'
if old in s:
    s = s.replace(old, new)

css = '''<style id="scanner-readability-v081">
#scanRows td{font-size:15px;line-height:1.5;padding-top:14px;padding-bottom:14px;vertical-align:top}
#scanRows td:first-child{min-width:205px}
#scanRows td:first-child b{font-size:18px;line-height:1.25}
#scanRows .stock-name-v081{font-size:16px;font-weight:700;color:#e8edf7;display:inline-block;margin:2px 0 3px}
#scanRows .muted{font-size:13px!important;line-height:1.45}
#scanRows .pill{font-size:12px;padding:3px 7px}
#scanRows td:nth-child(n+2){font-size:16px;font-weight:700;white-space:nowrap}
#scanTable th{font-size:14px;padding-top:11px;padding-bottom:11px}
</style>'''
if 'scanner-readability-v081' not in s:
    s = s.replace('</head>', css + '</head>')

d = chr(36)
old_name = '<span class="muted">' + d + '{x.name}</span><br>'
new_name = '<span class="stock-name-v081">' + d + '{(x.name&&x.name!==x.symbol)?x.name:"名稱載入中"}</span><br>'
if old_name in s:
    s = s.replace(old_name, new_name)

p.write_text(s, encoding='utf-8', newline='\n')
print('v0.8.1 UI patch applied')
