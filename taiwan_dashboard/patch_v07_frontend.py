from pathlib import Path

p=Path('/app/app.py') if Path('/app/app.py').exists() else Path('app.py')
s=p.read_text(encoding='utf-8')

old="document.getElementById('ticker').textContent=j.ticker;"
new="let ci=j.cache||{};document.getElementById('ticker').textContent=j.ticker+(ci.last_date?`｜本機資料至 ${ci.last_date}`:'')+(ci.source?`｜來源 ${ci.source}`:'');"
if old not in s:
    raise SystemExit('ticker UI block not found')
s=s.replace(old,new)

old2="st.textContent=`已掃 ${j.scanned??'—'} 檔，找到 ${j.count} 檔符合條件`; "
new2="let cs=j.cache_stats||{};st.textContent=`已掃 ${j.scanned??'—'} 檔，找到 ${j.count} 檔｜RAM ${cs.ram_hits||0}｜SQLite ${cs.sqlite_hits||0}｜網路完整 ${cs.network_full||0}｜增量 ${cs.network_incremental||0}｜備援 ${cs.stale_fallback||0}`; "
if old2 in s:
    s=s.replace(old2,new2)

p.write_text(s,encoding='utf-8',newline='\n')
print('v0.7 frontend patch applied')
