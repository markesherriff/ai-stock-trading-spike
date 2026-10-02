# Types of trades and traders, including crypto

A map of the whole possibility space, so choices for this project are made against
the full picture instead of whichever strategy came up first. These are research
notes, not investment advice. Labels used throughout: **[read]** means the abstract
or document was opened and read at its source during this research; **[secondary]**
means a search summary or aggregator only; **[not researched]** means I know the
category exists but did not verify claims about it.

## 1. How to slice it: where does the profit come from?

Every trade, in every market, is one of a handful of bets, and the useful question
is "who is on the other side, and why are they paying me?"

| Source of edge | The idea | Who can realistically have it |
|---|---|---|
| Speed | Act on information or mispricing faster than others | Firms with colocation and custom hardware |
| Liquidity provision | Get paid the spread for standing ready to trade | Market makers; needs speed, capital, inventory risk management |
| Risk premium | Get paid for holding risk others avoid (equity, trend, volatility, carry) | Anyone, but the premium is small and arrives with drawdowns |
| Information / analysis | Process public data better than the crowd (news, fundamentals, models) | Possible but the edge is thin and decays when published |
| Behavioral | Exploit others' mistakes (overreaction, attention, overconfidence) | Possible; the same behavior can hurt the exploiter |
| Access / structure | Trades others can't do (capital controls, market segmentation) | Whoever can reach both sides |

Most retail "strategies" are an attempt at information or behavioral edge, while the
trader types that clearly profit usually hold a speed, liquidity or structural edge.

## 2. Trader types (who)

