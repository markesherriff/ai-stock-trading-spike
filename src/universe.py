"""Point-in-time S&P 500 membership.

Source: github.com/fja05680/sp500 (`sp500_ticker_start_end.csv`), an open dataset of membership
intervals. Spot-checked against known events (TSLA added 2020-12-21, TWX removed 2018-06-15) and
membership counts (503-506 on every date tested). It is third-party data, not an S&P product.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests

from .data import ROOT

URL = "https://raw.githubusercontent.com/fja05680/sp500/master/sp500_ticker_start_end.csv"
PATH = ROOT / "data" / "universe" / "sp500_start_end.csv"


def load_membership(refresh: bool = False) -> pd.DataFrame:
    PATH.parent.mkdir(parents=True, exist_ok=True)
    if refresh or not PATH.exists():
        response = requests.get(URL, timeout=60)
        response.raise_for_status()
        PATH.write_bytes(response.content)
    frame = pd.read_csv(PATH, parse_dates=["start_date", "end_date"])
    frame["ticker"] = frame["ticker"].str.strip()
    return frame


def members_on(membership: pd.DataFrame, day: pd.Timestamp | str) -> list[str]:
    day = pd.Timestamp(day)
    active = (membership["start_date"] <= day) & (membership["end_date"].isna() | (membership["end_date"] > day))
    return sorted(membership.loc[active, "ticker"].unique())


def tickers_since(membership: pd.DataFrame, start: str) -> list[str]:
    """Every ticker that was a member at any point on or after `start`."""
    keep = membership["end_date"].isna() | (membership["end_date"] >= pd.Timestamp(start))
    return sorted(membership.loc[keep, "ticker"].unique())
