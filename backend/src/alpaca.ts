import { Alpaca } from "@alpacahq/alpaca-trade-api";

// Credentials resolve from APCA_API_KEY_ID / APCA_API_SECRET_KEY env vars.
// `paper: true` is the default, but spelled out here since this project
// should never accidentally point at a live account.
//
// Constructed lazily so a missing .env doesn't crash the whole server at
// import time — routes see a clear "not configured" error instead.
let client: Alpaca | undefined;
let initError: string | undefined;

export function getAlpaca(): Alpaca {
  if (client) return client;
  if (!process.env.APCA_API_KEY_ID || !process.env.APCA_API_SECRET_KEY) {
    initError = "APCA_API_KEY_ID / APCA_API_SECRET_KEY are not set. Copy backend/.env.example to .env and fill in your Alpaca paper trading keys.";
    throw new Error(initError);
  }
  client = new Alpaca({ paper: true });
  return client;
}

export async function checkAlpacaConnection(): Promise<{ connected: boolean; detail?: string }> {
  try {
    await getAlpaca().trading.account.getAccount();
    return { connected: true };
  } catch (err) {
    return { connected: false, detail: err instanceof Error ? err.message : String(err) };
  }
}
