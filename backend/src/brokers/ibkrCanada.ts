import { etDate, round } from "../costs.js";
import type { IbkrBreakdown } from "../types.js";

// Interactive Brokers Canada, US-listed stocks, USD denominated, lowest volume tier
// (<= 300,000 shares/month). Source: interactivebrokers.ca/en/pricing/commissions-stocks.php
// (read 2026-10-02). Canadian DIY accounts can only API-trade US-listed securities
// (CIRO Rule 3200) — see docs/research-landscape.md.
const TIERED_PER_SHARE = 0.0035;
const TIERED_MIN = 0.35;
const FIXED_PER_SHARE = 0.005;
const FIXED_MIN = 1.0;
const MAX_PCT_OF_TRADE_VALUE = 0.01;

// Tiered only: NSCC/DTC clearing and IBKR's NYSE/FINRA pass-through (a fraction of commission).
const CLEARING_PER_SHARE = 0.0002;
const PASS_THROUGH_RATE = 0.000175 + 0.000563;

// ASSUMPTION: exchange fee for removing liquidity. IBKR adds it to marketable orders on both
// plans; the real figure varies by venue, so this is a conservative placeholder.
const EXCHANGE_REMOVE_LIQUIDITY_PER_SHARE = 0.003;

// Regulatory pass-throughs (identical on both plans).
const SEC_FEE_RATE = 0.0000206; // x sale value
const CAT_FEE_PER_SHARE = 0.000003;
// IBKR lists a TAF fee holiday for trades Oct 1 - Dec 31, 2026. Afterwards we assume FINRA's
// published 2026 rate ($0.000195/share, $9.79 cap), which is NOT confirmed on IBKR's page.
const TAF_PER_SHARE = 0.000195;
const TAF_CAP = 9.79;
const TAF_HOLIDAY = { start: "2026-10-01", end: "2026-12-31" };

type Plan = "tiered" | "fixed";

function commissionFor(plan: Plan, qty: number, tradeValue: number): number {
  const raw = plan === "tiered" ? TIERED_PER_SHARE * qty : FIXED_PER_SHARE * qty;
  const min = plan === "tiered" ? TIERED_MIN : FIXED_MIN;
  const cap = MAX_PCT_OF_TRADE_VALUE * tradeValue;
  // IBKR: when the cap is below the minimum, the cap is what gets charged.
  return Math.min(Math.max(raw, min), cap);
}

export function ibkrCanadaFees(
  plan: Plan,
  side: "BUY" | "SELL",
  qty: number,
  price: number,
  filledAt: Date,
): IbkrBreakdown {
  const tradeValue = qty * price;
  const commission = commissionFor(plan, qty, tradeValue);

  const exchange = EXCHANGE_REMOVE_LIQUIDITY_PER_SHARE * qty;
  const clearing = plan === "tiered" ? CLEARING_PER_SHARE * qty : 0;
  const passThrough = plan === "tiered" ? commission * PASS_THROUGH_RATE : 0;

  const day = etDate(filledAt);
  const inHoliday = day >= TAF_HOLIDAY.start && day <= TAF_HOLIDAY.end;
  const sec = side === "SELL" ? SEC_FEE_RATE * tradeValue : 0;
  const taf = side === "SELL" && !inHoliday ? Math.min(TAF_PER_SHARE * qty, TAF_CAP) : 0;
  const cat = CAT_FEE_PER_SHARE * qty;
  const regulatory = sec + taf + cat;

  const exchangeAndClearing = exchange + clearing + passThrough;
  return {
    commission: round(commission, 6),
    exchange_and_clearing: round(exchangeAndClearing, 6),
    regulatory: round(regulatory, 6),
    total: round(commission + exchangeAndClearing + regulatory, 6),
  };
}
