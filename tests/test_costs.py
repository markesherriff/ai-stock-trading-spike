from datetime import date

import pytest

from src.costs import CostModel

NO_SPREAD = {"half_spread_bps": 0.0}
HOLIDAY = date(2026, 10, 2)  # IBKR TAF fee holiday, same date as the live AAPL fills


# Expected totals are the figures the TypeScript backend produced for the two real AAPL fills.
@pytest.mark.parametrize(
    "plan, side, price, expected",
    [
        ("tiered", "BUY", 330.90, 0.353461),
        ("tiered", "SELL", 331.10, 0.360282),
        ("fixed", "BUY", 330.90, 1.003003),
        ("fixed", "SELL", 331.10, 1.009824),
    ],
)
def test_matches_typescript_backend(plan, side, price, expected):
    cost = CostModel(plan=plan, **NO_SPREAD).order_cost(side, 1, price, HOLIDAY)
    assert cost.total == pytest.approx(expected, abs=1e-6)


def test_taf_applies_outside_holiday_on_sells_only():
    model = CostModel(**NO_SPREAD)
    sell = model.order_cost("SELL", 100, 50.0, date(2026, 6, 1))
    buy = model.order_cost("BUY", 100, 50.0, date(2026, 6, 1))
    assert sell.regulatory == pytest.approx(0.0000206 * 5000 + 0.000195 * 100 + 0.000003 * 100)
    assert buy.regulatory == pytest.approx(0.000003 * 100)


def test_cap_beats_minimum_for_tiny_trades():
    # IBKR: if 1% of trade value is below the minimum, the cap is charged.
    cost = CostModel(**NO_SPREAD).order_cost("BUY", 10, 0.20, HOLIDAY)
    assert cost.commission == pytest.approx(0.02)


def test_spread_is_half_spread_on_notional():
    cost = CostModel(half_spread_bps=2.0).order_cost("BUY", 100, 100.0, HOLIDAY)
    assert cost.spread == pytest.approx(2.0)


def test_disabled_model_is_free():
    assert CostModel(enabled=False).order_cost("BUY", 100, 100.0, HOLIDAY).total == 0.0
