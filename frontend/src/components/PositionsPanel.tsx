import type { Position } from "../types";

export function PositionsPanel({ positions }: { positions: Position[] }) {
  return (
    <section className="panel">
      <h2>Positions</h2>
      {positions.length === 0 ? (
        <p className="muted">No open positions.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Quantity</th>
              <th>Avg Cost</th>
              <th>Current Price</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((p) => (
              <tr key={p.symbol}>
                <td>{p.symbol}</td>
                <td>{p.position}</td>
                <td>{p.avg_cost.toFixed(2)}</td>
                <td>{p.current_price !== null ? p.current_price.toFixed(2) : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
