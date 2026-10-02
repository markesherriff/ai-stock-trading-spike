import numpy as np
import pandas as pd
import pytest

from src import strategies
from src.backtest import run_backtest, summarize
from src.costs import ZERO_COST, CostModel
from src.data import Prices


def make_prices(closes: dict[str, list[float]], opens: dict[str, list[float]] | None = None) -> Prices:
    n = len(next(iter(closes.values())))
    index = pd.bdate_range("2020-01-01", periods=n)
    close = pd.DataFrame(closes, index=index, dtype=float)
    open_ = pd.DataFrame(opens, index=index, dtype=float) if opens else close.copy()
    return Prices(open=open_, high=close * 1.01, low=close * 0.99, close=close)


def test_executes_at_next_open_not_decision_close():
    prices = make_prices({"A": [100, 100, 100, 100]}, opens={"A": [100, 100, 50, 100]})
    decisions = pd.DataFrame({"A": [1.0]}, index=[prices.close.index[0]])
    result = run_backtest(prices.open, prices.close, decisions, ZERO_COST, 10_000)
    trade = result.trades.iloc[0]
    assert trade["date"] == prices.close.index[1]
    assert trade["price"] == 100  # day-1 open, not day-2's cheaper open


def test_zero_cost_buy_and_hold_tracks_the_asset():
    closes = list(100 * np.cumprod(1 + np.random.default_rng(0).normal(0.0005, 0.01, 250)))
    prices = make_prices({"A": closes})
    decisions = strategies.buy_and_hold(prices, ["A"], "2020-01-01")
    result = run_backtest(prices.open, prices.close, decisions, ZERO_COST, 100_000)
    expected = result.equity.iloc[0] * closes[-1] / closes[0]
    assert result.equity.iloc[-1] == pytest.approx(expected, rel=0.01)


def test_costs_are_charged_and_reduce_equity():
    prices = make_prices({"A": [100.0] * 30})
    decisions = strategies.buy_and_hold(prices, ["A"], "2020-01-01")
    free = run_backtest(prices.open, prices.close, decisions, ZERO_COST, 10_000)
    paid = run_backtest(prices.open, prices.close, decisions, CostModel(), 10_000)
    assert paid.trades["total_cost"].sum() > 0
    assert paid.equity.iloc[-1] == pytest.approx(free.equity.iloc[-1] - paid.trades["total_cost"].sum(), abs=1.0)


def test_cash_never_goes_negative_and_shares_are_whole():
    prices = make_prices({"A": [101.7] * 20, "B": [33.3] * 20})
    decisions = pd.DataFrame({"A": [0.5], "B": [0.5]}, index=[prices.close.index[0]])
    result = run_backtest(prices.open, prices.close, decisions, CostModel(), 1_000)
    assert (result.trades["shares"] == result.trades["shares"].astype(int)).all()
    spent = result.trades.query("side == 'BUY'")[["notional", "total_cost"]].sum().sum()
    assert spent <= 1_000


def test_min_trade_value_suppresses_tiny_rebalances():
    prices = make_prices({"A": [100.0] * 10, "B": [100.0] * 10})
    decisions = pd.DataFrame({"A": [0.5, 0.505], "B": [0.5, 0.495]},
                             index=[prices.close.index[0], prices.close.index[3]])
    result = run_backtest(prices.open, prices.close, decisions, ZERO_COST, 100_000, min_trade_value=1_000)
    assert len(result.trades) == 2  # initial buys only; the 0.5% drift is skipped


def test_donchian_breakout_uses_prior_highs_only():
    closes = [100.0] * 60 + [120.0] + [120.0] * 5
    prices = make_prices({"A": closes})
    decisions = strategies.donchian_breakout(prices, "2020-01-01")
    entry_day = prices.close.index[60]
    assert decisions.index.max() == entry_day
    assert decisions.loc[entry_day, "A"] == 1.0


def test_summarize_reports_costs():
    prices = make_prices({"A": [100.0] * 40})
    decisions = strategies.buy_and_hold(prices, ["A"], "2020-01-01")
    stats = summarize(run_backtest(prices.open, prices.close, decisions, CostModel(), 10_000))
    assert stats["n_trades"] == 1 and stats["total_costs"] > 0


def test_cash_earns_the_supplied_yield():
    prices = make_prices({"A": [100.0] * 11})
    empty = pd.DataFrame(columns=["A"], dtype=float)
    daily = pd.Series(0.001, index=prices.close.index)
    result = run_backtest(prices.open, prices.close, empty, ZERO_COST, 10_000, cash_yield=daily)
    assert result.equity.iloc[-1] == pytest.approx(10_000 * 1.001**11, rel=1e-9)


def test_sharpe_is_measured_against_the_risk_free_rate():
    prices = make_prices({"A": [100.0] * 60})
    empty = pd.DataFrame(columns=["A"], dtype=float)
    rf = pd.Series(0.0004, index=prices.close.index)
    result = run_backtest(prices.open, prices.close, empty, ZERO_COST, 10_000, cash_yield=rf)
    assert summarize(result, rf)["cagr"] > 0
