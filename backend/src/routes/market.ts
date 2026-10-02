import { Router } from "express";
import { getAlpaca } from "../alpaca.js";
import type { Quote } from "../types.js";

export const marketRouter = Router();

marketRouter.get("/quote/:symbol", async (req, res, next) => {
  try {
    const symbol = req.params.symbol.toUpperCase();
    const last = await getAlpaca().marketData.getLatestPrice(symbol);
    const quote: Quote = { symbol, last: last ?? null };
    res.json(quote);
  } catch (err) {
    next(err);
  }
});
