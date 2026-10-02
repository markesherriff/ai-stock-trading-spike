"""Alpaca PAPER execution: turn a strategy's target weights into orders, dry-run by default.

    python -m src.live --strategy sma200_trend            # show the plan, place nothing
    python -m src.live --strategy sma200_trend --place-orders
    python -m src.live --strategy spy_hold --force        # ignore the month-end schedule

Orders are market-on-open ("opg") when the market is closed, so they fill at the open as in the backtests.
Only the strategy's own symbols are touched; other positions in the account are left alone.
"""

from __future__ import annotations

import argparse
import json
import math
import uuid
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import requests

from .costs import CostModel
from .data import ROOT, _headers, download_bars, load_panel

PAPER_URL = "https://paper-api.alpaca.markets/v2"
ETF_UNIVERSE = ["SPY", "QQQ", "IWM", "EFA", "EEM", "VNQ", "TLT", "IEF", "GLD", "DBC"]
MIN_TRADE_VALUE = 500.0
LOG_DIR = ROOT / "data" / "live"


class AlpacaPaper:
    """Minimal Alpaca trading client that refuses to talk to anything except the paper endpoint."""

    def __init__(self, base_url: str = PAPER_URL):
        if "paper-api.alpaca.markets" not in base_url:
            raise ValueError("Refusing to use a non-paper Alpaca endpoint")
        self.base_url, self.headers = base_url, _headers()

    def _call(self, method: str, path: str, **kwargs):
        response = requests.request(method, f"{self.base_url}{path}", headers=self.headers, timeout=30, **kwargs)
        response.raise_for_status()
        return response.json()

    def account(self) -> dict:
        return self._call("GET", "/account")

    def positions(self) -> list[dict]:
        return self._call("GET", "/positions")

    def clock(self) -> dict:
        return self._call("GET", "/clock")

    def submit(self, symbol: str, qty: int, side: str, time_in_force: str) -> dict:
        body = {"symbol": symbol, "qty": str(qty), "side": side.lower(), "type": "market",
                "time_in_force": time_in_force, "client_order_id": str(uuid.uuid4())}
        return self._call("POST", "/orders", json=body)


def plan_orders(targets: dict[str, float], managed: set[str], equity: float, positions: dict[str, float],
                prices: dict[str, float], position_values: dict[str, float], cash: float,
                min_trade_value: float = MIN_TRADE_VALUE) -> list[dict]:
    """Whole-share orders (sells first) moving the managed symbols to `targets`.

    Capital is the account equity minus the value of positions outside `managed`, which are never traded.
    """
    capital = equity - sum(v for s, v in position_values.items() if s not in managed)
    orders: list[dict] = []
    for symbol in sorted(managed):
        price = prices.get(symbol)
        if not price or price <= 0:
            continue
        target = math.floor(targets.get(symbol, 0.0) * capital / price)
        delta = target - int(positions.get(symbol, 0))
        if delta == 0 or (abs(delta) * price < min_trade_value and target != 0):
            continue
        orders.append({"symbol": symbol, "side": "SELL" if delta < 0 else "BUY", "qty": abs(delta), "price": price})
    sells = [o for o in orders if o["side"] == "SELL"]
    buys = [o for o in orders if o["side"] == "BUY"]
    budget = (cash + sum(o["qty"] * o["price"] for o in sells)) * 0.995
    needed = sum(o["qty"] * o["price"] for o in buys)
    if needed > budget > 0:
        for o in buys:
            o["qty"] = int(o["qty"] * budget / needed)
        buys = [o for o in buys if o["qty"] > 0]
    return sells + buys


def is_last_trading_day_of_month(last_bar: pd.Timestamp) -> bool:
    return (last_bar + pd.offsets.BDay(1)).month != last_bar.month


def refresh_bars(symbols: list[str]) -> pd.DataFrame:
    end = (date.today() - timedelta(days=1)).isoformat()
    download_bars(symbols, "2016-01-04", end)
    return load_panel(symbols).close


