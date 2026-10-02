import { useState } from "react";
import { api } from "../api";
import type { OrderResult, Quote, Signal } from "../types";

export function TradePanel({
  marketOpen,
  onOrderPlaced,
}: {
  marketOpen: boolean | null;
  onOrderPlaced: () => void;
}) {
  const [symbol, setSymbol] = useState("AAPL");
  const [quantity, setQuantity] = useState(1);
  const [limitPrice, setLimitPrice] = useState("");
  const [quote, setQuote] = useState<Quote | null>(null);
  const [signal, setSignal] = useState<Signal | null>(null);
  const [orderResult, setOrderResult] = useState<OrderResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function withBusy(fn: () => Promise<void>) {
    setBusy(true);
    setError(null);
    try {
      await fn();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  const handleQuote = () =>
    withBusy(async () => {
      const result = await api.quote(symbol);
      setQuote(result);
      // Outside regular hours a limit price is required — prefill from the
      // last trade so the overnight/extended-hours order has a sane default.
      if (marketOpen === false && result.last !== null && !limitPrice) {
        setLimitPrice(result.last.toFixed(2));
      }
    });

  const handleSignal = () =>
    withBusy(async () => {
      setSignal(await api.signal(symbol));
    });

  const handleOrder = (action: "BUY" | "SELL") =>
    withBusy(async () => {
      const parsedLimitPrice = limitPrice ? Number(limitPrice) : undefined;
      const result = await api.placeOrder(symbol, action, quantity, parsedLimitPrice);
      setOrderResult(result);
      onOrderPlaced();
    });

  return (
    <section className="panel">
      <h2>Trade</h2>
      {marketOpen === false && (
        <p className="muted">
          Market is closed — a limit price is required (pre-market/after-hours/overnight orders
          must be limit orders).
        </p>
      )}
      <div className="trade-form">
        <label>
          Symbol
          <input
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            disabled={busy}
          />
        </label>
        <label>
          Quantity
          <input
            type="number"
            min={1}
            value={quantity}
            onChange={(e) => setQuantity(Number(e.target.value))}
            disabled={busy}
          />
        </label>
        <label>
          Limit Price {marketOpen === false ? "(required)" : "(optional)"}
          <input
            type="number"
            min={0}
            step="0.01"
            placeholder={marketOpen === false ? "required" : "market order"}
            value={limitPrice}
            onChange={(e) => setLimitPrice(e.target.value)}
            disabled={busy}
          />
        </label>
      </div>

      <div className="button-row">
        <button onClick={handleQuote} disabled={busy}>
          Get Quote
        </button>
        <button onClick={handleSignal} disabled={busy}>
          Get AI Signal
        </button>
        <button onClick={() => handleOrder("BUY")} disabled={busy}>
          Buy (paper)
        </button>
        <button onClick={() => handleOrder("SELL")} disabled={busy}>
          Sell (paper)
        </button>
      </div>

      {quote && (
        <p>
          <strong>{quote.symbol}</strong> last: {quote.last ?? "—"}
        </p>
      )}
      {signal && (
        <p className={`signal signal-${signal.action.toLowerCase()}`}>
          AI signal for <strong>{signal.symbol}</strong>: {signal.action} — {signal.reason}
        </p>
      )}
      {orderResult && (
        <p>
          Order #{orderResult.order_id}: {orderResult.action} {orderResult.quantity}{" "}
          {orderResult.symbol}
          {orderResult.limit_price !== null && ` @ limit $${orderResult.limit_price}`} —{" "}
          {orderResult.status}
        </p>
      )}
      {error && <p className="error">{error}</p>}
    </section>
  );
}
