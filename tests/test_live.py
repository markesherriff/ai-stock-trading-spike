import pandas as pd
import pytest

from src import live


def plan(targets, positions=None, prices=None, equity=100_000.0, cash=100_000.0, managed=None, values=None):
    prices = prices or {"A": 100.0, "B": 50.0}
    positions = positions or {}
    values = values if values is not None else {s: q * prices[s] for s, q in positions.items() if s in prices}
    return live.plan_orders(targets, managed or set(prices), equity, positions, prices, values, cash)


def test_buys_whole_shares_to_target_weight():
    orders = plan({"A": 0.5})
    assert orders == [{"symbol": "A", "side": "BUY", "qty": 500, "price": 100.0}]


def test_sells_come_before_buys_and_exits_are_not_suppressed():
    orders = plan({"B": 0.5}, positions={"A": 10}, cash=0.0, equity=1_000.0)
    assert [o["side"] for o in orders] == ["SELL", "BUY"]
    assert orders[0] == {"symbol": "A", "side": "SELL", "qty": 10, "price": 100.0}


def test_tiny_rebalances_are_skipped_but_full_exits_still_happen():
    assert plan({"A": 0.5}, positions={"A": 498}, equity=100_000.0) == []  # 2 shares ($200) under the minimum
    exit_order = plan({}, positions={"A": 3}, equity=100_000.0)
    assert exit_order == [{"symbol": "A", "side": "SELL", "qty": 3, "price": 100.0}]


def test_positions_outside_the_strategy_are_never_traded_and_reduce_capital():
    prices = {"A": 100.0, "Z": 10.0}
    orders = live.plan_orders({"A": 1.0}, {"A"}, 100_000.0, {"Z": 5000}, prices, {"Z": 50_000.0}, 60_000.0)
    assert orders == [{"symbol": "A", "side": "BUY", "qty": 500, "price": 100.0}]  # capital = 100k - 50k unmanaged


def test_buys_are_scaled_down_to_available_cash():
    orders = plan({"A": 1.0}, equity=100_000.0, cash=10_000.0)
    assert orders[0]["qty"] <= 99 and orders[0]["qty"] * 100.0 <= 10_000.0


def test_month_end_detection():
    assert live.is_last_trading_day_of_month(pd.Timestamp("2026-09-30"))
    assert live.is_last_trading_day_of_month(pd.Timestamp("2026-10-30"))  # Friday; next business day is in November
    assert not live.is_last_trading_day_of_month(pd.Timestamp("2026-10-01"))


def test_client_refuses_non_paper_endpoint():
    with pytest.raises(ValueError):
        live.AlpacaPaper("https://api.alpaca.markets/v2")


def test_failed_model_cannot_be_run():
    with pytest.raises(SystemExit):
        live.strategy_pooled_model()
