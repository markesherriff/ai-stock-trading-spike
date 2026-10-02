"""Cost-aware daily backtest engine.

Signals are known at the close of a decision date; orders execute at the NEXT trading day's open
(no look-ahead), in whole shares, with every order charged by the cost model.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .costs import CostModel


@dataclass
class BacktestResult:
    equity: pd.Series
    trades: pd.DataFrame
    initial_cash: float


TRADE_COLUMNS = [
    "date", "symbol", "side", "shares", "price", "notional",
    "commission", "exchange_and_clearing", "regulatory", "spread", "total_cost",
]


def run_backtest(
    open_: pd.DataFrame,
    close: pd.DataFrame,
    decisions: pd.DataFrame,
    cost_model: CostModel,
    initial_cash: float = 100_000.0,
    min_trade_value: float = 0.0,
    cash_yield: pd.Series | None = None,
) -> BacktestResult:
    """`decisions`: index = decision dates (present in close.index), columns = symbols, values = target weights.

    `cash_yield`: daily return earned on uninvested cash (e.g. a T-bill ETF's returns); 0% when omitted.
    """
    dates = close.index
    symbols = list(close.columns)
    execute_on: dict[pd.Timestamp, pd.Series] = {}
    for decision_date, weights in decisions.iterrows():
        position = dates.get_loc(decision_date)
        if position + 1 < len(dates):
            execute_on[dates[position + 1]] = weights.reindex(symbols).fillna(0.0)

    shares = pd.Series(0, index=symbols, dtype="int64")
    cash = float(initial_cash)
    equity: dict[pd.Timestamp, float] = {}
    trades: list[dict] = []

    for day in dates:
        if cash_yield is not None:
            cash *= 1.0 + float(cash_yield.get(day, 0.0))
        if day in execute_on:
            px = open_.loc[day]
            tradable = px.notna() & (px > 0)
            weights = execute_on[day].where(tradable, 0.0)
            equity_open = cash + float((shares * px.fillna(0.0)).sum())
            target = pd.Series(0, index=symbols, dtype="int64")
            for s in symbols:
                if weights[s] > 0:
                    target[s] = int(np.floor(weights[s] * equity_open / px[s]))
            delta = target - shares
            for s in symbols:
                small = abs(delta[s]) * (px[s] if tradable[s] else 0.0) < min_trade_value
                if delta[s] != 0 and small and target[s] != 0:
                    delta[s] = 0

            for s in symbols:
                if delta[s] < 0:
                    n = int(-delta[s])
                    cash += _execute(trades, cost_model, day, s, "SELL", n, float(px[s]))
                    shares[s] -= n

            buys = {s: int(delta[s]) for s in symbols if delta[s] > 0}
            needed = sum(n * float(px[s]) + cost_model.order_cost("BUY", n, float(px[s]), day.date()).total
                         for s, n in buys.items())
            scale = min(1.0, cash / needed * 0.9999) if needed > 0 else 1.0
            for s, n in buys.items():
                n = int(np.floor(n * scale))
                if n > 0:
                    cash += _execute(trades, cost_model, day, s, "BUY", n, float(px[s]))
                    shares[s] += n

        equity[day] = cash + float((shares * close.loc[day].fillna(0.0)).sum())

    frame = pd.DataFrame(trades, columns=TRADE_COLUMNS)
    return BacktestResult(pd.Series(equity, name="equity"), frame, initial_cash)


def _execute(trades: list[dict], model: CostModel, day: pd.Timestamp, symbol: str, side: str, n: int, price: float) -> float:
    """Record the trade and return the signed cash change (proceeds or outlay, net of costs)."""
    cost = model.order_cost(side, n, price, day.date())
    notional = n * price
    trades.append({
        "date": day, "symbol": symbol, "side": side, "shares": n, "price": price, "notional": notional,
        "commission": cost.commission, "exchange_and_clearing": cost.exchange_and_clearing,
        "regulatory": cost.regulatory, "spread": cost.spread, "total_cost": cost.total,
    })
    return notional - cost.total if side == "SELL" else -(notional + cost.total)


def summarize(result: BacktestResult, risk_free: pd.Series | None = None) -> dict:
    """Headline metrics. Sharpe is on returns in excess of `risk_free` (daily returns; 0% when omitted)."""
    equity = result.equity
    returns = equity.pct_change().dropna()
    rf = risk_free.reindex(returns.index).fillna(0.0) if risk_free is not None else 0.0
    excess = returns - rf
    years = (equity.index[-1] - equity.index[0]).days / 365.25
    vol = float(returns.std() * np.sqrt(252))
    trades = result.trades
    avg_equity = float(equity.mean())
    return {
        "final_equity": float(equity.iloc[-1]),
        "cagr": float((equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1),
        "volatility": vol,
        "sharpe": float(excess.mean() * 252 / (excess.std() * np.sqrt(252))) if vol > 0 else float("nan"),
        "max_drawdown": float((equity / equity.cummax() - 1).min()),
        "n_trades": int(len(trades)),
        "turnover_per_year": float(trades["notional"].sum() / avg_equity / years) if len(trades) else 0.0,
        "total_costs": float(trades["total_cost"].sum()),
        "commission": float(trades["commission"].sum()),
        "exchange_and_clearing": float(trades["exchange_and_clearing"].sum()),
        "regulatory": float(trades["regulatory"].sum()),
        "spread": float(trades["spread"].sum()),
        "costs_pct_per_year": float(trades["total_cost"].sum() / avg_equity / years),
        "years": float(years),
    }


def calendar_year_returns(equity: pd.Series) -> pd.Series:
    year_end = equity.resample("YE").last()
    start = pd.concat([pd.Series([equity.iloc[0]], index=[equity.index[0] - pd.Timedelta(days=1)]), year_end])
    return start.pct_change().dropna().rename(lambda ts: ts.year)
