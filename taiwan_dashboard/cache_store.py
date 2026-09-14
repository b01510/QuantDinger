from __future__ import annotations

import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

DATA_DIR = Path(os.environ.get("QD_DATA_DIR", "/app/data"))
DB_PATH = DATA_DIR / "taiwan_market.db"
_LOCK = threading.RLock()


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_bars (
            symbol TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            source TEXT,
            updated_at TEXT,
            PRIMARY KEY(symbol, date)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS symbols (
            symbol TEXT PRIMARY KEY,
            name TEXT,
            market TEXT,
            ticker TEXT,
            updated_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cache_meta (
            symbol TEXT PRIMARY KEY,
            last_checked TEXT,
            last_source TEXT,
            last_error TEXT
        )
        """
    )
    return conn


def init_db() -> None:
    with _LOCK:
        with _connect() as conn:
            conn.commit()


def clean_symbol(symbol: str) -> str:
    s = str(symbol or "").strip().upper()
    return s.replace(".TW", "").replace(".TWO", "")


def upsert_bars(symbol: str, ticker: str, df: pd.DataFrame, source: str = "yahoo") -> int:
    if df is None or df.empty:
        return 0
    code = clean_symbol(symbol)
    now = datetime.now(timezone.utc).isoformat()
    rows = []
    for idx, row in df.iterrows():
        try:
            dt = pd.Timestamp(idx)
            date = dt.strftime("%Y-%m-%d")
            rows.append((
                code, date,
                float(row["Open"]), float(row["High"]), float(row["Low"]), float(row["Close"]),
                int(float(row.get("Volume", 0) or 0)), source, now,
            ))
        except Exception:
            continue
    if not rows:
        return 0
    with _LOCK:
        with _connect() as conn:
            conn.executemany(
                """
                INSERT INTO daily_bars(symbol,date,open,high,low,close,volume,source,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?)
                ON CONFLICT(symbol,date) DO UPDATE SET
                    open=excluded.open, high=excluded.high, low=excluded.low,
                    close=excluded.close, volume=excluded.volume,
                    source=excluded.source, updated_at=excluded.updated_at
                """,
                rows,
            )
            conn.execute(
                """
                INSERT INTO symbols(symbol,ticker,updated_at) VALUES(?,?,?)
                ON CONFLICT(symbol) DO UPDATE SET ticker=excluded.ticker,updated_at=excluded.updated_at
                """,
                (code, ticker, now),
            )
            conn.commit()
    return len(rows)


def load_bars(symbol: str, limit: int = 520) -> pd.DataFrame:
    code = clean_symbol(symbol)
    with _LOCK:
        with _connect() as conn:
            rows = conn.execute(
                """
                SELECT date,open,high,low,close,volume
                FROM daily_bars WHERE symbol=? ORDER BY date DESC LIMIT ?
                """,
                (code, int(limit)),
            ).fetchall()
    if not rows:
        return pd.DataFrame()
    rows.reverse()
    df = pd.DataFrame(rows, columns=["Date", "Open", "High", "Low", "Close", "Volume"])
    df["Date"] = pd.to_datetime(df["Date"])
    return df.set_index("Date")


def cache_info(symbol: str) -> dict:
    code = clean_symbol(symbol)
    with _LOCK:
        with _connect() as conn:
            stat = conn.execute(
                "SELECT COUNT(*),MIN(date),MAX(date),MAX(source) FROM daily_bars WHERE symbol=?",
                (code,),
            ).fetchone()
            meta = conn.execute(
                "SELECT last_checked,last_source,last_error FROM cache_meta WHERE symbol=?",
                (code,),
            ).fetchone()
            sym = conn.execute(
                "SELECT ticker,name,market FROM symbols WHERE symbol=?",
                (code,),
            ).fetchone()
    return {
        "symbol": code,
        "ticker": sym[0] if sym else None,
        "name": sym[1] if sym else None,
        "market": sym[2] if sym else None,
        "rows": int((stat or [0])[0] or 0),
        "first_date": (stat or [None, None])[1],
        "last_date": (stat or [None, None, None])[2],
        "source": (stat or [None, None, None, None])[3],
        "last_checked": meta[0] if meta else None,
        "last_source": meta[1] if meta else None,
        "last_error": meta[2] if meta else None,
    }


def mark_checked(symbol: str, source: str = "yahoo", error: str | None = None) -> None:
    code = clean_symbol(symbol)
    now = datetime.now(timezone.utc).isoformat()
    with _LOCK:
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO cache_meta(symbol,last_checked,last_source,last_error) VALUES(?,?,?,?)
                ON CONFLICT(symbol) DO UPDATE SET
                    last_checked=excluded.last_checked,last_source=excluded.last_source,last_error=excluded.last_error
                """,
                (code, now, source, error),
            )
            conn.commit()


init_db()
