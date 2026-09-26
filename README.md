# AI Stock Trading Spike

> 🚧 **WIP — active spike, not a finished project.** Hypothesis, stack, and
> structure are all still subject to change as research continues.

**Status:** Spike / proof-of-concept. No real money at any stage of this repo. Paper trading only.

## Hypothesis

A model combining engineered price/volume features (via gradient boosting) with
lagged news-sentiment features can produce a **walk-forward-validated, cost-adjusted
positive expectancy** when applied across a diversified basket of stocks (many small
positions, not concentrated bets) on a daily/weekly rebalancing horizon — meaningfully
outperforming a buy-and-hold baseline **after realistic transaction costs**, and
after correcting for overfitting (Deflated Sharpe Ratio / Probability of Backtest
Overfitting).

This is a falsifiable claim, not a foregone conclusion. The honest baseline
expectation, per the research this spike is built on, is that it fails — most
single-signal retail strategies don't survive rigorous out-of-sample testing. The
point of the spike is to find out, cheaply, before risking anything.

## Explicit non-goals

- **Not** a high-frequency or intraday-speed strategy. Retail cannot compete with
  institutional latency (sub-second reaction), and trading faster without an edge
  just compounds transaction costs — it doesn't reduce risk. Risk reduction here
  comes from diversification (many small positions) and disciplined, unemotional
  execution, not speed.
- **Not** a long-term (multi-year) investing strategy — horizon is daily/weekly,
  where backtesting is tractable.
- **Not** live-money trading. This repo stops at paper trading. Moving beyond that
  is a separate, later decision with its own review (including Canadian/IIROC
  regulatory rules, which have not been researched yet — the regulatory research
  behind this spike was US-focused).

## Why this shape of project

Full landscape research (brokers, regulatory constraints, evidence quality behind
technical/ML/sentiment signals, data sources) is in
[`docs/research-landscape.md`](docs/research-landscape.md). Short version:

- Classical technical indicators (RSI, MACD, MA crossovers) have weak-to-negative
  documented out-of-sample edge in modern markets — treated here as features, not
  standalone signals.
- Gradient-boosted models on engineered features have real peer-reviewed support,
  but most solo-developer backtests show classic overfitting fingerprints — hence
  the walk-forward + Deflated Sharpe Ratio requirement baked into this spike from
  day one, not bolted on after a good-looking backtest.
- News/earnings-drift sentiment (post-earnings-announcement drift) is one of the
  most-replicated anomalies in finance, strongest in small/mid-cap names — which
  is also where pump-and-dump risk concentrates, so sentiment features need
  sanity checks, not blind trust.

## Stack

| Concern | Choice | Why |
|---|---|---|
| Backtesting engine | [vectorbt](https://github.com/polakowo/vectorbt) | Actively maintained, vectorized multi-asset support, built-in Deflated Sharpe Ratio |
| Signal modeling | gradient boosting (LightGBM/XGBoost), patterned on [`stefan-jansen/machine-learning-for-trading`](https://github.com/stefan-jansen/machine-learning-for-trading) | Peer-reviewed support for this class of model; that repo is the closest existing reference implementation for this exact shape of project |
| Paper execution | [ib_async](https://github.com/ib-api-reloaded/ib_async) via IBKR paper trading account | IBKR has real Canadian retail access; `ib_async` is the actively maintained successor to the now-dead `ib_insync` |
| Historical price data | IBKR historical data API (paper account) and/or `yfinance` for quick iteration | Free tiers sufficient for a daily/weekly-horizon backtest |
| News/sentiment data | TBD — evaluated during signal-development phase | See gaps noted in the research doc |

## Project layout

```
src/          strategy code: feature engineering, model training, backtest wiring
data/         local cache of downloaded historical data (gitignored)
notebooks/    exploratory analysis
backtests/    backtest run configs and outputs (gitignored, except summaries)
docs/         research notes, hypothesis write-ups, decision log
```

## Definition of done (for this spike)

1. A backtest across a diversified stock universe (survivorship-bias-free), with
   realistic transaction costs, produces a Deflated Sharpe Ratio that survives
   correction for multiple testing.
2. If (1) holds, the same strategy runs unattended against an IBKR **paper**
   account for a defined trial period and its live paper-trading performance is
   compared against the backtest's expectations.
3. Either way, write up the result — a negative result (strategy doesn't survive
   walk-forward/cost-adjustment) is a valid, useful outcome of a spike.

## Next steps

- [ ] Pick initial stock universe (survivorship-bias-free list) and data source
- [ ] Build baseline: buy-and-hold benchmark + naive technical-indicator baseline
- [ ] Feature engineering pipeline (price/volume)
- [ ] Add walk-forward validation + Deflated Sharpe Ratio / PBO from the start
- [ ] Layer in news-sentiment features once price/volume baseline is honest
- [ ] Wire up IBKR paper trading via `ib_async` once backtest clears the bar above
