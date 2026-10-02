import numpy as np
import pandas as pd
import pytest

from src import features, model
from src.data import Prices


def synthetic_prices(n=420, symbols=("A", "B", "C"), seed=0) -> tuple[Prices, pd.Series]:
    rng = np.random.default_rng(seed)
    index = pd.bdate_range("2020-01-01", periods=n)
    close = pd.DataFrame(100 * np.cumprod(1 + rng.normal(0, 0.01, (n, len(symbols))), axis=0), index=index, columns=list(symbols))
    open_ = close.shift(1).fillna(close.iloc[0]) * (1 + rng.normal(0, 0.002, close.shape))
    high = np.maximum(open_, close) * 1.005
    low = np.minimum(open_, close) * 0.995
    volume = pd.DataFrame(rng.integers(1_000_000, 5_000_000, close.shape), index=index, columns=close.columns).astype(float)
    spy = pd.Series(100 * np.cumprod(1 + rng.normal(0, 0.008, n)), index=index)
    return Prices(open_, high, low, close, volume), spy


def test_features_never_use_future_data():
    prices, spy = synthetic_prices()
    cut = prices.close.index[330]
    dates = features.decision_dates(prices.close.index)
    dates = dates[(dates >= prices.close.index[270]) & (dates <= cut)]
    before = features.compute_features(prices, spy, dates)
    future = prices.close.index > cut
    rng = np.random.default_rng(9)
    altered = Prices(*(f.copy() for f in (prices.open, prices.high, prices.low, prices.close, prices.volume)))
    for frame in (altered.open, altered.high, altered.low, altered.close, altered.volume):
        frame.loc[future] = frame.loc[future] * rng.uniform(0.5, 2.0, frame.loc[future].shape)
    spy_altered = spy.copy()
    spy_altered.loc[future] = spy_altered.loc[future] * 1.7
    after = features.compute_features(altered, spy_altered, dates)
    for name in before:
        pd.testing.assert_frame_equal(before[name], after[name], check_exact=False, rtol=1e-5, atol=1e-6, obj=name)


def test_forward_returns_start_at_the_open_after_the_decision_date():
    index = pd.bdate_range("2021-01-04", periods=12)
    open_ = pd.DataFrame({"A": np.arange(100.0, 112.0)}, index=index)
    dates = pd.DatetimeIndex([index[0], index[5]])
    fwd = model.forward_returns(open_, dates)
    # decision on day 0 -> enter at day-1 open (101), exit at day-6 open (106)
    assert fwd.loc[index[0], "A"] == pytest.approx(106 / 101 - 1)
    assert np.isnan(fwd.loc[index[5], "A"])  # no following decision date, so no label


def test_walk_forward_training_never_overlaps_the_prediction_block(monkeypatch):
    dates = pd.date_range("2020-01-03", periods=60, freq="W-FRI")
    idx = pd.MultiIndex.from_product([dates, ["A", "B"]], names=["date", "symbol"])
    X = pd.DataFrame({"f": np.random.default_rng(0).normal(size=len(idx))}, index=idx)
    y = pd.Series(np.random.default_rng(1).normal(size=len(idx)), index=idx)
    seen = []

    class Spy:
        def __init__(self, **kwargs): pass
        def fit(self, X_, y_):
            seen.append(X_.index.get_level_values(0).max())
            return self
        def predict(self, X_): return np.zeros(len(X_))

    monkeypatch.setattr(model, "HistGradientBoostingRegressor", Spy)
    first_test = dates[30]
    out = model.walk_forward(X, y, dates, first_test=str(first_test.date()), refit_every=10, purge=2, verbose=False)
    block_starts = dates[dates >= first_test][::10]
    for latest_train, start in zip(seen, block_starts):
        assert latest_train <= dates[dates.get_loc(start) - 2]
    assert out.index.get_level_values(0).min() == first_test


def test_select_portfolio_keeps_holdings_within_the_hold_band():
    symbols = [f"S{i}" for i in range(100)]
    day1 = pd.Series(np.arange(100, 0, -1.0), index=symbols)               # S0 best
    day2 = day1.copy()
    day2["S0"] = day1.iloc[40]                                              # S0 slips to about rank 41
    day3 = day1.copy()
    day3["S0"] = -1.0                                                       # S0 falls out of the band
    scores = pd.concat({pd.Timestamp("2022-01-07"): day1, pd.Timestamp("2022-01-14"): day2,
                        pd.Timestamp("2022-01-21"): day3}, names=["date", "symbol"])
    w = model.select_portfolio(scores, n_buy=30, n_hold=60)
    assert w.loc["2022-01-14", "S0"] > 0 and w.loc["2022-01-21", "S0"] == 0
    assert (w.sum(axis=1).round(9) == 1.0).all() and ((w > 0).sum(axis=1) == 30).all()


def test_eligibility_filters_membership_price_and_history():
    prices, _ = synthetic_prices()
    dates = features.decision_dates(prices.close.index)
    member = pd.DataFrame(True, index=prices.close.index, columns=prices.close.columns)
    member["B"] = False
    prices.close.loc[:, "C"] = 3.0
    elig = features.eligibility(prices, member, dates)
    assert not elig["B"].any() and not elig["C"].any()
    assert not elig["A"].iloc[0] and elig["A"].iloc[-1]  # 252-day history requirement
