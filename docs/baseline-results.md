# Baseline backtest results

First results from the cost-aware harness in [`src/`](../src). These are the **hurdles**
any model has to clear, not strategies being promoted. Reproduce with
`python -m src.run_baselines`.

## Setup

- **Data:** Alpaca daily bars (SIP feed, adjusted for splits and dividends), 2016-01-04 to
  2026-10-01. Backtest window 2017-01-03 onward (earlier bars are signal warm-up), about 9.75 years,
  including the 2018 Q4 drop, the 2020 crash and the 2022 bear market.
- **Universe:** 10 liquid ETFs: SPY, QQQ, IWM, EFA, EEM, VNQ, TLT, IEF, GLD, DBC.
- **Capital:** $100,000, matching the Alpaca paper account.
- **Execution:** signals at the close, orders at the next day's open, whole shares only.
- **Costs:** Interactive Brokers Canada Tiered plan for US stocks (commission with the US$0.35
  per-order minimum, clearing, pass-through, regulatory fees), plus an *assumed* 2 bps half-spread
  per side and an *assumed* US$0.003/share exchange fee. Orders under $500 of rebalancing drift
  are skipped.
- **Cash:** earns the return of BIL, a 1–3 month T-bill ETF. Sharpe ratios are measured against it.
- **Parameters fixed in advance** (SMA 200; Donchian 55-day entry / 20-day exit), so this is
  **four trials in total** for overfitting purposes.

## Results (net of costs)

| Strategy | Final $ | CAGR gross | CAGR net | Volatility | Sharpe | Max drawdown | Costs per year |
|---|---|---|---|---|---|---|---|
| SPY buy & hold | $392,135 | 15.1% | 15.1% | 17.8% | 0.75 | -33.8% | 0.00% |
| 10-ETF equal weight, monthly | $246,227 | 9.7% | 9.7% | 11.7% | 0.65 | -23.0% | 0.02% |
| SMA-200 trend, monthly | $213,371 | 8.2% | 8.1% | 7.3% | 0.78 | -8.3% | 0.07% |
| Donchian 55/20 breakout | $158,581 | 5.0% | 4.8% | 5.5% | 0.46 | -5.9% | 0.15% |

## What this says

- **SPY buy-and-hold is a high bar for this decade.** US large caps returned about 15% a year
  with a Sharpe of 0.75 here; every diversified baseline earned less in absolute terms. Any model
  has to beat that net of costs, or justify itself on risk.
- **Trend following traded return for risk.** The SMA-200 rule earned about half of SPY's return
  with a quarter of the drawdown (-8.3% vs -33.8%) and a slightly higher Sharpe (0.78 vs 0.75),
  which is the classic trend-following shape. The Donchian breakout was weaker on every measure.
- **Costs are negligible at ETF position sizes.** At roughly $10,000 per position, total costs were
  0.00–0.15% a year even for the most active baseline. The cost problem identified in the research
  docs is a many-small-stock-positions problem and will appear in the pooled-model step, not here.
- **Passive growth did most of the work.** $100,000 in SPY became about $392,000. At that size,
  the same 15% return is roughly $1,100 a week, which is why capital is the main lever, but this
  decade was unusually strong for US large caps and should not be projected forward.

## Caveats

- **Period-specific.** 2017–2026 was exceptional for US large caps. Different decades would rank
  these strategies differently, and ten years is one path, not a distribution.
- **Benchmark chosen with hindsight.** SPY is the obvious benchmark now, partly because it won.
- **Assumed costs.** The spread (2 bps per side) and exchange fee are assumptions, not measurements,
  and ETF spreads differ from stock spreads.
- **Simplifications.** Adjusted prices stand in for dividends, taxes are ignored, fee rates for
  past years use today's schedule, and cash yield uses BIL's price-based daily returns.
- **Data cross-check.** The SPY result matches a direct buy-and-hold calculation from the raw bars
  to within 19 cents when costs and cash yield are switched off, and SPY's calendar-year returns match
  the known figures (for example +31.1% in 2019, -18.2% in 2022).
