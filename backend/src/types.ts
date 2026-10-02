export interface AccountSummary {
  account: string;
  equity: number | null;
  cash: number | null;
  buying_power: number | null;
}

export interface PositionOut {
  symbol: string;
  position: number;
  avg_cost: number;
  current_price: number | null;
}

export interface Quote {
  symbol: string;
  last: number | null;
}

export type OrderAction = "BUY" | "SELL";

export interface OrderRequest {
  symbol: string;
  action: OrderAction;
  quantity: number;
  limit_price?: number;
}

export interface OrderResult {
  order_id: string;
  symbol: string;
  action: OrderAction;
  quantity: number;
  limit_price: number | null;
  status: string;
}

export type SignalAction = "BUY" | "SELL" | "HOLD";

export interface Signal {
  symbol: string;
  action: SignalAction;
  reason: string;
}

export interface ReferenceQuote {
  bid: number;
  ask: number;
  mid: number;
  feed: string;
  quote_time: string;
  age_seconds: number;
}

export interface IbkrBreakdown {
  commission: number;
  exchange_and_clearing: number;
  regulatory: number;
  total: number;
}

export interface LiveBrokerFill {
  tiered: IbkrBreakdown;
  fixed: IbkrBreakdown;
}

export interface FillCost {
  order_id: string;
  symbol: string;
  side: OrderAction;
  quantity: number;
  fill_price: number;
  filled_at: string;
  commission: number;
  regulatory: { sec_fee: number; finra_taf: number; cat_fee: number; total: number };
  spread_slippage: number | null;
  reference_quote: ReferenceQuote | null;
  live_broker: LiveBrokerFill;
}

export interface CostSummary {
  commission: number;
  regulatory: number;
  spread_slippage: number;
  total: number;
  unpriced_fills: number;
}

export interface LiveBrokerSummary {
  name: string;
  tiered: IbkrBreakdown;
  fixed: IbkrBreakdown;
  assumptions: string[];
}

export interface CostsResponse {
  summary: CostSummary;
  live_broker: LiveBrokerSummary;
  fills: FillCost[];
  assumptions: string[];
}
