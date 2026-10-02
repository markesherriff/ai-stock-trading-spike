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
  is a separate, later decision with its own review. One piece of Canadian
  regulation is now resolved, not just flagged: CIRO (formerly IIROC) bars
  order-execution-only/DIY retail accounts from API-driven automated orders on
  **Canadian marketplaces** specifically — see
  [`docs/research-landscape.md`](docs/research-landscape.md#canadian-retail-clients-cannot-api-trade-canadian-listed-securities--this-is-a-real-current-rule-not-forum-folklore).
  So any future automated (non-paper) phase is necessarily scoped to US-listed
  equities, regardless of broker — it doesn't change anything this repo does
  today. Other Canadian regulatory/tax considerations beyond that one rule
  remain unresearched.

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
| Backtesting engine | Custom cost-aware engine in [`src/backtest.py`](src/backtest.py) ([vectorbt](https://github.com/polakowo/vectorbt) kept as an option for later parameter sweeps) | Next-open execution, whole shares and IBKR's per-order commission minimums are explicit and unit-tested against the live cost figures; the Deflated Sharpe Ratio still needs adding for the model step |
| Signal modeling | gradient boosting (LightGBM/XGBoost), patterned on [`stefan-jansen/machine-learning-for-trading`](https://github.com/stefan-jansen/machine-learning-for-trading) | Peer-reviewed support for this class of model; that repo is the closest existing reference implementation for this exact shape of project |
| Paper execution (strategy validation target) | [ib_async](https://github.com/ib-api-reloaded/ib_async) via IBKR paper trading account | IBKR has real Canadian retail access for opening an account and API-trading US-listed securities; `ib_async` is the actively maintained successor to the now-dead `ib_insync`. CIRO rules bar API orders on *Canadian* marketplaces for any DIY account regardless of broker — not an IBKR limitation, see research doc |
| Paper execution (website, for now) | [Alpaca](https://alpaca.markets) paper trading API | Pure cloud REST/WebSocket, free unlimited paper trading, no local gateway app to run — much faster to develop the website against. US equities only; doesn't replace IBKR for the Canadian-access goal above |
| Historical price data | IBKR historical data API (paper account) and/or `yfinance` for quick iteration | Free tiers sufficient for a daily/weekly-horizon backtest |
| News/sentiment data | TBD — evaluated during signal-development phase | See gaps noted in the research doc |

## Project layout

```
src/          research code: data download/cache, IBKR cost model, backtest engine, baseline strategies
tests/        pytest suite (cost model vs. the live backend's figures, backtest invariants)
data/         local cache of downloaded historical data (gitignored)
notebooks/    exploratory analysis
backtests/    backtest run configs and outputs (gitignored, except summaries)
docs/         research notes, hypothesis write-ups, decision log
backend/      Node/TypeScript (Express) service wrapping the Alpaca API — paper account, basic order placement
frontend/     React + TypeScript (Vite) website — account/positions view, manual + AI-suggested trades
```

## Running the research baselines

```bash
/opt/homebrew/bin/python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q                 # unit tests
python -m src.run_baselines         # downloads bars on first run (needs backend/.env keys), then backtests
```

## Running the website (paper trading)

This is a basic web UI for watching an Alpaca **paper** account and placing
paper trades — by hand or via a placeholder "AI" signal (a moving-average
crossover stub in [`backend/src/routes/signal.ts`](backend/src/routes/signal.ts),
to be replaced once the real model from `src/` is trained and validated). A
React Native app may follow later; the website is faster to iterate on for now.

The website uses **Alpaca**, not IBKR, purely because it's much faster to
develop against (cloud API, no local gateway app). This doesn't change the
IBKR choice in the Stack table above for actually validating the strategy —
see that table's note on why.

1. Sign up for a free account at [alpaca.markets](https://alpaca.markets) and
   grab your **paper trading** API key/secret from the dashboard (make sure
   you're viewing the paper account, not live).
2. Backend:
   ```bash
   cd backend
   npm install
   cp .env.example .env   # fill in APCA_API_KEY_ID / APCA_API_SECRET_KEY
   npm run dev
   ```
3. Frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
4. Open http://localhost:5173. The backend runs on http://localhost:8000 and
   reports Alpaca connection status at `/api/health`.

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

- [x] Data source: Alpaca daily bars (SIP, split/dividend-adjusted, free back to 2016) cached in `data/`
- [ ] Pick the stock universe for the pooled model (survivorship-bias-free list; the baselines use a 10-ETF universe)
- [x] Baselines: SPY buy-and-hold, equal-weight ETFs, SMA-200 trend, Donchian breakout — results in [`docs/baseline-results.md`](docs/baseline-results.md)
- [ ] Feature engineering pipeline (price/volume), including candlestick/pattern features on daily and weekly bars
- [x] Cost-aware backtest harness using the broker-specific fee models (IBKR per-order minimums, assumed spread)
- [ ] Nested walk-forward validation of any per-stock/per-regime pattern selection, counting every candidate as a trial
- [ ] LLM news-drift bot, forward paper-traded only (weekly horizon, timestamped predictions)
- [ ] Add walk-forward validation + Deflated Sharpe Ratio / PBO from the start
- [ ] Layer in news-sentiment features once price/volume baseline is honest
- [ ] Wire up IBKR paper trading via `ib_async` once backtest clears the bar above

## Other docs

- [`docs/research-landscape.md`](docs/research-landscape.md) — broker/data/regulatory landscape research behind the stack decisions above.
- [`docs/academic-literature-review.md`](docs/academic-literature-review.md) — academic evidence review behind the hypothesis.
- [`docs/tooling-ideas.md`](docs/tooling-ideas.md) — unvetted external tools/examples worth considering later (TradingView, agent-trading MCP servers, dashboard ideas).
- [`docs/strategy-horizons-and-patterns.md`](docs/strategy-horizons-and-patterns.md) — which horizon the cost structure allows, what the evidence says about candlestick/chart patterns, and how to do per-stock/per-regime pattern selection without overfitting.
- [`docs/baseline-results.md`](docs/baseline-results.md) — first backtest results for the baseline strategies, with caveats.
- [`docs/trade-and-trader-types.md`](docs/trade-and-trader-types.md) — map of all trade types, trader types, strategy families and asset classes (including crypto and its Canadian constraints), with a ranked possibility list for this project.
- [`docs/prediction-approach.md`](docs/prediction-approach.md) — open options for what the model should predict (direction/signal vs. exact candle values) and a fast hold-out-the-last-N-days validation loop.
