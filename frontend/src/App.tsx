import { useCallback, useEffect, useState } from "react";
import "./App.css";
import { api } from "./api";
import { AccountPanel } from "./components/AccountPanel";
import { CostsPanel } from "./components/CostsPanel";
import { PositionsPanel } from "./components/PositionsPanel";
import { TradePanel } from "./components/TradePanel";
import type { AccountSummary, Position } from "./types";

function App() {
  const [connected, setConnected] = useState<boolean | null>(null);
  const [marketOpen, setMarketOpen] = useState<boolean | null>(null);
  const [account, setAccount] = useState<AccountSummary | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const refresh = useCallback(async () => {
    try {
      const health = await api.health();
      setConnected(health.alpaca_connected);
      setMarketOpen(health.market_open);
      if (!health.alpaca_connected) {
        setLoadError(health.detail ?? "Not connected to Alpaca.");
        return;
      }
      const [accountData, positionsData] = await Promise.all([api.account(), api.positions()]);
      setAccount(accountData);
      setPositions(positionsData);
      setRefreshKey((k) => k + 1);
      setLoadError(null);
    } catch (err) {
      setConnected(false);
      setLoadError(err instanceof Error ? err.message : String(err));
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <main className="app">
      <header>
        <h1>AI Paper Trader</h1>
        <div className="badges">
          <span className={`status status-${connected ? "ok" : "down"}`}>
            {connected === null ? "Checking Alpaca…" : connected ? "Alpaca connected" : "Alpaca disconnected"}
          </span>
          {marketOpen !== null && (
            <span className={`status status-${marketOpen ? "ok" : "down"}`}>
              {marketOpen ? "Market open" : "Market closed"}
            </span>
          )}
        </div>
      </header>

      {loadError && (
        <p className="error">
          {loadError} Make sure the backend is running with valid Alpaca paper trading API keys
          (see backend/.env.example).
        </p>
      )}

      <AccountPanel account={account} />
      <PositionsPanel positions={positions} />
      <TradePanel marketOpen={marketOpen} onOrderPlaced={refresh} />
      <CostsPanel refreshKey={refreshKey} />
    </main>
  );
}

export default App;
