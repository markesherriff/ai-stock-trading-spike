import { Router } from "express";
import { getAlpaca } from "../alpaca.js";
import type { AccountSummary } from "../types.js";

export const accountRouter = Router();

accountRouter.get("/", async (_req, res, next) => {
  try {
    const account = await getAlpaca().trading.account.getAccount();
    const summary: AccountSummary = {
      account: account.id,
      equity: account.equity ? Number(account.equity) : null,
      cash: account.cash ? Number(account.cash) : null,
      buying_power: account.buyingPower ? Number(account.buyingPower) : null,
    };
    res.json(summary);
  } catch (err) {
    next(err);
  }
});
