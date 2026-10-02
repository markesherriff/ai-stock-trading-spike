"""Daily bars from Alpaca market data, adjusted for splits and dividends, cached as parquet."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "data" / "bars"
BARS_URL = "https://data.alpaca.markets/v2/stocks/bars"
FIELDS = ["open", "high", "low", "close", "volume"]


@dataclass
class Prices:
    open: pd.DataFrame
    high: pd.DataFrame
    low: pd.DataFrame
    close: pd.DataFrame
    volume: pd.DataFrame | None = None

    @property
    def symbols(self) -> list[str]:
        return list(self.close.columns)


def _headers() -> dict[str, str]:
    load_dotenv(ROOT / "backend" / ".env")
    key, secret = os.getenv("APCA_API_KEY_ID"), os.getenv("APCA_API_SECRET_KEY")
    if not key or not secret:
        raise RuntimeError("Set APCA_API_KEY_ID / APCA_API_SECRET_KEY (see backend/.env.example)")
    return {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}


def fetch_daily_bars(symbols: list[str], start: str, end: str) -> pd.DataFrame:
    """Long-format bars (symbol, date, open, high, low, close, volume). SIP data is free once >15 min old."""
    headers = _headers()
    params = {
        "symbols": ",".join(symbols),
        "timeframe": "1Day",
        "start": start,
        "end": end,
        "adjustment": "all",
        "feed": "sip",
        "limit": 10000,
        "sort": "asc",
    }
    rows: list[tuple] = []
    page_token = None
    while True:
        page_params = {**params, **({"page_token": page_token} if page_token else {})}
        response = requests.get(BARS_URL, headers=headers, params=page_params, timeout=60)
        response.raise_for_status()
        body = response.json()
        for symbol, bars in (body.get("bars") or {}).items():
            rows.extend((symbol, b["t"], b["o"], b["h"], b["l"], b["c"], b["v"]) for b in bars)
        page_token = body.get("next_page_token")
        if not page_token:
            break
    frame = pd.DataFrame(rows, columns=["symbol", "t", *FIELDS])
    stamp = pd.to_datetime(frame.pop("t"), utc=True).dt.tz_convert("America/New_York")
    frame["date"] = stamp.dt.normalize().dt.tz_localize(None)
    return frame


def _cache_path(symbol: str) -> Path:
    return CACHE_DIR / f"{symbol.replace('/', '_')}.parquet"


def download_bars(symbols: list[str], start: str, end: str, batch: int = 100) -> dict[str, int]:
    """Download and cache bars in batches; symbols with no data are skipped. Returns bars per symbol."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    counts = {s: 0 for s in symbols}
    for i in range(0, len(symbols), batch):
        chunk = symbols[i : i + batch]
        fetched = fetch_daily_bars(chunk, start, end)
        for symbol, part in fetched.groupby("symbol"):
            part.drop(columns="symbol").to_parquet(_cache_path(str(symbol)), index=False)
            counts[str(symbol)] = len(part)
        print(f"  downloaded {min(i + batch, len(symbols))}/{len(symbols)} symbols", flush=True)
    return counts


def load_panel(symbols: list[str]) -> Prices:
    """Wide price panel from the cache for every symbol that has cached bars."""
    present = [s for s in symbols if _cache_path(s).exists()]
    frames = {s: pd.read_parquet(_cache_path(s)).set_index("date") for s in present}
    wide = {f: pd.DataFrame({s: frames[s][f] for s in present}).sort_index() for f in FIELDS}
    index = wide["close"].dropna(how="all").index
    return Prices(*(wide[f].loc[index] for f in ("open", "high", "low", "close")), volume=wide["volume"].loc[index])


def load_prices(symbols: list[str], start: str, end: str | None = None, refresh: bool = False) -> Prices:
    """Load cached bars, downloading any missing symbols (or everything when refresh=True)."""
    end = end or (date.today() - timedelta(days=1)).isoformat()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    missing = [s for s in symbols if refresh or not _cache_path(s).exists()]
    if missing:
        fetched = fetch_daily_bars(missing, start, end)
        for symbol in missing:
            part = fetched[fetched["symbol"] == symbol].drop(columns="symbol")
            if part.empty:
                raise RuntimeError(f"No bars returned for {symbol}")
            part.to_parquet(_cache_path(symbol), index=False)
    frames = {s: pd.read_parquet(_cache_path(s)).set_index("date") for s in symbols}
    wide = {f: pd.DataFrame({s: frames[s][f] for s in symbols}).sort_index() for f in FIELDS}
    index = wide["close"].dropna(how="all").index
    return Prices(*(wide[f].loc[index] for f in ("open", "high", "low", "close")), volume=wide["volume"].loc[index])
