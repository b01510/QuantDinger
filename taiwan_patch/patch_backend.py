from pathlib import Path

ROOT = Path('/app')


def replace(path: Path, old: str, new: str, label: str):
    text = path.read_text(encoding='utf-8')
    if new in text:
        print(f'[ok] {label} already patched')
        return
    if old not in text:
        raise RuntimeError(f'Patch anchor not found: {label} in {path}')
    path.write_text(text.replace(old, new), encoding='utf-8')
    print(f'[ok] {label}')


# 1) DataSourceFactory
factory = ROOT / 'app/data_sources/factory.py'
replace(factory,
    '    "hk": "HKStock",\n    "hongkong": "HKStock",\n',
    '    "hk": "HKStock",\n    "hongkong": "HKStock",\n    "twstock": "TWStock",\n    "tw_stock": "TWStock",\n    "taiwan": "TWStock",\n    "taiwanstock": "TWStock",\n    "twse": "TWStock",\n    "tpex": "TWStock",\n',
    'TW market aliases')
replace(factory,
    '    _CANONICAL_MARKETS = ("Crypto", "Forex", "Futures", "USStock", "CNStock", "HKStock", "MOEX")',
    '    _CANONICAL_MARKETS = ("Crypto", "Forex", "Futures", "USStock", "CNStock", "HKStock", "TWStock", "MOEX")',
    'TW canonical market')
replace(factory,
    '        if key in ("usstock", "us_stocks", "stock", "stocks", "ibkr", "alpaca"):\n            return cls.get_source("USStock")\n',
    '        if key in ("usstock", "us_stocks", "stock", "stocks", "ibkr", "alpaca"):\n            return cls.get_source("USStock")\n        if key in ("twstock", "tw_stock", "taiwan", "taiwanstock", "twse", "tpex"):\n            return cls.get_source("TWStock")\n',
    'TW get_data_source aliases')
replace(factory,
    "        elif market == 'USStock':\n            from app.data_sources.us_stock import USStockDataSource\n            return USStockDataSource()\n",
    "        elif market == 'USStock':\n            from app.data_sources.us_stock import USStockDataSource\n            return USStockDataSource()\n        elif market == 'TWStock':\n            from app.data_sources.tw_stock import TWStockDataSource\n            return TWStockDataSource()\n",
    'TW data source factory')

# 2) Market registry / UI market list
registry = ROOT / 'app/markets/registry.py'
replace(registry,
    '    "HKStock",\n    "Forex",\n',
    '    "HKStock",\n    "TWStock",\n    "Forex",\n',
    'TW market order')
anchor = '''    "Forex": MarketModule(\n'''
tw_module = '''    "TWStock": MarketModule(\n        key="TWStock",\n        label="Taiwan Stocks",\n        description="Taiwan listed and OTC equities and ETFs.",\n        asset_class="equity",\n        symbol_hint="2330",\n        base_currency="TWD",\n        features=["research", "backtest", "paper"],\n        data_requirements=[\n            DataRequirement(\n                key="yfinance",\n                label="Yahoo Finance",\n                built_in=True,\n                purpose="quotes and OHLCV",\n            ),\n        ],\n        supports={"spot": True, "swap": False, "short": False, "session": "exchange-hours"},\n    ),\n'''
replace(registry, anchor, tw_module + anchor, 'TW market registry module')

# 3) Visibility
visibility = ROOT / 'app/utils/market_visibility.py'
replace(visibility,
    "    'Crypto', 'USStock', 'CNStock', 'HKStock', 'Forex', 'Futures', 'MOEX',\n",
    "    'Crypto', 'USStock', 'CNStock', 'HKStock', 'TWStock', 'Forex', 'Futures', 'MOEX',\n",
    'TW visibility registry')

# 4) Symbol search. Yahoo search provides TWSE/TPEX names and codes.
symbol_search = ROOT / 'app/services/market/symbol_search.py'
replace(symbol_search,
    '    if market in {"USStock", "CNStock", "HKStock"}:\n',
    '    if market in {"USStock", "CNStock", "HKStock", "TWStock"}:\n',
    'TW external symbol search')
replace(symbol_search,
    '    elif market in {"USStock", "CNStock", "HKStock"}:\n',
    '    elif market in {"USStock", "CNStock", "HKStock", "TWStock"}:\n',
    'TW exact symbol search')
search_anchor = '''\ndef _search_external_symbols(market: str, keyword: str, limit: int, existing: set) -> list:\n'''
tw_search = '''\ndef _search_tw_yahoo(keyword: str, limit: int) -> list:\n    if limit <= 0:\n        return []\n    try:\n        import requests\n        resp = requests.get(\n            "https://query2.finance.yahoo.com/v1/finance/search",\n            params={"q": keyword, "quotesCount": max(limit * 3, 20), "newsCount": 0},\n            timeout=6,\n            headers={"User-Agent": "Mozilla/5.0"},\n        )\n        if resp.status_code != 200:\n            return []\n        kw = str(keyword or "").strip().upper()\n        out = []\n        for quote in (resp.json() or {}).get("quotes") or []:\n            symbol = str(quote.get("symbol") or "").strip().upper()\n            if not symbol.endswith((".TW", ".TWO")):\n                continue\n            quote_type = str(quote.get("quoteType") or "").upper()\n            if quote_type not in {"EQUITY", "ETF"}:\n                continue\n            base_symbol = symbol.rsplit(".", 1)[0]\n            name = str(quote.get("shortname") or quote.get("longname") or quote.get("name") or base_symbol).strip()\n            if kw and kw not in base_symbol.upper() and kw not in name.upper() and kw not in symbol:\n                continue\n            out.append({\n                "market": "TWStock",\n                "symbol": base_symbol,\n                "name": name,\n                "exchange_id": "TWSE" if symbol.endswith(".TW") else "TPEX",\n                "market_type": "spot",\n                "settle_currency": "TWD",\n                "asset_class": "equity",\n                "product_type": "direct_equity",\n                "api_family": "yfinance",\n                "product_meta": {"provider_symbol": symbol},\n            })\n            persist_seed_name("TWStock", base_symbol, name)\n            if len(out) >= limit:\n                break\n        return out\n    except Exception as exc:\n        logger.debug("TW Yahoo symbol search failed: %s", exc)\n        return []\n\n'''
replace(symbol_search, search_anchor, tw_search + search_anchor, 'TW Yahoo symbol search helper')
replace(symbol_search,
    '    elif market == "USStock":\n        rows = _search_us_yahoo(keyword, limit)\n    else:\n',
    '    elif market == "USStock":\n        rows = _search_us_yahoo(keyword, limit)\n    elif market == "TWStock":\n        rows = _search_tw_yahoo(keyword, limit)\n    else:\n',
    'TW external search route')

print('Taiwan stock backend patch completed.')
