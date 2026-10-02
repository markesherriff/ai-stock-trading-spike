import { Router } from "express";
import { TimeFrame } from "@alpacahq/alpaca-trade-api";
import { getAlpaca } from "../alpaca.js";
import type { Signal } from "../types.js";

export const signalRouter = Router();

const SHORT_WINDOW = 5;
const LONG_WINDOW = 20;

/**
 * Placeholder "AI" signal: a simple moving-average crossover.
 *
 * This stands in for the gradient-boosting model under development in
 * src/ (repo root) — swap it out once that model is trained and validated.
 */
signalRouter.get("/:symbol", async (req, res, next) => {
  try {
    const symbol = req.params.symbol.toUpperCase();
    const end = new Date();
    const start = new Date(end);
    start.setDate(start.getDate() - LONG_WINDOW * 3);

    const bars = await getAlpaca().marketData.getStockBarsFor(symbol, {
      timeframe: TimeFrame.Day,
      start,
      end,
      feed: "iex", // free-tier data feed; SIP requires a paid subscription
    });

    if (bars.length < LONG_WINDOW) {
      const signal: Signal = { symbol, action: "HOLD", reason: "Not enough historical data yet" };
      res.json(signal);
      return;
    }

    const closes = bars.map((b) => b.close);
    const shortMa = average(closes.slice(-SHORT_WINDOW));
    const longMa = average(closes.slice(-LONG_WINDOW));

    let signal: Signal;
    if (shortMa > longMa) {
      signal = {
        symbol,
        action: "BUY",
        reason: `${SHORT_WINDOW}-day MA (${shortMa.toFixed(2)}) above ${LONG_WINDOW}-day MA (${longMa.toFixed(2)})`,
      };
    } else if (shortMa < longMa) {
      signal = {
        symbol,
        action: "SELL",
        reason: `${SHORT_WINDOW}-day MA (${shortMa.toFixed(2)}) below ${LONG_WINDOW}-day MA (${longMa.toFixed(2)})`,
      };
    } else {
      signal = { symbol, action: "HOLD", reason: "Moving averages are flat" };
    }
    res.json(signal);
  } catch (err) {
    next(err);
  }
});

function average(values: number[]): number {
  return values.reduce((sum, v) => sum + v, 0) / values.length;
}
