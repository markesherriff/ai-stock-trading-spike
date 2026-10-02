"""Baseline strategies that return `decisions` (decision date -> target weights) for the engine.

Parameters are classic textbook values fixed in advance (SMA 200; Donchian 55-day entry / 20-day exit),
so each baseline counts as ONE trial when judging overfitting.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .data import Prices


def _first_on_or_after(index: pd.DatetimeIndex, start: str) -> pd.Timestamp:
    return index[index >= pd.Timestamp(start)][0]


def _month_ends(index: pd.DatetimeIndex, start: str) -> pd.DatetimeIndex:
    s = pd.Series(index, index=index)
    last = s.groupby([index.year, index.month]).last()
    return pd.DatetimeIndex([d for d in last.values if d >= pd.Timestamp(start)])


def buy_and_hold(prices: Prices, symbols: list[str], start: str) -> pd.DataFrame:
    weights = pd.DataFrame(0.0, index=[_first_on_or_after(prices.close.index, start)], columns=prices.symbols)
    weights.loc[:, symbols] = 1.0 / len(symbols)
    return weights


def equal_weight_monthly(prices: Prices, start: str) -> pd.DataFrame:
    first = _first_on_or_after(prices.close.index, start)
    dates = pd.DatetimeIndex([first]).append(_month_ends(prices.close.index, start)).unique()
    return pd.DataFrame(1.0 / len(prices.symbols), index=dates, columns=prices.symbols)


def sma_trend_monthly(prices: Prices, start: str, lookback: int = 200) -> pd.DataFrame:
    """Hold an asset (1/N of capital) while its close is above its SMA at month end, else cash."""
    close = prices.close
    above = (close > close.rolling(lookback).mean()).astype(float)
    first = _first_on_or_after(close.index, start)
    dates = pd.DatetimeIndex([first]).append(_month_ends(close.index, start)).unique()
    return above.loc[dates] / len(close.columns)


def donchian_breakout(prices: Prices, start: str, entry: int = 55, exit_: int = 20) -> pd.DataFrame:
    """Enter when the close exceeds the prior `entry`-day high; exit when it falls below the prior `exit_`-day low."""
    close = prices.close
    upper = prices.high.rolling(entry).max().shift(1)
    lower = prices.low.rolling(exit_).min().shift(1)
    state = pd.DataFrame(np.nan, index=close.index, columns=close.columns)
    state = state.mask(close > upper, 1.0).mask(close < lower, 0.0).ffill().fillna(0.0)
    first = _first_on_or_after(close.index, start)
    state = state.loc[first:]
    changed = (state != state.shift(1)).any(axis=1)
    changed.iloc[0] = True
    return state[changed] / len(close.columns)
