"""Run the pre-registered pooled weekly model test (docs/model-validation-plan.md).

    python -m src.run_model
"""

from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd

from . import features as F
from . import model as M
from . import stats
from .backtest import calendar_year_returns, run_backtest, summarize
from .costs import ZERO_COST, CostModel
from .data import Prices, load_panel, load_prices
from .universe import load_membership, tickers_since

FIRST_TEST = "2020-01-01"
CAPITAL = 100_000.0
MIN_TRADE = 500.0
OUT = F.__file__.rsplit("/src/", 1)[0] + "/backtests"


def membership_mask(membership: pd.DataFrame, index: pd.DatetimeIndex, columns: pd.Index) -> pd.DataFrame:
    mask = pd.DataFrame(False, index=index, columns=columns)
    for row in membership.itertuples():
        if row.ticker in mask.columns:
            end = row.end_date if pd.notna(row.end_date) else pd.Timestamp.max
            mask.loc[(index >= row.start_date) & (index < end), row.ticker] = True
    return mask


def backtest(weights: pd.DataFrame, open_: pd.DataFrame, close: pd.DataFrame, cost: CostModel, cash: pd.Series):
    cols = weights.columns[(weights > 0).any()]
    start = weights.index[0]
    return run_backtest(open_.loc[start:, cols], close.loc[start:, cols], weights[cols], cost, CAPITAL, MIN_TRADE, cash)


