import type { AccountSummary } from "../types";

function formatCurrency(value: number | null): string {
  if (value === null) return "—";
  return value.toLocaleString(undefined, { style: "currency", currency: "USD" });
}

export function AccountPanel({ account }: { account: AccountSummary | null }) {
  return (
    <section className="panel">
      <h2>Account</h2>
      {account ? (
        <dl className="stat-grid">
          <dt>Account</dt>
          <dd>{account.account || "—"}</dd>
          <dt>Equity</dt>
          <dd>{formatCurrency(account.equity)}</dd>
          <dt>Cash</dt>
          <dd>{formatCurrency(account.cash)}</dd>
          <dt>Buying Power</dt>
          <dd>{formatCurrency(account.buying_power)}</dd>
        </dl>
      ) : (
        <p className="muted">Loading account…</p>
      )}
    </section>
  );
}
