"""Download daily bars for every S&P 500 member since 2016 and report coverage.

    python -m src.download_universe
"""

from __future__ import annotations

import json

from .data import ROOT, download_bars
from .universe import load_membership, members_on, tickers_since

START = "2016-01-04"


def main() -> None:
    from datetime import date, timedelta

    end = (date.today() - timedelta(days=1)).isoformat()
    membership = load_membership()
    tickers = tickers_since(membership, START)
    print(f"{len(tickers)} tickers were S&P 500 members since {START}; downloading bars {START} -> {end}")
    counts = download_bars(tickers, START, end)
    missing = [t for t, n in counts.items() if n == 0]
    print(f"\nWith data: {len(tickers) - len(missing)} | no data: {len(missing)}")
    print("No data:", ", ".join(missing))

    print("\nCoverage of point-in-time membership (share of members with price data):")
    for day in ["2016-01-04", "2018-01-02", "2020-01-02", "2022-01-03", "2024-01-02", "2026-01-02"]:
        members = members_on(membership, day)
        have = [m for m in members if counts.get(m, 0) > 0]
        print(f"  {day}: {len(have)}/{len(members)} = {len(have) / len(members):.1%}")
    out = ROOT / "data" / "universe" / "coverage.json"
    out.write_text(json.dumps({"counts": counts, "missing": missing}, indent=2))


if __name__ == "__main__":
    main()
