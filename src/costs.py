"""Interactive Brokers Canada cost model for US-listed stocks (USD), plus an assumed spread.

Mirrors backend/src/brokers/ibkrCanada.ts (IBKR Canada commissions pages, read 2026-10-02).
Canadian DIY accounts can only API-trade US-listed securities (CIRO Rule 3200).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

TIERED_PER_SHARE, TIERED_MIN = 0.0035, 0.35
FIXED_PER_SHARE, FIXED_MIN = 0.005, 1.00
MAX_PCT_OF_TRADE_VALUE = 0.01
CLEARING_PER_SHARE = 0.0002
PASS_THROUGH_RATE = 0.000175 + 0.000563
SEC_FEE_RATE = 0.0000206
CAT_FEE_PER_SHARE = 0.000003
TAF_PER_SHARE, TAF_CAP = 0.000195, 9.79
TAF_HOLIDAY = (date(2026, 10, 1), date(2026, 12, 31))


@dataclass(frozen=True)
class OrderCost:
    commission: float = 0.0
    exchange_and_clearing: float = 0.0
    regulatory: float = 0.0
    spread: float = 0.0

    @property
    def total(self) -> float:
        return self.commission + self.exchange_and_clearing + self.regulatory + self.spread


@dataclass(frozen=True)
class CostModel:
    plan: str = "tiered"
    half_spread_bps: float = 2.0
    exchange_fee_per_share: float = 0.003  # assumed: every fill removes liquidity
    enabled: bool = True

    def order_cost(self, side: str, shares: int, price: float, on: date) -> OrderCost:
        if not self.enabled or shares <= 0:
            return OrderCost()
        value = shares * price
        raw, minimum = (
            (TIERED_PER_SHARE * shares, TIERED_MIN)
            if self.plan == "tiered"
            else (FIXED_PER_SHARE * shares, FIXED_MIN)
        )
        commission = min(max(raw, minimum), MAX_PCT_OF_TRADE_VALUE * value)
        exchange = self.exchange_fee_per_share * shares
        clearing = CLEARING_PER_SHARE * shares if self.plan == "tiered" else 0.0
        pass_through = commission * PASS_THROUGH_RATE if self.plan == "tiered" else 0.0

        in_holiday = TAF_HOLIDAY[0] <= on <= TAF_HOLIDAY[1]
        sec = SEC_FEE_RATE * value if side == "SELL" else 0.0
        taf = min(TAF_PER_SHARE * shares, TAF_CAP) if side == "SELL" and not in_holiday else 0.0
        cat = CAT_FEE_PER_SHARE * shares
        return OrderCost(
            commission=commission,
            exchange_and_clearing=exchange + clearing + pass_through,
            regulatory=sec + taf + cat,
            spread=self.half_spread_bps / 10_000 * value,
        )


ZERO_COST = CostModel(enabled=False)
