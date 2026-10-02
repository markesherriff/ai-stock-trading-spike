# Tooling & inspiration ideas

A running, unvetted list of external tools and examples worth considering as
the website and agent layer develop. Lighter than
[`research-landscape.md`](research-landscape.md) and
[`academic-literature-review.md`](academic-literature-review.md) — this is
captured ideas, not evaluated conclusions.

## TradingView

Charting widgets/library ([tradingview.com](https://www.tradingview.com)) for
embedding real candlestick + indicator charts in the React frontend instead of
hand-rolling them. There's a free embeddable widget and a more full-featured
Charting Library (licensing terms vary by use case). Worth evaluating once the
website needs more than a bare last-price number — e.g. to visualize the
moving averages the placeholder signal already computes.

## OKX Agent Trade Kit

<https://www.okx.com/agent-tradekit> — OKX's (crypto exchange) toolkit for
letting AI agents trade via natural language, shipped as:

- An **MCP server** — "talk to OKX using Claude, ChatGPT, or any AI supporting
  MCP."
- Plug-and-play **Claude Skills** (`npx skills add okx/agent-skills`), split
  into self-contained modules: market data (no auth required), trading
  (spot/futures/options/algo orders), portfolio (balances/PnL/fees).
- A **CLI** for terminal- and cron-job-based trading.

The relevant pattern here, independent of OKX/crypto specifically: once this
project's paper-trading backend ([`backend/`](../backend)) is stable, it could
be exposed as an MCP server or Claude Skill so trades can be placed via
natural language directly from Claude — as a complement to, or even instead
of, the React UI. The REST endpoints already built (account, positions,
quote, order, signal) map fairly directly onto MCP tool calls.

## "I Gave 3 AI Trading Bots $1,000" (Jev) + beebots.tech

- YouTube: <https://www.youtube.com/watch?v=8ijN8LGljKg> — Jev gives three AI
  trading bots $1,000 each and trades live.
- Live companion site: <https://beebots.tech> — tracks the three bots
  head-to-head in real time: "Bizzy" (the grinder), "Breezy" (the calculated
  one), "Boozy" (the degen), each with live equity, position status,
  trades-today count, fee budget used, funding, a "JEV'S LAST CALL" commentary
  feed, a leaderboard by equity, a "pick your bee" prediction game (who wins /
  who dies first), and a real-time decision stream of the bots' trades.

Ideas worth stealing for this project's own dashboard, once there's a live
paper-trading loop running:

- Give the signal/strategy a distinct **persona** and narrate its decisions,
  not just display numbers — more engaging to watch, and easier to reason
  about qualitatively when debugging.
- A transparent, live-updating **decision/reasoning stream** (what the model
  saw, what it decided, why) alongside the trade log — useful for debugging
  and for trust, separate from the formal backtest validation in
  `research-landscape.md`.
- Running **multiple strategy variants side-by-side** (e.g. different risk
  tolerances or feature sets) and comparing live performance, rather than
  only backtesting one strategy in isolation.
- Lightweight **gamification** (leaderboard, predictions) as a way to make a
  paper-trading demo engaging to show other people — a presentation-layer
  idea, not a substitute for the rigor the research docs call for.

These are all future-facing — not yet prioritized against the Next steps in
the main [README](../README.md). The project is still at the
placeholder-signal, basic-website stage.
