import { randomUUID } from "node:crypto";
import { Router } from "express";
import { getAlpaca } from "../alpaca.js";
import type { OrderRequest, OrderResult } from "../types.js";

export const ordersRouter = Router();

ordersRouter.post("/", async (req, res, next) => {
  try {
    const { symbol, action, quantity, limit_price } = req.body as OrderRequest;
    if (!symbol || (action !== "BUY" && action !== "SELL") || !quantity || quantity <= 0) {
      res.status(400).json({ detail: "symbol, action (BUY/SELL), and a positive quantity are required" });
      return;
    }

    const alpaca = getAlpaca();
    const upperSymbol = symbol.toUpperCase();
    const side = action === "BUY" ? "buy" : "sell";

    const { isOpen } = await alpaca.trading.clock.legacyClock();
    if (!isOpen && !limit_price) {
      res.status(400).json({
        detail:
          "Market is closed. Outside regular hours (pre-market/after-hours/overnight), only limit orders are accepted — set a limit price to trade now.",
      });
      return;
    }

    // A limit price opts into extended-hours execution (pre-market, after-hours,
    // and the 8pm-4am ET overnight session) — Alpaca requires limit (not market)
    // orders outside regular hours.
    const order = limit_price
      ? await alpaca.trading.orders.limit({
          symbol: upperSymbol,
          side,
          qty: quantity,
          limitPrice: limit_price,
          extendedHours: true,
          clientOrderId: randomUUID(),
        })
      : await alpaca.trading.orders.market({
          symbol: upperSymbol,
          side,
          qty: quantity,
          clientOrderId: randomUUID(),
        });

    const result: OrderResult = {
      order_id: order.id ?? "",
      symbol: upperSymbol,
      action,
      quantity,
      limit_price: limit_price ?? null,
      status: order.status ?? "unknown",
    };
    res.json(result);
  } catch (err) {
    next(err);
  }
});
