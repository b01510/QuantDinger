"""Taiwan stock/ETF data source for QuantDinger.

Uses Yahoo Finance through yfinance.  Symbols may be entered as bare Taiwan
codes (2330, 0050, 00981A) or Yahoo symbols (2330.TW, 6488.TWO).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd
import yfinance as yf

from app.data_sources.base import BaseDataSource
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TWStockDataSource(BaseDataSource):
    name = "TWStock/yfinance"

    INTERVAL_MAP = {
        "1m": "1m",
        "3m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1H": "60m",
        "4H": "60m",
        "1D": "1d",
        "1W": "1wk",
    }

    PERIOD_MAP = {
        "1m": "7d",
        "3m": "7d",
        "5m": "60d",
        "15m": "60d",
        "30m": "60d",
        "1H": "730d",
        "4H": "730d",
        "1D": "10y",
        "1W": "10y",
    }

    @staticmethod
    def _candidate_symbols(symbol: str) -> List[str]:
        raw = str(symbol or "").strip().upper()
        if not raw:
            return []
        if raw.endswith((".TW", ".TWO")):
            return [raw]
        # TWSE first, then TPEx. This also works for most Taiwan-listed ETFs.
        return [f"{raw}.TW", f"{raw}.TWO"]

    @staticmethod
    def _to_epoch(index_value: Any) -> int:
        ts = pd.Timestamp(index_value)
        if ts.tzinfo is None:
            ts = ts.tz_localize("Asia/Taipei")
        return int(ts.tz_convert("UTC").timestamp())

    def _history(self, yahoo_symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        interval = self.INTERVAL_MAP.get(timeframe, "1d")
        period = self.PERIOD_MAP.get(timeframe, "2y")
        df = yf.Ticker(yahoo_symbol).history(
            period=period,
            interval=interval,
            auto_adjust=False,
            actions=False,
            repair=True,
        )
        if df is None or df.empty:
            return pd.DataFrame()
        return df

    def get_kline(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
        before_time: Optional[int] = None,
        after_time: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        timeframe = str(timeframe or "1D")
        rows: List[Dict[str, Any]] = []
        resolved = ""
        for candidate in self._candidate_symbols(symbol):
            try:
                df = self._history(candidate, timeframe, limit)
                if df.empty:
                    continue
                resolved = candidate
                for idx, row in df.iterrows():
                    try:
                        rows.append(
                            self.format_kline(
                                self._to_epoch(idx),
                                row["Open"],
                                row["High"],
                                row["Low"],
                                row["Close"],
                                row.get("Volume", 0),
                            )
                        )
                    except Exception:
                        continue
                break
            except Exception as exc:
                logger.debug("TW stock history failed for %s: %s", candidate, exc)

        if not rows:
            logger.warning("TWStock: no data for %s", symbol)
            return []

        rows = self.filter_and_limit(
            rows,
            limit=max(1, int(limit or 200)),
            before_time=before_time,
            after_time=after_time,
            truncate=after_time is None,
        )
        logger.debug("TWStock resolved %s -> %s (%d bars)", symbol, resolved, len(rows))
        return rows

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        for candidate in self._candidate_symbols(symbol):
            try:
                ticker = yf.Ticker(candidate)
                price = None
                try:
                    price = ticker.fast_info.get("last_price")
                except Exception:
                    pass
                if price is None:
                    hist = ticker.history(period="5d", interval="1d", actions=False)
                    if hist is not None and not hist.empty:
                        price = float(hist["Close"].dropna().iloc[-1])
                if price is not None:
                    return {
                        "symbol": str(symbol).upper(),
                        "provider_symbol": candidate,
                        "last": float(price),
                        "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
                    }
            except Exception as exc:
                logger.debug("TW stock ticker failed for %s: %s", candidate, exc)
        return {"symbol": str(symbol).upper(), "last": 0}
