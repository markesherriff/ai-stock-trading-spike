import { Router } from "express";
import { getAlpaca } from "../alpaca.js";
import { ibkrCanadaFees } from "../brokers/ibkrCanada.js";
import {
  COMMISSION_PER_SHARE,
  round,
  billedRegulatoryTotal,
  referenceQuoteAt,
  regulatoryFees,
  spreadSlippage,
} from "../costs.js";
import type { CostsResponse, FillCost, IbkrBreakdown, OrderAction } from "../types.js";

export const costsRouter = Router();

const FINAL_AFTER_MS = 16 * 60_000;
const cache = new Map<string, FillCost>();

costsRouter.get("/", async (req, res, next) => {
  try {
    const limit = Math.min(Number(req.query.limit) || 25, 100);
    const orders = await getAlpaca().trading.orders.getAllOrders({
      status: "closed",
      limit,
      direction: "desc",
    });

    const filled = orders.filter(
      (o) => o.assetClass === "us_equity" && Number(o.filledQty) > 0 && o.filledAvgPrice && o.filledAt && o.submittedAt,
    );

    const fills = await Promise.all(
      filled.map(async (o): Promise<FillCost> => {
        const id = o.id ?? "";
        const cached = cache.get(id);
        if (cached) return cached;

        const side: OrderAction = o.side === "sell" ? "SELL" : "BUY";
        const qty = Number(o.filledQty);
        const price = Number(o.filledAvgPrice);
        const submittedAt = new Date(o.submittedAt as Date);
        const filledAt = new Date(o.filledAt as Date);
        const reference = await referenceQuoteAt(o.symbol as string, submittedAt);

        const fill: FillCost = {
          order_id: id,
          symbol: o.symbol as string,
          side,
          quantity: qty,
          fill_price: price,
          filled_at: filledAt.toISOString(),
          commission: COMMISSION_PER_SHARE * qty,
          regulatory: regulatoryFees(side, qty, price),
          spread_slippage: reference ? spreadSlippage(side, qty, price, reference.mid) : null,
          reference_quote: reference,
          live_broker: {
            tiered: ibkrCanadaFees("tiered", side, qty, price, filledAt),
            fixed: ibkrCanadaFees("fixed", side, qty, price, filledAt),
          },
        };
        if (reference && Date.now() - submittedAt.getTime() > FINAL_AFTER_MS) cache.set(id, fill);
        return fill;
      }),
    );

    const commission = fills.reduce((sum, f) => sum + f.commission, 0);
    const regulatory = billedRegulatoryTotal(fills);
    const spread = round(fills.reduce((sum, f) => sum + (f.spread_slippage ?? 0), 0), 6);

    const sumPlan = (plan: "tiered" | "fixed"): IbkrBreakdown => ({
      commission: round(fills.reduce((a, f) => a + f.live_broker[plan].commission, 0), 6),
      exchange_and_clearing: round(fills.reduce((a, f) => a + f.live_broker[plan].exchange_and_clearing, 0), 6),
      regulatory: round(fills.reduce((a, f) => a + f.live_broker[plan].regulatory, 0), 6),
      total: round(fills.reduce((a, f) => a + f.live_broker[plan].total, 0), 6),
    });

    const response: CostsResponse = {
      summary: {
        commission,
        regulatory,
        spread_slippage: spread,
        total: round(commission + regulatory + spread, 6),
        unpriced_fills: fills.filter((f) => f.spread_slippage === null).length,
      },
      live_broker: {
        name: "Interactive Brokers Canada",
        tiered: sumPlan("tiered"),
        fixed: sumPlan("fixed"),
        assumptions: [
          "Why IBKR Canada: it's the only Canadian-accessible broker found with an order-placing API (TWS API), US stocks are the only thing a Canadian DIY account may API-trade (CIRO Rule 3200), and its per-order minimums are the lowest. Questrade's API is read-only for customers; Webull's OpenAPI is US-only; moomoo's minimum is US$1.99.",
          "Tiered plan (shown first, cheapest for small orders): US$0.0035/share, min US$0.35, max 1% of trade value; plus NSCC/DTC clearing US$0.0002/share and a pass-through of 0.0738% of commission. Fixed plan: US$0.005/share, min US$1.00, max 1%; clearing is included.",
          "ASSUMED: every fill removes liquidity and pays US$0.003/share exchange fee (IBKR adds it to marketable orders on both plans; the real amount varies by venue).",
          "Regulatory: SEC fee on sells (0.0000206 x value) + CAT US$0.000003/share. FINRA TAF is $0 during IBKR's fee holiday (Oct 1 - Dec 31, 2026); outside it we assume FINRA's 2026 rate of $0.000195/share (cap $9.79), which IBKR's page doesn't confirm.",
          "Not included: CAD/USD conversion (IBKR charges 0.2 bps with a US$2.00 minimum per conversion, so convert in bulk and hold USD), market-data subscriptions, and the spread/slippage shown separately.",
          "Source: interactivebrokers.ca commissions pages, read 2026-10-02. These are estimates; confirm against a live account's statements.",
        ],
      },
      fills,
      assumptions: [
        "Commission: Alpaca charges $0 on US equities for retail order flow.",
        "Regulatory: SEC fee on sells ($20.60 per $1M) + CAT fee on buys and sells ($0.000003/share); Alpaca currently passes through $0 FINRA TAF. Each fee type is summed per ET day and rounded up to the cent, per Alpaca's schedule (rev. 2026-10-01).",
        "Spread/slippage: fill price vs. the mid of the last quote at order submission (sip/boats for fills older than 16 min, iex for newer; stale >5 min quotes are skipped). Negative means price improvement.",
        "Paper accounts do not actually deduct regulatory fees; these are estimates of live-account costs.",
      ],
    };
    res.json(response);
  } catch (err) {
    next(err);
  }
});