| Type | What they do | Edge source | Evidence on outcomes | Open to a solo Canadian? |
|---|---|---|---|---|
| High-frequency / market makers | Provide liquidity and arbitrage at microsecond to second scale | Speed, liquidity | Relative latency explains large differences in HFT firms' performance, and speed helps market making and cross-market arbitrage ([Baron et al. 2019](https://doi.org/10.1017/s0022109018001096)) **[read]**. The arbitrage opportunities are built into continuous-market design and competition only raised the speed needed to capture them ([Budish, Cramton & Shim 2015](https://doi.org/10.1093/qje/qjv027)) **[read]** | No: a speed arms race |
| Quant hedge funds / prop firms | Systematic models at scale | Many small edges, infrastructure, data | Medallion reported at about 66% gross and 39% net a year 1988–2018, closed to outsiders since 1993 ([overview](https://pwlcapital.com/renaissance-technologies-medallion-fund-an-exception-to-the-indexing-rule/)) **[secondary]** | No |
| CTAs / trend followers | Systematic trend following across futures and other markets | Risk premium (time-series momentum) | Positive average returns in each decade since 1880 and good performance in 8 of the 10 largest crisis periods ([Hurst, Ooi & Pedersen 2017](https://doi.org/10.3905/jpm.2017.44.1.015)) **[read]** | Yes, in simplified form (ETFs or futures) |
| Active mutual funds / institutions | Stock picking | Analysis | 67% of active large-cap funds underperformed the S&P 500 in H1 2026 and 79% in 2025 ([SPIVA](https://www.spglobal.com/spdji/en/spiva/article/spiva-us/)) **[read]** | n/a |
| Retail day traders | Intraday discretionary trading | Claimed information/pattern | 97% of persistent Brazilian futures day traders lost money; under 1% of Taiwanese day traders predictably profited ([literature review](academic-literature-review.md)) **[secondary to this research]** | Yes, and it's where most losses are |
| Retail swing / position traders | Hold days to months | Analysis, behavioral | The average household earned 16.4% a year versus 17.9% for the market, and the most active earned 11.4% ([Barber & Odean 2000](https://doi.org/10.1111/0022-1082.00226)) **[read]** | Yes |
| Retail algorithmic / quant hobbyists | Automated rules built by individuals | Information, behavioral | Backtest Sharpe ratios had little power to predict live results across 888 algorithms (Wiecki et al., per the [literature review](academic-literature-review.md)) **[secondary to this research]** | Yes; this project |
| Passive / index investors | Buy and hold diversified funds | Risk premium | The benchmark everything else is measured against | Yes |
| Copy / social traders, prop-firm "funded account" programs | Follow others, or trade a firm's capital under rules | Varies | **[not researched]** | Varies |
| Crypto market makers, cross-exchange arbitrageurs, MEV searchers | Provide liquidity or capture mispricing across venues and on-chain | Speed, capital, structure | **[not researched]** beyond the crypto section below | Mostly no |

## 3. Trades by holding period (how long)

| Style | Holding period | What it needs | Cost sensitivity |
|---|---|---|---|
| High-frequency | microseconds to seconds | Colocation, specialized hardware | Extreme; lives on rebates and spreads |
| Scalping | seconds to minutes | Fast execution, tight spreads | Very high |
| Day trading | minutes to hours, flat overnight | Attention, capital, low costs | High: at this repo's measured IBKR costs, fee drag is about 9% a year on a $2,000 position traded daily, about 36% on $500 ([strategy doc](strategy-horizons-and-patterns.md)) |
| Swing trading | days to weeks | Analysis | Moderate |
| Position / trend | weeks to months | Patience, diversification | Low |
| Buy-and-hold / DCA | years | Nothing but discipline | Negligible |

## 4. Strategy families (what the edge is)

| Family | Idea | Evidence | Notes |
|---|---|---|---|
| Trend following / time-series momentum | Ride sustained moves, cut losers | Significant time-series momentum in 58 liquid futures across equity indexes, currencies, commodities and bonds, with persistence over 1 to 12 months ([Moskowitz, Ooi & Pedersen](https://doi.org/10.1016/j.jfineco.2011.11.003)) **[read]**; century-long evidence above | Strongest long-run evidence of any style here; low turnover; modest returns and long drawdowns are normal |
| Cross-sectional factors / anomalies | Long winners, short losers on characteristics | Net of costs, decay and data mining the average anomaly earns about 4 bps a month ([Chen & Velikov](https://doi.org/10.1017/s0022109022000874)) **[read]**; few strategies above 50% monthly turnover survive costs ([Novy-Marx & Velikov](https://doi.org/10.1093/rfs/hhv063)) **[read]** | Favors low turnover |
| Technical patterns / candlesticks | Pattern signals on price charts | Segment-dependent; see [strategy doc](strategy-horizons-and-patterns.md) | Best treated as model features |
| Event-driven / earnings drift / news and sentiment (including LLM) | Trade the slow digestion of information | See [`research-landscape.md`](research-landscape.md) | Next-day-to-week horizon; forward paper testing recommended |
| Volatility / premium selling (options) | Sell insurance, collect premium | The variance risk premium is a measurable quantity in index and stock options ([Carr & Wu](https://doi.org/10.1093/rfs/hhn038)) **[read]**; that sellers earn a premium for bearing crash risk is the usual interpretation, from my general knowledge rather than the abstract | Small steady gains with rare large losses |
| Carry (FX carry, crypto basis and perpetual-futures funding) | Collect the yield difference between two positions | Perpetual futures are analyzed in He, Manela, Ross & von Wachter (SSRN 4301150) **[not read: no abstract]** | Funding-rate carry returns **[not researched]** |
| Statistical arbitrage / pairs | Bet on relationships reverting | No source here quantified a retail-achievable net return ([`research-landscape.md`](research-landscape.md)) | Educational |
| Market making / latency arbitrage | See trader types | Speed-dependent | Not feasible solo |
| Fundamental / value investing, DCA | Buy cheap or buy steadily | Benchmark territory | Lowest effort |
| Discretionary macro, copy trading, signals | Judgment-based | **[not researched]** | |

## 5. Asset classes

| Asset | Hours | Leverage | Cost profile | Solo-Canadian access |
|---|---|---|---|---|
| US stocks / ETFs | Alpaca: Sun 8pm to Fri 8pm ET (24/5); regular session 9:30am to 4pm | Margin available | Commission minimums, spread | Yes via IBKR Canada (API OK for US-listed only, CIRO Rule 3200) |
| Canadian-listed stocks | Exchange hours | Margin | Commission minimums | **No API orders for DIY accounts** (CIRO Rule 3200) |
| Options | Exchange hours | Built in | Per-contract fees, wide spreads | Yes, via IBKR; IBKR also lists a separate "Prediction Markets" category on its commissions page |
| Futures | Near 24/5 | Built in | Per-contract | Yes via IBKR; NinjaTrader also serves Canada (per BrokerChooser) |
| Forex / CFDs | 24/5 | High | Spread; retail loss rates are high: Oanda 75%, FXCM 63%, Forex.com 77% of retail CFD accounts lose money (broker disclosures on [BrokerChooser](https://brokerchooser.com/best-brokers/best-brokers-for-algo-trading-in-canada)) **[read]** | Available per BrokerChooser |
| Crypto spot | 24/7 | None on Canadian-registered platforms | Maker/taker fees of a few tenths of a percent | Yes, see section 6 |
| Crypto derivatives (perps, futures, options) | 24/7 | High | Fees plus funding | Not on Canadian-registered platforms, see section 6 |
| DeFi, yield, NFTs, prediction markets | Varies | Varies | Varies | **[not researched]** |

## 6. Crypto in depth

**Structure.** Markets run 24/7, are fragmented across many venues, and are far more
volatile than stocks. A bot has to run (and be monitored) around the clock.

**What drives returns.** Crypto returns have a strong time-series momentum effect, and
investor-attention proxies forecast future returns ([Liu & Tsyvinski 2020](https://doi.org/10.1093/rfs/hhaa113))
**[read]**. Three factors (market, size, momentum) capture the cross-section of
expected crypto returns, and ten stock-style characteristics produce significant
long-short excess returns that the three-factor model explains ([Liu, Tsyvinski & Wu 2022](https://doi.org/10.1111/jofi.13119))
**[read]**. That echoes the stock results in the strategy doc: signals show up where
markets are less mature, which is also where costs and risks are highest. Separately,
Makarov & Schoar (2020, [DOI](https://doi.org/10.1016/j.jfineco.2019.07.001)) studied
arbitrage across crypto exchanges; I recall large, recurring cross-exchange price
gaps but did not read the abstract, so treat that as **[not verified]**.

**What a Canadian can legally use.**
- CSA staff require crypto trading platforms serving Canadians to operate under
  registration or pre-registration undertakings that include **a prohibition on
  offering margin, credit or other leverage** to clients, along with custody and
  segregation requirements ([CSA Staff Notice 21-332, Feb 2023](https://www.osc.ca/sites/default/files/2023-02/csa_20230222_21-332_crypto-trading-platforms-pre-reg-undertakings.pdf))
  **[read]**. Secondary sources say the regime remains in force in 2026 and list
  Wealthsimple, Coinbase Canada and Kraken Canada among registered platforms
  **[secondary]**.
- So on Canadian-registered platforms crypto is **spot-only and unlevered**. Perpetual
  futures and high leverage live on offshore venues, which sit outside this regime and
  carry extra counterparty and legal risk; this repo does not consider them.
- API access exists: bot services such as 3Commas integrate with Kraken and Coinbase
  Advanced for Canadian users **[secondary]**. CIRO Rule 3200 concerns CIRO dealers'
  orders on Canadian marketplaces, so it should not apply to CSA-registered crypto
  platforms, but I did not verify this per platform **[not verified]**.

**Costs are much higher in percentage terms.** Published maker/taker ranges are roughly
0–0.25% / 0.1–0.4% on Kraken Pro and 0–0.4% / 0.05–0.6% on Coinbase Advanced
**[secondary]**. At a 0.4% taker fee a round trip costs 0.8%, versus about 0.036% for
the measured IBKR round trip on a $2,000 US-stock position, roughly 20 times more.
High-turnover crypto strategies are therefore even more cost-sensitive than stock ones.

**Other risks.** Custody and counterparty failure, price manipulation and wash
trading, rapidly changing regulation, and tax treatment (whether frequent trading is
taxed as business income in Canada) **[not researched]**. Crypto bot profitability
evidence **[not researched]**.

## 7. The possibility map for this project

Ranked by evidence quality, cost fit, accessibility and automation fit. These are
candidates to evaluate and paper-test, not predictions of what will make money.

1. **Low-turnover diversified US equities** (weekly or monthly, pooled model, nested
   walk-forward validation). The current plan; best fit with the cost structure.
2. **Trend following on a handful of liquid ETFs** (equity, bond, gold, and so on).
   The strongest long-run evidence of any style, very low turnover, and trivial to code,
   so it doubles as a baseline that any fancier model must beat. Testable today on
   Alpaca's paper account with ETFs.
3. **Crypto spot momentum, low turnover.** Documented momentum and size factors and a
   market that never closes, but costs of roughly 0.8% a round trip rule out frequent
   trading, and it carries custody and manipulation risk. Whether Alpaca's paper API
   supports crypto for a Canadian-resident user is **[not verified]**.
4. **LLM news-drift on mid/small caps**, forward paper-traded only.
5. **Options premium selling.** Available through IBKR, but the small-gains,
   rare-large-losses shape makes it a poor early choice.
6. **Intraday trading, HFT, market making, leverage, perpetual futures.** Not
   recommended: speed arms race, cost drag, or outside the Canadian regulatory regime.

The common thread is that anything with high turnover or built-in leverage is where the
evidence turns against retail, and anything low-turnover and diversified is where
the cost structure permits an edge to exist at all.

## 8. Source notes and open questions

- **Read at source:** Baron et al.; Budish et al.; Hurst et al.; Moskowitz et al.; Carr &
  Wu; Liu & Tsyvinski; Liu, Tsyvinski & Wu; Chen & Velikov; Novy-Marx & Velikov;
  Barber & Odean (abstracts via OpenAlex); S&P SPIVA Mid-Year 2026; CSA Staff Notice
  21-332; BrokerChooser's broker table.
- **Secondary only:** Medallion's returns; Canadian crypto platform registrations and
  their 2026 status; crypto fee ranges; the bot-service list.
- **Not read:** Makarov & Schoar; He et al. (no abstracts available).
- **Not researched:** copy trading, prop-firm programs, DeFi/MEV/NFTs, funding-rate
  carry returns, crypto bot profitability, crypto tax treatment, per-platform
  applicability of CIRO Rule 3200.
