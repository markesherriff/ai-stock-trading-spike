import type {
  AccountSummary,
  CostsResponse,
  OrderAction,
  OrderResult,
  Position,
  Quote,
  Signal,
} from "./types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${body}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () =>
    request<{ alpaca_connected: boolean; market_open: boolean | null; detail?: string }>("/api/health"),
  account: () => request<AccountSummary>("/api/account"),
  positions: () => request<Position[]>("/api/positions"),
  costs: () => request<CostsResponse>("/api/costs"),
  quote: (symbol: string) => request<Quote>(`/api/market/quote/${symbol}`),
  signal: (symbol: string) => request<Signal>(`/api/signal/${symbol}`),
  placeOrder: (symbol: string, action: OrderAction, quantity: number, limitPrice?: number) =>
    request<OrderResult>("/api/orders", {
      method: "POST",
      body: JSON.stringify({ symbol, action, quantity, limit_price: limitPrice }),
    }),
};
