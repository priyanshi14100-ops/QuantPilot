"""Creates four SIMULATED stock files in data/ (fictional companies, not real prices).

The prices come from a random-walk model with a fixed seed, so the same files are
produced every time. Run:  python generate_sample_data.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

# name: (start price, yearly drift, yearly volatility, typical daily volume)
STOCKS = {
    "ALPHA": (150.0, 0.18, 0.22, 2_000_000),
    "BRAVO": (80.0, 0.08, 0.30, 3_500_000),
    "CHARLIE": (320.0, 0.12, 0.16, 900_000),
    "DELTA": (45.0, -0.04, 0.38, 5_000_000),
}


def make_stock(rng, dates, market, start, drift, vol, base_volume):
    n = len(dates)
    daily_vol = vol / np.sqrt(252)
    scale = np.ones(n)
    scale[250:290] = 1.8                      # a short period of market stress
    noise = rng.normal(0, 1, n)
    returns = drift / 252 - 0.5 * daily_vol ** 2 + 0.4 * market + daily_vol * 0.9 * scale * noise
    close = start * np.exp(np.cumsum(returns))
    prev_close = np.concatenate([[start], close[:-1]])
    open_ = prev_close * (1 + rng.normal(0, 0.003, n))
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.006, n)))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.006, n)))
    volume = base_volume * rng.lognormal(0, 0.25, n) * (1 + 15 * np.abs(returns))
    return pd.DataFrame({
        "Date": dates.strftime("%Y-%m-%d"),
        "Open": open_.round(2), "High": high.round(2), "Low": low.round(2),
        "Close": close.round(2), "Volume": volume.astype(int),
    })


def main():
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2024-10-01", "2026-09-30")
    market = rng.normal(0, 0.008, len(dates))
    out_dir = Path(__file__).resolve().parent / "data"
    out_dir.mkdir(exist_ok=True)
    for name, (start, drift, vol, base_volume) in STOCKS.items():
        df = make_stock(rng, dates, market, start, drift, vol, base_volume)
        df["High"] = df[["Open", "High", "Close"]].max(axis=1)
        df["Low"] = df[["Open", "Low", "Close"]].min(axis=1)
        df.to_csv(out_dir / f"{name}.csv", index=False)
        print(f"{name}: {len(df)} rows written")


if __name__ == "__main__":
    main()
