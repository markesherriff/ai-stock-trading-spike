"""Run the baseline strategies net and gross of costs.

    python -m src.run_baselines [--refresh] [--start 2017-01-03] [--capital 100000]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from . import strategies
from .backtest import calendar_year_returns, run_backtest, summarize
from .costs import ZERO_COST, CostModel
from .data import Prices, load_prices

UNIVERSE = ["SPY", "QQQ", "IWM", "EFA", "EEM", "VNQ", "TLT", "IEF", "GLD", "DBC"]
CASH_PROXY = "BIL"  # 1-3 month T-bill ETF: what uninvested cash would have earned
OUT_DIR = Path(__file__).resolve().parents[1] / "backtests"


def build_decisions(prices, start: str) -> dict[str, pd.DataFrame]:
    return {
        "SPY buy & hold": strategies.buy_and_hold(prices, ["SPY"], start),
        "10-ETF equal weight (monthly)": strategies.equal_weight_monthly(prices, start),
        "SMA-200 trend (monthly)": strategies.sma_trend_monthly(prices, start),
        "Donchian 55/20 breakout": strategies.donchian_breakout(prices, start),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--start", default="2017-01-03")
    parser.add_argument("--capital", type=float, default=100_000.0)
    parser.add_argument("--min-trade", type=float, default=500.0)
    args = parser.parse_args()

    everything = load_prices([*UNIVERSE, CASH_PROXY], "2016-01-04", refresh=args.refresh)
    cash_yield = everything.close[CASH_PROXY].pct_change().fillna(0.0)
    prices = Prices(*(getattr(everything, f)[UNIVERSE] for f in ("open", "high", "low", "close")))
    print(f"Data: {prices.close.index[0].date()} -> {prices.close.index[-1].date()}, {len(prices.close)} days, {len(UNIVERSE)} ETFs")
    net_model = CostModel(plan="tiered", half_spread_bps=2.0)
    rows, years = {}, {}
    OUT_DIR.mkdir(exist_ok=True)

    for name, decisions in build_decisions(prices, args.start).items():
        window_open, window_close = prices.open.loc[args.start:], prices.close.loc[args.start:]
        net = run_backtest(window_open, window_close, decisions, net_model, args.capital, args.min_trade, cash_yield)
        gross = run_backtest(window_open, window_close, decisions, ZERO_COST, args.capital, args.min_trade, cash_yield)
        n, g = summarize(net, cash_yield), summarize(gross, cash_yield)
        rows[name] = {
            "final $": n["final_equity"], "CAGR gross": g["cagr"], "CAGR net": n["cagr"],
            "vol": n["volatility"], "Sharpe": n["sharpe"], "max DD": n["max_drawdown"],
            "trades": n["n_trades"], "turnover/yr": n["turnover_per_year"],
            "costs $": n["total_costs"], "costs %/yr": n["costs_pct_per_year"],
        }
        years[name] = calendar_year_returns(net.equity)
        slug = "".join(c if c.isalnum() else "_" for c in name.lower()).strip("_")
        net.trades.to_csv(OUT_DIR / f"trades_{slug}.csv", index=False)

    table = pd.DataFrame(rows).T
    fmt = {c: "{:.1%}" for c in ["CAGR gross", "CAGR net", "vol", "max DD", "turnover/yr"]}
    fmt["costs %/yr"] = "{:.2%}"
    fmt.update({"final $": "${:,.0f}", "Sharpe": "{:.2f}", "costs $": "${:,.0f}", "trades": "{:.0f}"})
    print("\n" + table.to_string(formatters={k: v.format for k, v in fmt.items()}))
    print("\nCalendar-year net returns:")
    print(pd.DataFrame(years).to_string(float_format=lambda v: f"{v:.1%}"))
    (OUT_DIR / "baselines_summary.json").write_text(json.dumps(rows, indent=2))
    print(f"\nCapital ${args.capital:,.0f}; IBKR Canada tiered fees + 2 bps half-spread per side; cash earns T-bill ETF (BIL) returns; Sharpe is vs that rate.")


if __name__ == "__main__":
    main()
