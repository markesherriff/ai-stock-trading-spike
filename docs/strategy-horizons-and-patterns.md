# Strategy horizons, chart patterns, and per-stock tuning

Research notes on three linked questions: which trading horizon the cost structure
allows, what the evidence says about candlestick and chart patterns, and whether
choosing patterns per stock (or per market regime) is a good idea. These are
research notes, not investment advice. Sources marked "read at source" were opened
and read in full-abstract form during this research; anything else is flagged.

**Short version.** Horizon is mostly a cost decision, and costs rule out day
trading for a small account before any signal question comes up. Pattern signals
are not day-trading-specific, but where they work at all, the evidence says they
work in *less efficient segments* (smaller, younger, higher-volatility), not in
large liquid names. Choosing patterns per stock is a plausible instinct but, done
naively, is a multiple-testing trap; the version that survives is a pooled model
that conditions on stock characteristics and regime, with the selection process
itself validated.

## 1. Horizon is mostly a cost decision

Costs here are roughly fixed per order, not proportional to size. The first real
round trip (see [`research-landscape.md`](research-landscape.md#what-the-first-real-round-trip-cost-and-how-it-was-measured))
cost about $0.26 on Alpaca and about $0.94 on Interactive Brokers Canada's Tiered
plan, where two US$0.35 minimum commissions dominate. For small share counts that
is about $0.71 in IBKR fees per round trip whatever the position size, so the cost
as a share of capital depends almost entirely on position size and trade
frequency. Illustrative annual fee drag, assuming the whole position turns over
every period (an upper bound) and ignoring spread/slippage:

| Position size | Daily (252 round trips) | Weekly (52) | Monthly (12) |
|---|---|---|---|
| $500 | ~36% | ~7.4% | ~1.7% |
| $2,000 | ~9.0% | ~1.9% | ~0.4% |
| $10,000 | ~1.8% | ~0.4% | ~0.1% |

A day-trading strategy on a small position has to out-earn that drag before it
earns anything, while a weekly or monthly one barely notices it. That drag is the
cost-side reason for the evidence side: the academic review in this repo cites
80–97% of real day traders losing money net of costs, 97% of persistent Brazilian
futures day traders losing, and under 1% of Taiwanese day traders predictably
profiting ([`academic-literature-review.md`](academic-literature-review.md)).

## 2. What the evidence says about candlestick and chart patterns

A candle is just open/high/low/close for a window, so patterns are not inherently
day-trading tools; a weekly candle is as valid as a one-minute one. Day traders use
them most because intraday charts produce many signals. On higher timeframes the
same patterns appear less often, which cuts cost drag but also cuts the number of
observations available to validate them.

| Study | Market / sample | Finding | Read at source? |
|---|---|---|---|
| Marshall, Young & Rose (2006), *J. Banking & Finance* ([DOI](https://doi.org/10.1016/j.jbankfin.2005.08.001)) | US DJIA stocks, 1992–2002 | Candlestick rules not profitable, per secondary summaries | **No** — article blocked; abstract unavailable |
| Lu, Shiu & Liu (2012), *Review of Financial Economics* ([DOI](https://doi.org/10.1016/j.rfe.2012.02.001)) | Taiwan Top 50 Tracker Fund constituents, 2002–2008 | Three bullish reversal patterns profitable; robust to out-of-sample test and bootstrap | Yes |
| Lu & Shiu (2011), *Int. J. Economics & Finance* ([DOI](https://doi.org/10.5539/ijef.v3n1p234)) | All Taiwan electronic securities, 1998–2007 | Harami signals significantly positive; confirmation factors (next-day open, body-size change, volume) improve results | Yes |
| Lo, Mamaysky & Wang (2000), *J. Finance* | US stocks, 1962–1996 | Chart patterns add incremental information, not shown profitable net of costs | Via the existing literature review |
| Hsu & Kuan (2005), SSRN ([DOI](https://doi.org/10.2139/ssrn.685361)) | NASDAQ Composite, Russell 2000, DJIA, S&P 500 | After White's Reality Check, profitable rules exist for NASDAQ Composite and Russell 2000 but **not** DJIA or S&P 500; best rules beat buy-and-hold in most in- and out-of-sample periods even after costs | Yes |
| Han, Yang & Zhou (2013), *JFQA* ([DOI](https://doi.org/10.1017/s0022109013000586)) | Volatility-sorted US portfolios | Moving-average timing beats buy-and-hold; for high-volatility portfolios the abnormal returns exceed momentum's and aren't explained by market timing, sentiment, default or liquidity risk; similar for other proxies of information uncertainty | Yes |
| Neely, Rapach, Tu & Zhou (2014), *Management Science* ([DOI](https://doi.org/10.1287/mnsc.2013.1838)) | Aggregate US equity risk premium | Technical indicators match or beat macro variables out of sample; they better detect declines near business-cycle peaks while macro variables better detect rises near troughs; combining both helps | Yes |
| Sullivan, Timmermann & White (1999), *J. Finance* ([DOI](https://doi.org/10.1111/0022-1082.00163)) | 100 years of DJIA daily data | Method paper: evaluates technical rules while adjusting for data snooping across the whole universe of rules tried | Yes (design only; abstract states no result) |

What the table says in plain terms. First, the results are **segment-dependent**,
not uniformly negative: nothing in the large, liquid DJIA/S&P 500 universe, but
significant results in NASDAQ Composite, Russell 2000, Taiwan, and high-volatility
portfolios. Second, the segments where signals appear are the segments with the
highest information uncertainty, which are also where spreads, thin liquidity and
manipulation risk concentrate (see the pump-and-dump discussion in
[`research-landscape.md`](research-landscape.md)); a signal that exists on paper can
still fail net of those costs. Third, **confirmation helps**: the Taiwan work found
that conditioning a pattern on volume and the next day's open improved it, which
argues for treating patterns as inputs combined with other variables rather than as
standalone triggers. Fourth, effects decay after publication (McLean & Pontiff, in
the literature review), and these samples mostly end well before the current period, so none of this
is direct evidence about today's market.

**Trendlines and support/resistance.** Trendline trading is a discretionary form of the same idea, and the evidence is mixed rather than empty. Osler (2000) tested support and resistance levels that six foreign-exchange firms gave their customers and found strong evidence that the levels predict intraday trend interruptions, with predictive power that varied across currencies and firms ("Support for Resistance: Technical Analysis and Intraday Exchange Rates") **[read]**. Brock, Lakonishok & LeBaron (1992) found strong support for moving-average and trading-range-break rules on the Dow from 1897 to 1986 ([DOI](https://doi.org/10.1111/j.1540-6261.1992.tb04681.x)) **[read]**. Work that corrects for data snooping then narrows it: Hsu & Kuan found significant rules for the NASDAQ Composite and Russell 2000 but not for the DJIA or S&P 500 **[read]**, and secondary summaries say Sullivan, Timmermann & White's data-snooping test of the Brock et al. rules likewise left no significant rule for the Dow **[secondary]**. The practical problem with trendlines specifically is that they are drawn by judgment: where a line starts and which touches count are discretionary, so a claimed track record cannot be replicated or independently tested. The testable version is a rule, for example a breakout of an N-day high/low channel (a trading-range break) or a break of a fitted regression channel, coded so identical inputs always produce identical trades, then put through the walk-forward and cost tests described here. That is a reasonable baseline to build, and if a discretionary trendline trader's edge is real, a mechanical version of it should retain some of it.

## 3. Choosing patterns per stock or per regime

**Why the instinct is reasonable.** Heterogeneity is documented: by market segment
(Hsu & Kuan), by volatility level (Han et al.), and over the business cycle (Neely
et al.). "Different stocks behave differently in different conditions" is
consistent with the literature.

**Why the naive version fails.** Picking the best-looking pattern for each stock is
multiple testing. If every candidate is noise, the chance that at least one of *n*
independent candidates looks significant at the 5% level is 1 − 0.95ⁿ: about 23%
for 5 candidates, 64% for 20, and 99.4% for 100. Per-stock data makes it worse: a
weekly series over five years has roughly 260 bars, and a specific pattern may
occur only a handful of times. Sullivan, Timmermann & White and Hsu & Kuan exist
precisely because the best of many rules looks good by chance. The selection
procedure gets overfit even if no individual rule does.

**A design that keeps the idea and removes the trap.**

1. **Pool across stocks and condition on characteristics.** Let one model see all
   stocks, with volatility, size, liquidity, sector and recent regime as inputs, so
   "this pattern matters for high-volatility small caps but not for mega caps"
   emerges as an interaction instead of a hand-picked per-ticker choice. This is
   where tree and neural-network models earn their keep: Gu, Kelly & Xiu (2020)
   attribute their gains over linear methods to nonlinear predictor interactions,
   with momentum, liquidity and volatility the dominant signals
   ([DOI](https://doi.org/10.1093/rfs/hhaa009)).
2. **If per-stock effects are wanted, shrink them.** Estimate per-stock deviations
   but pull them toward the group average (ridge-style or mixed-effects), so a stock
   with little data stays near the pooled answer. This is standard statistical
   practice rather than something established by the sources above.
3. **Validate the selection process, not the selected pattern.** Use nested
   walk-forward testing: each fold chooses patterns using only its training window,
   trades the following window, and the whole pipeline is scored. Count every
   candidate ever tried as a trial when computing the Deflated Sharpe Ratio and
   Probability of Backtest Overfitting already required in this repo.
4. **Treat regime as an input, not a switch.** Feed volatility and market-state
   variables to the model rather than hard-switching rule sets; switching adds
   parameters and overfitting risk. Monitor rolling out-of-sample performance and
   retire signals that decay.
5. **Fix the candidate list and horizons before looking at results**, and keep a
   final untouched hold-out period.

**Candidate features to start with** (daily and weekly bars): candle body size and
upper/lower wick ratios, gap size, engulfing / harami / hammer / doji flags, and
each of those combined with relative volume and the next bar's open, given the
Taiwan confirmation result.

## 4. Where an LLM news bot fits

The research already places the usable news edge at the next-day-to-week horizon:
same-day reaction is priced within roughly 250 milliseconds, while post-news drift
persists, especially in smaller and thinly covered stocks
([`research-landscape.md`](research-landscape.md)). A weekly cadence also keeps cost
drag low (section 1).

The main backtesting risk is **look-ahead bias**: an LLM trained on years of data may
carry knowledge of what happened after an old headline. Glasserman & Lin (2023)
studied exactly this for GPT-based headline sentiment ([DOI](https://doi.org/10.3905/jfds.2023.1.143)).
Their finding is more nuanced than "the model knows the future": in-sample, a
*distraction effect* (general knowledge about a named company interfering with the
sentiment reading) mattered more than look-ahead bias, especially for large
companies, and out-of-sample look-ahead bias was not a concern. Anonymizing company
names before scoring was proposed as a remedy. Two practical consequences: backtests
on news inside the model's training window are suspect, and **forward paper trading**
with timestamped predictions avoids the problem entirely, which is why it is the
recommended test here.

## 5. Recommended order of work

1. **Cost-aware harness first.** Charge every simulated fill using the broker-specific
   models already in the web app (IBKR per-order minimums, measured spread), and set
   a position-size floor of roughly $2,000 so commissions don't swamp small edges.
2. **Weekly/monthly pooled model.** Gradient boosting on engineered features,
   including the candle and pattern features above, with nested walk-forward
   validation and deflated-Sharpe reporting.
3. **Test the per-segment hypothesis directly.** Check whether pattern features add
   anything in high-volatility small/mid-caps but not large caps, net of costs, using
   the pooled model's interaction terms rather than per-stock selection.
4. **LLM news-drift bot, forward paper-traded only**, weekly horizon, with
   timestamped predictions and company-name anonymization as a robustness check.
5. **Defer intraday strategies and leverage** until something has a validated,
   net-of-cost edge. Leverage scales whatever edge exists, including a negative one.

## 6. Source notes and open questions

- Read at source (abstract or full text): Osler; Brock, Lakonishok & LeBaron; Hsu & Kuan; Han, Yang & Zhou; Neely et
  al.; Gu, Kelly & Xiu; Lu, Shiu & Liu; Lu & Shiu; Sullivan, Timmermann & White
  (design only); Glasserman & Lin.
- **Not read at source:** Marshall, Young & Rose (2006). The publisher page blocked
  access and no open abstract was found, so its result is as reported by secondary
  summaries. No other US candlestick study was checked.
- The day-trading statistics (Barber & Odean; Chague et al.; the Taiwan study) come
  from the existing literature review and were not re-verified here.
- Open questions: how stable the Taiwan candlestick results are after 2008 and in US
  small caps; whether the small-cap and high-volatility signals survive realistic
  spreads and borrow constraints; and how quickly pattern features decay once added
  to a pooled model.
