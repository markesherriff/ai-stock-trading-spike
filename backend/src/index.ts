import "dotenv/config";
import cors from "cors";
import express, { type ErrorRequestHandler } from "express";
import { checkAlpacaConnection, getAlpaca } from "./alpaca.js";
import { accountRouter } from "./routes/account.js";
import { marketRouter } from "./routes/market.js";
import { ordersRouter } from "./routes/orders.js";
import { positionsRouter } from "./routes/positions.js";
import { signalRouter } from "./routes/signal.js";
import { costsRouter } from "./routes/costs.js";

const app = express();
const port = process.env.PORT ?? 8000;

app.use(cors({ origin: "http://localhost:5173" }));
app.use(express.json());

app.get("/api/health", async (_req, res) => {
  const { connected, detail } = await checkAlpacaConnection();
  if (!connected) {
    res.json({ alpaca_connected: false, market_open: null, detail });
    return;
  }
  const { isOpen } = await getAlpaca().trading.clock.legacyClock();
  res.json({ alpaca_connected: true, market_open: isOpen });
});

app.use("/api/account", accountRouter);
app.use("/api/positions", positionsRouter);
app.use("/api/market", marketRouter);
app.use("/api/orders", ordersRouter);
app.use("/api/signal", signalRouter);
app.use("/api/costs", costsRouter);

const errorHandler: ErrorRequestHandler = (err, _req, res, _next) => {
  console.error(err);
  const message = err instanceof Error ? err.message : "Unknown error";
  res.status(502).json({ detail: `Alpaca request failed: ${message}` });
};
app.use(errorHandler);

app.listen(port, () => {
  console.log(`AI Paper Trader backend listening on http://localhost:${port}`);
});