def main() -> None:
    t0 = time.time()
    membership = load_membership()
    panel = load_panel(tickers_since(membership, "2016-01-04"))
    etf = load_prices(["SPY", "BIL"], "2016-01-04")
    idx = panel.close.index
    spy_close = etf.close["SPY"].reindex(idx).ffill()
    cash_yield = etf.close["BIL"].reindex(idx).ffill().pct_change().fillna(0.0)
    print(f"Panel: {panel.close.shape[1]} symbols, {idx[0].date()} -> {idx[-1].date()}", flush=True)

    dates = F.decision_dates(idx)
    dates = dates[dates >= pd.Timestamp("2017-01-01")]
    member = membership_mask(membership, idx, panel.close.columns)
    elig = F.eligibility(panel, member, dates)
    feats = F.compute_features(panel, spy_close, dates)
    regime = F.regime_features(spy_close, dates)
    X = F.build_dataset(feats, regime, elig)
    open_ff, close_ff = M.execution_prices(panel)
    fwd = M.forward_returns(open_ff, dates)
    y_raw = M.stack_like(fwd, X.index)
    y = M.cross_sectional_rank_target(y_raw)
    print(f"Dataset: {len(X):,} rows x {X.shape[1]} features, {len(dates)} weeks ({time.time() - t0:.0f}s)", flush=True)

    print("Walk-forward training:", flush=True)
    scores = M.walk_forward(X, y, dates, FIRST_TEST)
    test_idx = scores.index
    rule_scores = {
        "Model (gradient boosting)": scores,
        "12-1 momentum rule": X.loc[test_idx, "mom_12_1"],
        "Low-volatility rule": -X.loc[test_idx, "vol_60"],
    }

    # Signal quality
    ic_rows, decile_rows = {}, {}
    for name, sc in rule_scores.items():
        ic = stats.weekly_rank_ic(sc, y_raw.loc[sc.index])
        ic_rows[name] = stats.ic_summary(ic)
        decile_rows[name] = stats.decile_returns(sc, y_raw.loc[sc.index])
    ic_table = pd.DataFrame(ic_rows).T
    dec = pd.DataFrame(decile_rows)
    spread = (dec.loc[10] - dec.loc[1]) * 52

    # Portfolios and costs
    weights = {name: M.select_portfolio(sc) for name, sc in rule_scores.items()}
    first = weights["Model (gradient boosting)"].index[0]
    spy_w = pd.DataFrame({"SPY": [1.0]}, index=[first])
    scenarios = {"3 bps": CostModel(half_spread_bps=3.0), "1 bps": CostModel(half_spread_bps=1.0),
                 "5 bps": CostModel(half_spread_bps=5.0), "gross": ZERO_COST}
    results, equity = {}, {}
    for name, w in weights.items():
        for label, cost in scenarios.items():
            if name != "Model (gradient boosting)" and label in ("1 bps", "5 bps"):
                continue
            r = backtest(w, open_ff, close_ff, cost, cash_yield)
            results[(name, label)] = summarize(r, cash_yield)
            equity[(name, label)] = r.equity
        print(f"  backtested {name} ({time.time() - t0:.0f}s)", flush=True)
    for label in ("3 bps", "gross"):
        r = run_backtest(etf.open[["SPY"]].reindex(idx).loc[first:], etf.close[["SPY"]].reindex(idx).ffill().loc[first:],
                         spy_w, scenarios[label], CAPITAL, MIN_TRADE, cash_yield)
        results[("SPY buy & hold", label)] = summarize(r, cash_yield)
        equity[("SPY buy & hold", label)] = r.equity

    table = pd.DataFrame({k: v for k, v in results.items() if k[1] in ("3 bps", "gross")}).T
    net = table.xs("3 bps", level=1)
    gross = table.xs("gross", level=1)
    summary = pd.DataFrame({
        "final $": net["final_equity"], "CAGR net": net["cagr"], "CAGR gross": gross["cagr"], "vol": net["volatility"],
        "Sharpe": net["sharpe"], "max DD": net["max_drawdown"], "turnover/yr": net["turnover_per_year"],
        "costs %/yr": net["costs_pct_per_year"], "trades": net["n_trades"],
    })

    model_net_eq = equity[("Model (gradient boosting)", "3 bps")]
    spy_eq = equity[("SPY buy & hold", "3 bps")]
    mret, sret = model_net_eq.pct_change().dropna(), spy_eq.pct_change().dropna()
    excess = (mret - cash_yield.reindex(mret.index)).dropna()
    ab = stats.alpha_beta(mret - cash_yield.reindex(mret.index), sret - cash_yield.reindex(sret.index))
    dsr = {n: stats.deflated_sharpe(excess, n) for n in (1, 3, 5, 20)}

    gate = {
        "1. mean weekly IC > 0 and t >= 2": bool(ic_table.loc["Model (gradient boosting)", "mean_ic"] > 0
                                                  and ic_table.loc["Model (gradient boosting)", "t_stat"] >= 2),
        "2. net Sharpe > SPY's": bool(net.loc["Model (gradient boosting)", "sharpe"] > net.loc["SPY buy & hold", "sharpe"]),
        "3. DSR (5 trials) >= 0.95": bool(dsr[5] >= 0.95),
    }

    pd.options.display.width = 200
    fmt = {c: "{:.1%}".format for c in ["CAGR net", "CAGR gross", "vol", "max DD", "turnover/yr"]}
    fmt.update({"final $": "${:,.0f}".format, "Sharpe": "{:.2f}".format, "costs %/yr": "{:.2%}".format, "trades": "{:.0f}".format})
    print(f"\nTest window: {first.date()} -> {idx[-1].date()}  | capital ${CAPITAL:,.0f}")
    print("\nSignal quality (weekly rank IC; decile spread = top minus bottom decile, annualized):")
    sig = ic_table[["mean_ic", "t_stat", "pct_positive", "weeks"]].copy()
    sig["top-bottom spread/yr"] = spread
    print(sig.to_string(formatters={"mean_ic": "{:.4f}".format, "t_stat": "{:.2f}".format, "pct_positive": "{:.0%}".format,
                                     "weeks": "{:.0f}".format, "top-bottom spread/yr": "{:.1%}".format}))
    print("\nPortfolios (net = IBKR tiered + 3 bps half-spread):")
    print(summary.to_string(formatters=fmt))
    print("\nModel cost sensitivity (CAGR net):", {k[1]: f"{v['cagr']:.1%}" for k, v in results.items() if k[0] == "Model (gradient boosting)"})
    print(f"Model vs SPY (excess of T-bill): alpha {ab['alpha_annual']:.1%}/yr (t={ab['alpha_t']:.2f}), beta {ab['beta']:.2f}")
    print("Deflated Sharpe Ratio of model excess returns:", {n: round(v, 3) for n, v in dsr.items()})
    years = pd.DataFrame({n: calendar_year_returns(equity[(n, "3 bps")]) for n in summary.index})
    print("\nCalendar-year net returns:")
    print(years.to_string(float_format=lambda v: f"{v:.1%}"))
    print("\nPRE-REGISTERED GATE:")
    for k, v in gate.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    print("  => " + ("PASSES the gate" if all(gate.values()) else "FAILS the gate"))
    print(f"\nDecile mean forward weekly return (model):\n{dec['Model (gradient boosting)'].map('{:.3%}'.format).to_string()}")

    import os
    os.makedirs(OUT, exist_ok=True)
    scores.to_frame("score").to_parquet(f"{OUT}/model_scores.parquet")
    json.dump({"gate": gate, "dsr": dsr, "alpha_beta": ab, "ic": ic_rows,
               "summary": summary.reset_index().to_dict("records")}, open(f"{OUT}/model_report.json", "w"), indent=2, default=float)
    print(f"\nDone in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
