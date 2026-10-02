# Model validation plan (written before any model results existed)

This file fixes the design and the pass/fail criteria for the pooled weekly stock model
**before it was run**, so the result can't be tuned until it looks good. If a choice below
is changed after seeing results, that change must be recorded here with the date and
counted as another trial.

## What is being tested

Can a pooled gradient-boosting model, using only price/volume features (including candlestick
pattern features), rank S&P 500 stocks well enough to beat buying SPY **after realistic costs**,
over a period it never saw during training?

## Design (fixed in advance)

- **Universe:** point-in-time S&P 500 membership (third-party dataset, spot-checked), 2016–2026,
  including stocks later removed or acquired; ~99% of members have price data. A stock is eligible
  on a date if it is a member, has a bar that day, a price of at least $5, and at least 252 days of history.
- **Decision and execution:** decide at the close of the last trading day of each week; execute at the
  next trading day's open, whole shares, every order charged by the IBKR Canada tiered cost model plus
  an assumed spread of 3 bps per side (1 and 5 bps shown as sensitivity). Cash earns T-bill (BIL) returns.
- **Target:** cross-sectional percentile rank of the open-to-open return over the following week.
- **Features (about 40):** momentum and reversal at several horizons, volatility, beta, trend
  distances, 52-week-high proximity, RSI, volume/liquidity, daily and weekly candle-shape features,
  candlestick pattern flags (doji, hammer, shooting star, engulfing, harami), and market-regime variables
  (SPY volatility and trend, cross-sectional dispersion). Stock features are rank-normalized per date.
- **Model:** scikit-learn `HistGradientBoostingRegressor` with fixed hyperparameters (300 iterations,
  learning rate 0.05, 15 leaves, 500 samples per leaf, L2 = 1.0). **No tuning.** (LightGBM was the original
  plan but needs a system library that is not installed; this is the same model class.)
- **Walk-forward:** expanding window. First training window 2017-01 through 2019-12; the model is refit
  every 13 weeks and predicts the following 13 weeks. Training samples stop two weeks before each refit so
  no label overlaps the prediction period. Test window: 2020 through September 2026 (includes the 2020
  crash and the 2022 bear market).
- **Portfolio:** long-only, equal-weight 30 stocks. Buy the top 30 by predicted score; keep an existing
  holding while it stays in the top 60 (reduces turnover). About $3,300 per position on $100,000.
- **Comparisons:** SPY buy-and-hold; a plain 12-1 month momentum rule and a low-volatility rule run through
  the identical portfolio and cost machinery. If the model cannot beat simple momentum, the machine
  learning added nothing.
- **Trials counted:** the model, momentum and low-volatility rules are three trials; the Deflated Sharpe
  Ratio is reported for 3, 5 and 20 trials because the true count includes design decisions made here.

## Pass/fail gate for forward paper trading (all must hold)

1. Mean weekly rank information coefficient is positive with a t-statistic of at least 2.
2. Net-of-cost Sharpe ratio (3 bps spread) exceeds SPY's over the same window.
3. Deflated Sharpe Ratio of the strategy's returns, for 5 trials, is at least 0.95.

Failing any one means the model is **not** promoted to forward paper trading as a candidate strategy.
Passing does not mean it works: it only earns the right to a six-month forward test with timestamped
predictions before any other conclusion is drawn.

## Known biases that remain

- Membership data is third-party; ~1% of members have no price data (mostly renamed tickers).
- Prices are adjusted for splits and dividends; delisted holdings are exited at their last traded price.
- Spreads are assumed, not measured. The market-regime variables see only the past.
- One test window; no claim about other periods.

## Addendum, 2026-10-02: results

The model was run exactly as specified above and **failed all three gate criteria** (IC t-stat 0.69, Sharpe
0.32 vs SPY 0.69, Deflated Sharpe 0.35 at five trials); see [`model-results.md`](model-results.md).

Post-hoc notes, recorded honestly:

- The short-term-reversal hypothesis was found by examining single-feature ICs **in the test window**, so the
  test window cannot validate it. It was re-checked on 2017–2019 (never examined) and did not hold up net of
  costs. It counts as an additional trial. Any future promotion of a reversal strategy requires forward-only evidence.
- One implementation detail differs from the text: the feature set has 36 columns, not "about 40".