def strategy_sma200_trend() -> tuple[dict[str, float], dict[str, float], set[str], pd.Timestamp, bool]:
    close = refresh_bars(ETF_UNIVERSE)
    above = (close.iloc[-1] > close.rolling(200).mean().iloc[-1]).astype(float)
    weights = (above / len(ETF_UNIVERSE)).to_dict()
    return weights, close.iloc[-1].to_dict(), set(ETF_UNIVERSE), close.index[-1], True


def strategy_spy_hold() -> tuple[dict[str, float], dict[str, float], set[str], pd.Timestamp, bool]:
    close = refresh_bars(["SPY"])
    return {"SPY": 1.0}, close.iloc[-1].to_dict(), {"SPY"}, close.index[-1], False


def strategy_pooled_model():
    raise SystemExit("The pooled weekly model failed its pre-registered validation gate and is not promoted "
                     "to paper trading. See docs/model-results.md.")


STRATEGIES = {"sma200_trend": strategy_sma200_trend, "spy_hold": strategy_spy_hold, "pooled_model": strategy_pooled_model}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", choices=list(STRATEGIES), required=True)
    parser.add_argument("--place-orders", action="store_true", help="actually submit orders (paper account)")
    parser.add_argument("--force", action="store_true", help="rebalance even if not the last trading day of the month")
    args = parser.parse_args()

    weights, prices, managed, as_of, monthly = STRATEGIES[args.strategy]()
    client = AlpacaPaper()
    account, clock = client.account(), client.clock()
    positions = {p["symbol"]: float(p["qty"]) for p in client.positions()}
    values = {p["symbol"]: float(p["market_value"]) for p in client.positions()}
    equity, cash = float(account["equity"]), float(account["cash"])

    print(f"Strategy {args.strategy} | signals as of the {as_of.date()} close | paper equity ${equity:,.2f}, cash ${cash:,.2f}")
    print("Target weights:", {s: round(w, 3) for s, w in weights.items() if w > 0} or "all cash")
    if monthly and not args.force and not is_last_trading_day_of_month(as_of):
        print(f"{as_of.date()} is not the last trading day of its month; nothing to do (use --force to override).")
        return

    orders = plan_orders(weights, managed, equity, positions, prices, values, cash)
    model = CostModel(half_spread_bps=2.0)
    est = sum(model.order_cost(o["side"], o["qty"], o["price"], as_of.date()).total for o in orders)
    for o in orders:
        print(f"  {o['side']:4} {o['qty']:>5} {o['symbol']:<5} @ ~${o['price']:.2f}  (${o['qty'] * o['price']:,.0f})")
    print(f"{len(orders)} orders, estimated IBKR-style cost ${est:,.2f}" if orders else "Already on target; no orders.")

    tif = "day" if clock["is_open"] else "opg"
    record = {"strategy": args.strategy, "as_of": str(as_of.date()), "run_at": datetime.now(timezone.utc).isoformat(),
              "mode": "placed" if args.place_orders else "dry-run", "time_in_force": tif, "equity": equity, "cash": cash,
              "targets": weights, "prices": prices, "positions": positions, "orders": orders, "responses": []}
    if args.place_orders and orders:
        for o in orders:
            resp = client.submit(o["symbol"], o["qty"], o["side"], tif)
            record["responses"].append({"symbol": o["symbol"], "id": resp.get("id"), "status": resp.get("status")})
            print(f"  submitted {o['side']} {o['qty']} {o['symbol']} ({tif}) -> {resp.get('status')}")
    elif orders:
        print("DRY RUN: nothing was sent. Re-run with --place-orders to submit to the paper account.")
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / f"{datetime.now():%Y%m%d_%H%M%S}_{args.strategy}.json").write_text(json.dumps(record, indent=2, default=str))


if __name__ == "__main__":
    main()
