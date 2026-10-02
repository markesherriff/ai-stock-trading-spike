"""Labels, walk-forward training and portfolio selection for the pooled weekly model."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from .data import Prices

# Fixed in advance (see docs/model-validation-plan.md). No tuning.
MODEL_PARAMS = dict(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=500,
                    l2_regularization=1.0, max_features=0.7, early_stopping=False, random_state=0)


def execution_prices(prices: Prices) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Open/close panels for trading: a delisted stock keeps its last traded price (exit at last price)."""
    close = prices.close.ffill()
    open_ = prices.open.fillna(prices.close.ffill())
    return open_, close


def forward_returns(open_: pd.DataFrame, dates: pd.DatetimeIndex) -> pd.DataFrame:
    """Return from the next open after decision date t to the next open after the following decision date."""
    index = open_.index
    exec_dates = pd.DatetimeIndex([index[index.get_loc(d) + 1] if index.get_loc(d) + 1 < len(index) else pd.NaT for d in dates])
    entry = open_.reindex(exec_dates).to_numpy()
    exit_ = np.vstack([entry[1:], np.full((1, entry.shape[1]), np.nan)])
    return pd.DataFrame(exit_ / entry - 1, index=dates, columns=open_.columns)


def stack_like(wide: pd.DataFrame, index: pd.MultiIndex) -> pd.Series:
    dates, symbols = index.get_level_values(0), index.get_level_values(1)
    r = wide.index.get_indexer(dates)
    c = wide.columns.get_indexer(symbols)
    ok = (r >= 0) & (c >= 0)
    values = np.full(len(index), np.nan)
    values[ok] = wide.to_numpy()[r[ok], c[ok]]
    return pd.Series(values, index=index)


def cross_sectional_rank_target(fwd: pd.Series) -> pd.Series:
    return fwd.groupby(level=0).rank(pct=True) - 0.5


def walk_forward(X: pd.DataFrame, y: pd.Series, dates: pd.DatetimeIndex, first_test: str,
                 refit_every: int = 13, purge: int = 2, verbose: bool = True) -> pd.Series:
    """Expanding-window predictions. Each block of `refit_every` weeks is scored by a model trained only on
    samples at least `purge` weeks older than the block, so no training label overlaps the prediction period."""
    test_dates = dates[dates >= pd.Timestamp(first_test)]
    scores = []
    for i in range(0, len(test_dates), refit_every):
        block = test_dates[i : i + refit_every]
        cutoff_pos = dates.get_loc(block[0]) - purge
        train_dates = dates[: cutoff_pos + 1]
        train_mask = X.index.get_level_values(0).isin(train_dates) & y.notna().to_numpy()
        model = HistGradientBoostingRegressor(**MODEL_PARAMS).fit(X[train_mask], y[train_mask])
        block_mask = X.index.get_level_values(0).isin(block)
        scores.append(pd.Series(model.predict(X[block_mask]), index=X.index[block_mask]))
        if verbose:
            print(f"  refit {block[0].date()}: trained on {int(train_mask.sum()):,} rows through {train_dates[-1].date()}", flush=True)
    return pd.concat(scores)


def select_portfolio(scores: pd.Series, n_buy: int = 30, n_hold: int = 60) -> pd.DataFrame:
    """Equal-weight long-only top `n_buy`, keeping a holding while its rank stays within `n_hold`."""
    wide = scores.unstack()
    held: set[str] = set()
    rows: dict[pd.Timestamp, pd.Series] = {}
    for date, row in wide.iterrows():
        ranks = row.dropna().rank(ascending=False, method="first")
        keep = [s for s in held if s in ranks.index and ranks[s] <= n_hold]
        keep = sorted(keep, key=lambda s: ranks[s])[:n_buy]
        fill = [s for s in ranks.sort_values().index if s not in keep][: n_buy - len(keep)]
        chosen = keep + fill
        held = set(chosen)
        rows[date] = pd.Series(1.0 / len(chosen), index=chosen)
    return pd.DataFrame(rows).T.fillna(0.0)
