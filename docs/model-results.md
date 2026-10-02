# Pooled weekly model: first results (fails the pre-registered gate)

Test design and pass/fail criteria were fixed beforehand in
[`model-validation-plan.md`](model-validation-plan.md). Reproduce with
`python -m src.run_model` (about 90 seconds once bars are downloaded).

## Verdict

**The gradient-boosting model fails all three gate criteria and is not promoted to forward paper
trading.** On a survivorship-free S&P 500 universe, 2020–2026, weekly price/volume features including
candlestick patterns produced no detectable ranking skill, and the resulting long-only portfolio earned
less than SPY on both return and risk-adjusted terms after costs.

## Results (test window 2020-01-03 to 2026-10-01, $100,000, net = IBKR tiered + 3 bps half-spread)

**Signal quality** (weekly rank IC between predicted score and next-week return):

| Rule | Mean IC | t-stat | Weeks IC > 0 | Top-minus-bottom decile, annualized |
|---|---|---|---|---|
| Gradient-boosting model | +0.0071 | 0.69 | 53% | 3.7% |
| 12-1 momentum rule | +0.0120 | 0.91 | 53% | 7.2% |
| Low-volatility rule | -0.0091 | -0.61 | 48% | -11.9% |

**Portfolios** (long-only, 30 stocks, equal weight):

| Portfolio | Final $ | CAGR net | CAGR gross | Volatility | Sharpe | Max drawdown | Turnover / yr | Costs / yr |
|---|---|---|---|---|---|---|---|---|
| Model | $166,957 | 7.9% | 12.0% | 29.0% | 0.32 | -59.5% | 7,597% | 3.57% |
| 12-1 momentum | $340,090 | 19.9% | 20.4% | 29.0% | 0.68 | -36.4% | 581% | 0.29% |
| Low volatility | $179,139 | 9.0% | 9.2% | 15.0% | 0.47 | -29.3% | 537% | 0.24% |
| SPY buy & hold | $261,644 | 15.3% | 15.4% | 19.7% | 0.69 | -33.7% | 9% | 0.00% |

Model CAGR by assumed half-spread: 9.5% at 1 bp, 7.9% at 3 bps, 6.1% at 5 bps, 12.0% before costs.
Versus SPY the model's alpha was -6.8% a year (t = -1.0) with a beta of 1.18. Its Deflated Sharpe Ratio
was 0.79 for one trial, 0.48 for three, 0.35 for five and 0.14 for twenty.

**Gate:** (1) mean IC > 0 with t >= 2: **fail** (t = 0.69). (2) Sharpe above SPY's: **fail** (0.32 vs 0.69).
(3) Deflated Sharpe >= 0.95 at five trials: **fail** (0.35).

## Why it failed

- **No signal to find.** The model's IC was indistinguishable from zero, the decile returns were flat and
  non-monotonic, and its yearly IC flipped sign (-0.023 in 2020, +0.026 in 2021, +0.030 in 2022, -0.007 in
  2023, +0.008 in 2024, -0.009 in 2025, +0.030 in 2026).
- **Noise became turnover.** Weak, unstable scores reshuffled the top 30 almost completely each week:
  7,600% annual turnover and 15,684 trades, costing 3.6% a year and turning a 12.0% gross return into 7.9%
  net. The hold band (keep a stock while it ranks in the top 60) cannot help when ranks are mostly noise.
- **It was worse than one feature.** The single feature one-week return had an IC of -0.027 (t = -2.5), four
  times the model's, so the model spent its capacity fitting noise instead of capturing the one effect that
  existed.
- **Concentrated long-only risk.** Beta of 1.18 and a -59.5% drawdown (2020: -15.1% while SPY gained 18.8%).

## Diagnostics (exploratory, not used to tune anything)

Single-feature IC over the same window (32 features, so several will look significant by chance):

- The pipeline behaves sensibly: **short-term reversal** shows the textbook sign (`ret_1w` -0.027, t = -2.5;
  `body_ratio`, the last candle's direction, -0.021; `dist_sma20` -0.021), and 12-1 momentum is weak (+0.012,
  t = 0.9), as the research predicts for large caps.
- **Candlestick pattern flags added essentially nothing.** Of seven flags, six had |t| below 1. The exception,
  bearish engulfing (+0.010, t = 2.6, with the "wrong" sign for a bearish signal), is what you expect from
  picking the best of 32 tests. This fits the finding that patterns carry signal in less efficient segments,
  not in large-cap S&P 500 stocks.
- **The reversal effect was found by looking at the test window**, so it cannot be validated there. Re-checked
  on 2017–2019, which was never examined: same sign but weaker (IC +0.016, t = 1.2), and a long-only top-30
  reversal portfolio earned 10.7% net versus SPY's 14.6% (Sharpe 0.46 vs 1.02), with a -48.2% drawdown and
  1.0% a year in costs. In 2020–2026 it earned 17.8% net versus 15.3% but with a Sharpe of 0.59 vs 0.69, a
  -64.2% drawdown and 3.8% a year in costs. It is not an edge net of costs and risk.
- **Momentum** earned 19.9% a year but with 29% volatility, a Sharpe equal to SPY's (0.68 vs 0.69) and an IC
  that is not significant; 2026 alone returned +60.3%. That is not a validated edge.

## What this does and does not show

- It shows that **this design** (price/volume features, weekly horizon, S&P 500 universe, long-only top 30)
  has no demonstrated edge over buying SPY in 2020–2026. It matches the research: large caps are the
  efficient end of the market.
- It does **not** show that no edge exists anywhere. Small and mid caps, longer horizons, or non-price
  information (earnings, news) are untested, and the research points to those segments, where costs and risks
  are also higher.
- One test window is one path. A pass would not have proved an edge either; this fail is informative
  because the test was strict and the rules were fixed in advance.

## What happens next

The model is **not** promoted. Any further model variant is a new trial and needs its own pre-registered
design before it is run. Candidates, in the order the evidence supports them:

1. **LLM news-drift, forward-only.** Non-price information is the one input the large-cap price data lacks,
   and next-day-to-week drift is where the research puts the news edge. Forward paper trading avoids the
   look-ahead problem entirely.
2. **A smaller-cap universe.** Where the technical-signal evidence lives, but with wider spreads, thinner
   liquidity and manipulation risk; the cost model would need measured spreads first.
3. **A monthly horizon with score smoothing** to cut turnover, if a signal is found worth smoothing.

Meanwhile the live system runs the validated-as-baselines strategies (SPY hold, 200-day trend on ETFs) so
forward evidence accumulates for the hurdles any model must beat.
