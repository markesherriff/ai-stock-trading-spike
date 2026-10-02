# Prediction approach ideas

What the model should predict isn't decided yet — both framings below are kept
open as options, alongside a fast validation method that works for either one.

## Fast validation loop: hold out the most recent day(s)

- Pull a chunk of historical daily candles for a symbol (or basket), and
  withhold the last 1–2 (or N) days from whatever the model sees.
- Train/fit on everything before the cutoff, predict day N+1 (or N+1..N+2),
  and compare the prediction against what actually happened.
- This is the walk-forward validation [`research-landscape.md`](research-landscape.md)
  already requires before anything is trusted enough to touch paper trading —
  and it means iterating doesn't require waiting on new real-time data: the
  same historical pull can be re-sliced over and over just by moving the
  cutoff earlier.
- Carried-over caveats from that doc: a single holdout isn't enough to trust —
  this needs to be repeated across many different cutoff points (rolling
  walk-forward, not one train/test split), and any headline accuracy or Sharpe
  ratio should eventually go through Deflated Sharpe Ratio / Probability of
  Backtest Overfitting correction before being believed, exactly as required
  there for a full strategy backtest.

## Option A: direction/signal classification

- Predict whether the next period's move clears a threshold — up / down /
  flat, or directly a BUY/SELL/HOLD label — rather than a price.
- Matches the gradient-boosting-on-engineered-features approach already
  chosen in the README's Stack table and Next steps, and the strongest
  evidence base in `research-landscape.md` (Kelly, Malamud & Zhou on
  complexity adding real predictive value; the PEAD drift literature).
- The output maps directly onto a trading decision — "will this beat costs"
  is the question that actually matters for P&L, not "what will the exact
  price be."

## Option B: exact candle/price regression

- Predict the actual next OHLC or close price — a literal "predicted candle,"
  not just a label.
- Harder problem than direction classification: a small percentage price
  error can still get the direction wrong, and `research-landscape.md`
  specifically found raw price-level ML prediction collapses out-of-sample
  (the 13-model SPY study: 80–86% in-sample accuracy down to 47–49%
  out-of-sample — worse than a coin flip).
- Worth keeping anyway: a predicted-candle output is more visual and
  intuitive for a dashboard — e.g. overlaying "predicted" vs. "actual"
  candles on a chart (see the TradingView idea in
  [`tooling-ideas.md`](tooling-ideas.md)) — and a regression output can always
  be converted into a direction signal after the fact
  (`predicted_close > last_close`), so building it doesn't foreclose Option A.
- Live example of this exact approach: [Krafer Agent Trader (KAT)](https://krafercrypto.com/)
  — a line of ML models predicting "future price action, bar-by-bar," trained
  primarily on Bitcoin but also benchmarked on at least one stock (MSFT).
  Worth noting regardless of its own validity as a product:
  - It ships **multiple models tuned to different prediction horizons**
    rather than one model for everything: "Panther" (directional
    bias/candle-color only), "Bobcat" (~30 min, short-term/volatile),
    "Lion" (~1 hr, "more stable"), "Tiger" (~3 hr, "very mild predictions").
    A useful structural idea independent of this specific product: horizon
    and model confidence/volatility are coupled, and separating them into
    distinct models may be cleaner than one model outputting both.
  - It reports accuracy **against an explicit random-walk baseline**
    (e.g. "KAT Lion: avg 64.8% vs. Random Walk ±0.025%" on BTC, "KAT Bobcat:
    avg 63.7%" on MSFT) rather than a bare accuracy number — the same
    instinct behind the Deflated Sharpe Ratio / PBO correction
    `research-landscape.md` already calls for: a result only means something
    next to a naive baseline, not in isolation. Still worth treating these
    specific published numbers skeptically — a vendor self-reporting
    accuracy against its own chosen baseline is exactly the kind of claim
    this project's own research doc says to distrust by default until it
    survives independent out-of-sample / walk-forward scrutiny.
  - It also runs prediction "brackets" (contests with public leaderboards,
    e.g. a BTC 4-year-cycle bracket with scored submissions) — reinforcing
    the gamification/leaderboard idea already captured from beebots.tech in
    [`tooling-ideas.md`](tooling-ideas.md).

## Where this stands

Neither option is chosen yet. The likely shape is: a direction-classification
model is what should actually drive trades, given the evidence, but a
regression/candle-prediction model might be worth building too — purely for
the "watch it predict against real data" visual/demo value — independent of
which one ends up gating real paper trades. Not yet built; this is captured
ahead of implementation per the Next steps in the main [README](../README.md).
