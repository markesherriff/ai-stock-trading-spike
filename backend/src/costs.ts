import { getAlpaca } from "./alpaca.js";
import type { FillCost, ReferenceQuote } from "./types.js";

// Alpaca Brokerage Fee Schedule, revised 2026-10-01
// (https://files.alpaca.markets/disclosures/library/BrokFeeSched.pdf).
// Paper accounts don't deduct any of these — they're estimates of what a live account would pay.
export const COMMISSION_PER_SHARE = 0;
export const SEC_FEE_RATE = 0.0000206; // x sell trade value
export const FINRA_TAF_PER_SHARE = 0; // Alpaca currently passes through $0 (sells only)
export const CAT_FEE_PER_SHARE = 0.000003; // buys and sells

const MAX_QUOTE_AGE_SECONDS = 300;
// Free data plans can't query market data newer than ~15 minutes on SIP/BOATS.
const DELAYED_FEED_MIN_AGE_MS = 16 * 60_000;

export function round(value: number, decimals: number): number {
  const factor = 10 ** decimals;
  return Math.round(value * factor) / factor;
}

export function regulatoryFees(side: "BUY" | "SELL", qty: number, price: number) {
  const secFee = round(side === "SELL" ? SEC_FEE_RATE * qty * price : 0, 8);
  const finraTaf = round(side === "SELL" ? FINRA_TAF_PER_SHARE * qty : 0, 8);
  const catFee = round(CAT_FEE_PER_SHARE * qty, 8);
  return { sec_fee: secFee, finra_taf: finraTaf, cat_fee: catFee, total: round(secFee + finraTaf + catFee, 8) };
}

export function etDate(date: Date): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "America/New_York" }).format(date);
}

export function roundUpToCent(amount: number): number {
  return Math.ceil(amount * 100 - 1e-9) / 100;
}

/** Alpaca sums each fee type per account per day, then rounds each total up to the cent. */
export function billedRegulatoryTotal(fills: FillCost[]): number {
  const groups = new Map<string, number>();
  for (const fill of fills) {
    const day = etDate(new Date(fill.filled_at));
    for (const [type, amount] of Object.entries({
      sec: fill.regulatory.sec_fee,
      taf: fill.regulatory.finra_taf,
      cat: fill.regulatory.cat_fee,
    })) {
      const key = `${day}|${type}`;
      groups.set(key, (groups.get(key) ?? 0) + amount);
    }
  }
  let total = 0;
  for (const amount of groups.values()) total += roundUpToCent(amount);
  return total;
}

async function quoteFromFeed(
  symbol: string,
  submittedAt: Date,
  feed: "iex" | "sip" | "boats",
): Promise<ReferenceQuote | null> {
  try {
    const response = await getAlpaca().marketData.stocks.stockQuotes({
      symbols: symbol,
      start: new Date(submittedAt.getTime() - 10 * 60_000),
      end: submittedAt,
      feed,
      limit: 1,
      sort: "desc",
    } as Parameters<ReturnType<typeof getAlpaca>["marketData"]["stocks"]["stockQuotes"]>[0]);
    const quote = response.quotes?.[symbol]?.[0];
    if (!quote || !(quote.bp > 0) || !(quote.ap > 0) || quote.ap < quote.bp) return null;
    const age = (submittedAt.getTime() - new Date(quote.t).getTime()) / 1000;
    if (age > MAX_QUOTE_AGE_SECONDS) return null;
    return {
      bid: quote.bp,
      ask: quote.ap,
      mid: (quote.bp + quote.ap) / 2,
      feed,
      quote_time: new Date(quote.t).toISOString(),
      age_seconds: Math.max(0, age),
    };
  } catch {
    return null;
  }
}

/** Latest valid NBBO-style quote at or before the moment the order was submitted. */
export async function referenceQuoteAt(symbol: string, submittedAt: Date): Promise<ReferenceQuote | null> {
  const old = Date.now() - submittedAt.getTime() > DELAYED_FEED_MIN_AGE_MS;
  // sip covers 4am-8pm ET; boats is the Blue Ocean overnight session; iex is the only
  // feed free accounts can query for recent data.
  const feeds = old ? (["sip", "boats"] as const) : (["iex"] as const);
  const quotes = await Promise.all(feeds.map((feed) => quoteFromFeed(symbol, submittedAt, feed)));
  const valid = quotes.filter((q): q is ReferenceQuote => q !== null);
  valid.sort((a, b) => a.age_seconds - b.age_seconds);
  return valid[0] ?? null;
}

export function spreadSlippage(side: "BUY" | "SELL", qty: number, fillPrice: number, mid: number): number {
  const perShare = side === "BUY" ? fillPrice - mid : mid - fillPrice;
  return round(perShare * qty, 6);
}
