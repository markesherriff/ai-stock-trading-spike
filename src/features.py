"""Features for the pooled weekly model. Every feature at date t uses data up to and including t's close."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .data import Prices

PATTERN_FLAGS = ["doji", "hammer", "shooting_star", "bull_engulf", "bear_engulf", "bull_harami", "bear_harami"]
REGIME_FEATURES = ["mkt_vol_20", "mkt_trend_200", "mkt_ret_4w", "dispersion_1w"]


def decision_dates(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Last trading day of each calendar week."""
    series = pd.Series(index, index=index)
    return pd.DatetimeIndex(series.groupby(index.to_period("W")).last().values)


def eligibility(prices: Prices, member: pd.DataFrame, dates: pd.DatetimeIndex, min_price: float = 5.0) -> pd.DataFrame:
    """Member on the date, traded that day, price >= min_price, and 252+ days of history."""
    close = prices.close
    history = close.notna().cumsum() >= 252
    ok = member.reindex(index=close.index, columns=close.columns, fill_value=False) & close.notna() & (close >= min_price) & history
    return ok.loc[dates]


def compute_features(prices: Prices, spy_close: pd.Series, dates: pd.DatetimeIndex) -> dict[str, pd.DataFrame]:
    """Wide (dates x symbols) features. Daily series are computed in full, then cut to `dates`."""
    o, h, l, c, v = prices.open, prices.high, prices.low, prices.close, prices.volume
    r = c.pct_change()
    spy = spy_close.reindex(c.index)
    rm = spy.pct_change()
    out: dict[str, pd.DataFrame] = {}

    def put(name: str, frame: pd.DataFrame) -> None:
        out[name] = frame.replace([np.inf, -np.inf], np.nan).loc[dates].astype("float32")

    for name, n in [("ret_1w", 5), ("ret_2w", 10), ("ret_4w", 21), ("ret_12w", 63), ("ret_26w", 126)]:
        put(name, c / c.shift(n) - 1)
    put("mom_12_1", c.shift(21) / c.shift(252) - 1)
    put("vol_20", r.rolling(20).std())
    put("vol_60", r.rolling(60).std())
    cov = r.mul(rm, axis=0).rolling(60).mean() - r.rolling(60).mean().mul(rm.rolling(60).mean(), axis=0)
    put("beta_60", cov.div(rm.rolling(60).var(ddof=0), axis=0))
    put("maxdd_60", c / c.rolling(60).max() - 1)
    put("range_14", ((h - l) / c).rolling(14).mean())
    for n in (20, 50, 200):
        put(f"dist_sma{n}", c / c.rolling(n).mean() - 1)
    put("near_52w_high", c / c.rolling(252).max() - 1)
    gain = r.clip(lower=0).rolling(14).mean()
    loss = (-r.clip(upper=0)).rolling(14).mean()
    put("rsi_14", 100 - 100 / (1 + gain / loss))
    put("dollar_vol_20", np.log((c * v).rolling(20).mean()))
    put("vol_ratio_5_60", v.rolling(5).mean() / v.rolling(60).mean())

    top, bottom = o.where(o > c, c), o.where(o < c, c)
    rng = (h - l).where(h > l)
    body = c - o
    put("body_ratio", body / rng)
    put("upper_wick", (h - top) / rng)
    put("lower_wick", (bottom - l) / rng)
    put("gap", o / c.shift(1) - 1)
    wo, wh, wl = o.shift(4), h.rolling(5).max(), l.rolling(5).min()
    wrange = (wh - wl).where(wh > wl)
    put("week_body_ratio", (c - wo) / wrange)
    put("week_upper_wick", (wh - wo.where(wo > c, c)) / wrange)
    put("week_lower_wick", (wo.where(wo < c, c) - wl) / wrange)

    valid = o.notna() & c.notna() & rng.notna()
    small = (body.abs() / rng) < 0.3
    po, pc = o.shift(1), c.shift(1)
    flags = {
        "doji": (body.abs() / rng) < 0.1,
        "hammer": ((bottom - l) / rng > 0.6) & small & ((h - top) / rng < 0.1),
        "shooting_star": ((h - top) / rng > 0.6) & small & ((bottom - l) / rng < 0.1),
        "bull_engulf": (pc < po) & (c > o) & (o <= pc) & (c >= po),
        "bear_engulf": (pc > po) & (c < o) & (o >= pc) & (c <= po),
        "bull_harami": (pc < po) & (c > o) & (o > pc) & (c < po),
        "bear_harami": (pc > po) & (c < o) & (o < pc) & (c > po),
    }
    for name, cond in flags.items():
        put(name, cond.astype(float).where(valid))
    return out


def regime_features(spy_close: pd.Series, dates: pd.DatetimeIndex) -> pd.DataFrame:
    rm = spy_close.pct_change()
    frame = pd.DataFrame({
        "mkt_vol_20": rm.rolling(20).std(),
        "mkt_trend_200": spy_close / spy_close.rolling(200).mean() - 1,
        "mkt_ret_4w": spy_close / spy_close.shift(21) - 1,
    })
    return frame.reindex(dates)


def build_dataset(features: dict[str, pd.DataFrame], regime: pd.DataFrame, elig: pd.DataFrame) -> pd.DataFrame:
    """Stack eligible (date, symbol) rows; rank-normalize stock features per date; add regime columns."""
    dates, symbols = elig.index, elig.columns
    rows, cols = np.where(elig.to_numpy())
    index = pd.MultiIndex.from_arrays([dates[rows], symbols[cols]], names=["date", "symbol"])
    data = {}
    for name, wide in features.items():
        masked = wide.where(elig)
        if name not in PATTERN_FLAGS:
            masked = masked.rank(axis=1, pct=True) - 0.5
        data[name] = masked.to_numpy()[rows, cols]
    frame = pd.DataFrame(data, index=index)
    dispersion = features["ret_1w"].where(elig).std(axis=1).reindex(dates)
    for name in regime.columns:
        frame[name] = regime[name].to_numpy()[rows]
    frame["dispersion_1w"] = dispersion.to_numpy()[rows]
    return frame
