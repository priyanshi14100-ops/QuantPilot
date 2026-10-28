"""Reads stock CSV files and cleans them into Pandas DataFrames."""
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = ["Date", "Open", "High", "Low", "Close", "Volume"]
NUMBER_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]
MIN_ROWS = 60


def ticker_from_path(file_path):
    """The file name without .csv becomes the stock name (ALPHA.csv -> ALPHA)."""
    return Path(file_path).stem.upper()


def load_stock(file_path):
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip().str.title()

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError("The CSV file is missing these columns: " + ", ".join(missing))

    df = df[REQUIRED_COLUMNS].copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for column in NUMBER_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna()
    df = df[(df["Close"] > 0) & (df["Volume"] >= 0)]
    df = df.drop_duplicates(subset="Date")
    df = df.sort_values("Date").reset_index(drop=True)

    if len(df) < MIN_ROWS:
        raise ValueError(
            f"Only {len(df)} valid rows found. At least {MIN_ROWS} are needed."
        )
    return df


def load_many(file_paths):
    """Loads several files. Returns (stocks, errors): a dict of clean data and a list of messages."""
    stocks, errors = {}, []
    for path in file_paths:
        name = ticker_from_path(path)
        try:
            stocks[name] = load_stock(path)
        except Exception as error:  # show a clear message instead of crashing
            errors.append(f"{Path(path).name}: {error}")
    return stocks, errors
