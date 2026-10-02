#!/bin/bash
# Weekday-morning job: rebalance the 200-day trend baseline on Alpaca PAPER when the previous trading day
# was the last trading day of the month (src.live exits harmlessly on every other day).
cd "$(dirname "$0")/.." || exit 1
source .venv/bin/activate
mkdir -p data/live
{
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') ==="
  python -m src.live --strategy sma200_trend --place-orders 2>&1 | grep -v downloaded
} >> data/live/rebalance.log
