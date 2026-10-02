import { Router } from "express";
import { getAlpaca } from "../alpaca.js";
import type { PositionOut } from "../types.js";

export const positionsRouter = Router();

positionsRouter.get("/", async (_req, res, next) => {
  try {
    const positions = await getAlpaca().trading.positions.getAllOpenPositions();
    const out: PositionOut[] = positions.map((p) => ({
      symbol: p.symbol,
      position: Number(p.qty) * (p.side === "short" ? -1 : 1),
      avg_cost: Number(p.avgEntryPrice),
      current_price: p.currentPrice ? Number(p.currentPrice) : null,
    }));
    res.json(out);
  } catch (err) {
    next(err);
  }
});
