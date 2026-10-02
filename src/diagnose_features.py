"""Exploratory diagnostics for the pooled model (NOT used to tune it; see docs/model-validation-plan.md).

    python -m src.diagnose_features
"""

from __future__ import annotations

import pandas as pd

from . import features as F
from . import model as M
from . import stats
from .data import load_panel, load_prices
from .backtest import run_backtest, summarize
from .costs import CostModel
from .run_model import CAPITAL, FIRST_TEST, MIN_TRADE, backtest, membership_mask
from .universe import load_membership, tickers_since


def main() -> None:
    membership = load_membership()
    panel = load_panel(tickers_since(membership, "2016-01-04"))
    etf = load_prices(["SPY"], "2016-01-04")
    idx = panel.close.index
    spy = etf.close["SPY"].reindex(idx).ffill()
    dates = F.decision_dates(idx)
    dates = dates[dates >= pd.Timestamp("2017-01-01")]
    elig = F.eligibility(panel, membership_mask(membership, idx, panel.close.columns), dates)
    X = F.build_dataset(F.compute_features(panel, spy, dates), F.regime_features(spy, dates), elig)
    open_ff, _ = M.execution_prices(panel)
    y_raw = M.stack_like(M.forward_returns(open_ff, dates), X.index)
    test = X.index.get_level_values(0) >= pd.Timestamp(FIRST_TEST)

    rows = {}
    for col in X.columns:
        if col in F.REGIME_FEATURES:
            continue
        ic = stats.weekly_rank_ic(X.loc[test, col], y_raw[test])
        s = stats.ic_summary(ic)
        rows[col] = (s["mean_ic"], s["t_stat"])
    table = pd.DataFrame(rows, index=["mean IC", "t-stat"]).T.sort_values("t-stat")
    print("Single-feature weekly rank IC vs next-week return, 2020-2026 (negative = high value predicts LOW return):")
    print(table.to_string(float_format=lambda v: f"{v:.3f}"))

    reversal_check(X, y_raw, open_ff, panel, etf, idx, dates)

    scores = pd.read_parquet("backtests/model_scores.parquet")["score"]
    ic = stats.weekly_rank_ic(scores, y_raw.loc[scores.index])
    print("\nModel weekly IC by year:")
    by_year = ic.groupby(ic.index.get_level_values(0).year).agg(["mean", "count"])
    print(by_year.to_string(float_format=lambda v: f"{v:.4f}"))


def reversal_check(X, y_raw, open_ff, panel, etf, idx, dates) -> None:
    """Hypothesis found in 2020-2026 (examined), re-checked on 2017-2019 (never examined). Long-only top 30 by -ret_1w."""
    _, close_ff = M.execution_prices(panel)
    bil = load_prices(["BIL"], "2016-01-04").close["BIL"].reindex(idx).ffill()
    cash = bil.pct_change().fillna(0.0)
    cost = CostModel(half_spread_bps=3.0)
    periods = {"2017-2019 (never examined)": ("2017-01-01", "2019-12-31"), "2020-2026 (where it was found)": ("2020-01-01", "2026-12-31")}
    print("\nReversal hypothesis (top 30 by lowest 1-week return, net of IBKR tiered + 3 bps):")
    for label, (a, b) in periods.items():
        d = X.index.get_level_values(0)
        sel = (d >= pd.Timestamp(a)) & (d <= pd.Timestamp(b))
        ic = stats.ic_summary(stats.weekly_rank_ic(-X.loc[sel, "ret_1w"], y_raw[sel]))
        weights = M.select_portfolio(-X.loc[sel, "ret_1w"])
        res = backtest(weights, open_ff, close_ff, cost, cash)
        gross = backtest(weights, open_ff, close_ff, CostModel(enabled=False), cash)
        first = weights.index[0]
        spy = run_backtest(etf.open[["SPY"]].reindex(idx).loc[first:weights.index[-1]], etf.close[["SPY"]].reindex(idx).ffill().loc[first:weights.index[-1]],
                           pd.DataFrame({"SPY": [1.0]}, index=[first]), cost, CAPITAL, MIN_TRADE, cash)
        r, g, sp = summarize(res, cash), summarize(gross, cash), summarize(spy, cash)
        print(f"  {label}: IC {ic['mean_ic']:+.3f} (t={ic['t_stat']:.1f}) | CAGR net {r['cagr']:.1%} gross {g['cagr']:.1%} "
              f"| Sharpe {r['sharpe']:.2f} | max DD {r['max_drawdown']:.1%} | turnover {r['turnover_per_year']:.0%}/yr | costs {r['costs_pct_per_year']:.2%}/yr "
              f"|| SPY CAGR {sp['cagr']:.1%} Sharpe {sp['sharpe']:.2f}")


if __name__ == "__main__":
    main()
