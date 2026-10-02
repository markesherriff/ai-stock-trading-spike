import { useEffect, useState } from "react";
import { api } from "../api";
import type { CostsResponse } from "../types";

function usd(value: number): string {
  const sign = value < 0 ? "-" : "";
  const abs = Math.abs(value);
  const cents = abs * 100;
  let digits = 2;
  if (abs !== 0 && abs < 0.0001) digits = 6;
  else if (abs !== 0 && abs < 0.01) digits = 4;
  else if (Math.abs(cents - Math.round(cents)) > 1e-6) digits = 3;
  return `${sign}$${abs.toFixed(digits)}`;
}

export function CostsPanel({ refreshKey }: { refreshKey: number }) {
  const [costs, setCosts] = useState<CostsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .costs()
      .then((data) => {
        if (!cancelled) {
          setCosts(data);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      });
    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  return (
    <section className="panel">
      <h2>Estimated trading costs</h2>
      {error && <p className="error">{error}</p>}
      {!costs && !error && <p className="muted">Loading fills…</p>}
      {costs && costs.fills.length === 0 && <p className="muted">No filled orders yet.</p>}
      {costs && costs.fills.length > 0 && (
        <>
          <h3>On Alpaca (paper account)</h3>
          <dl className="stat-grid">
            <dt>Commission</dt>
            <dd>{usd(costs.summary.commission)}</dd>
            <dt>Regulatory (SEC + CAT)</dt>
            <dd>{usd(costs.summary.regulatory)}</dd>
            <dt>Spread / slippage</dt>
            <dd>{usd(costs.summary.spread_slippage)}</dd>
            <dt>
              <strong>Total</strong>
            </dt>
            <dd>
              <strong>{usd(costs.summary.total)}</strong>
            </dd>
          </dl>
          <h3>If traded live on {costs.live_broker.name} (Tiered plan)</h3>
          <dl className="stat-grid">
            <dt>Commission</dt>
            <dd>{usd(costs.live_broker.tiered.commission)}</dd>
            <dt>Exchange &amp; clearing</dt>
            <dd>{usd(costs.live_broker.tiered.exchange_and_clearing)}</dd>
            <dt>Regulatory (SEC + CAT)</dt>
            <dd>{usd(costs.live_broker.tiered.regulatory)}</dd>
            <dt>
              <strong>Total fees</strong>
            </dt>
            <dd>
              <strong>{usd(costs.live_broker.tiered.total)}</strong>
            </dd>
            <dt>Spread / slippage (same fills)</dt>
            <dd>{usd(costs.summary.spread_slippage)}</dd>
            <dt>
              <strong>All-in</strong>
            </dt>
            <dd>
              <strong>{usd(costs.live_broker.tiered.total + costs.summary.spread_slippage)}</strong>
            </dd>
          </dl>
          <p className="muted">
            The Fixed plan would charge {usd(costs.live_broker.fixed.total)} in fees for the same
            fills (US$1.00 minimum per order).
          </p>
          {costs.summary.unpriced_fills > 0 && (
            <p className="muted">
              {costs.summary.unpriced_fills} fill(s) had no usable quote, so their spread/slippage
              isn't included.
            </p>
          )}
          <table>
            <thead>
              <tr>
                <th>Fill</th>
                <th>Commission</th>
                <th>Regulatory</th>
                <th>Spread/slip</th>
                <th>IBKR fees</th>
              </tr>
            </thead>
            <tbody>
              {costs.fills.map((f) => (
                <tr key={f.order_id}>
                  <td title={new Date(f.filled_at).toLocaleString()}>
                    {f.side} {f.quantity} {f.symbol} @ {f.fill_price.toFixed(2)}
                  </td>
                  <td>{usd(f.commission)}</td>
                  <td>{usd(f.regulatory.total)}</td>
                  <td
                    title={
                      f.reference_quote
                        ? `mid ${f.reference_quote.mid.toFixed(3)} (bid ${f.reference_quote.bid} / ask ${f.reference_quote.ask}, ${f.reference_quote.feed})`
                        : "no usable quote"
                    }
                  >
                    {f.spread_slippage === null ? "n/a" : usd(f.spread_slippage)}
                  </td>
                  <td>{usd(f.live_broker.tiered.total)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <details className="assumptions">
            <summary>How the IBKR Canada estimate works</summary>
            <ul>
              {costs.live_broker.assumptions.map((a) => (
                <li key={a}>{a}</li>
              ))}
            </ul>
          </details>
          <details className="assumptions">
            <summary>How the Alpaca estimate works</summary>
            <ul>
              {costs.assumptions.map((a) => (
                <li key={a}>{a}</li>
              ))}
            </ul>
          </details>
        </>
      )}
    </section>
  );
}
