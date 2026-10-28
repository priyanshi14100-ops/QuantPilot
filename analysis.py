"""Statistics: returns, moving averages, volatility and risk measures."""
import numpy as np
import pandas as pd

TRADING_DAYS = 252
RISK_FREE_RATE = 0.05      # assumed yearly risk-free rate used in the Sharpe ratio


def add_indicators(df, short=20, long=50):
    out = df.copy()
    out["Daily_Return"] = out["Close"].pct_change()
    out["SMA_20"] = out["Close"].rolling(short).mean()
    out["SMA_50"] = out["Close"].rolling(long).mean()
    out["Volatility_20"] = out["Daily_Return"].rolling(20).std() * np.sqrt(TRADING_DAYS)
    out["Cumulative_Return"] = (1 + out["Daily_Return"].fillna(0)).cumprod() - 1
    return out


def daily_returns(df):
    return df["Close"].pct_change().dropna()


def total_return(df):
    return float(df["Close"].iloc[-1] / df["Close"].iloc[0] - 1)


def annual_return(returns):
    return float(np.mean(returns) * TRADING_DAYS)


def annual_volatility(returns):
    return float(np.std(returns, ddof=1) * np.sqrt(TRADING_DAYS))


def sharpe_ratio(returns, risk_free=RISK_FREE_RATE):
    vol = annual_volatility(returns)
    return float((annual_return(returns) - risk_free) / vol) if vol > 0 else float("nan")


def max_drawdown(close):
    running_peak = close.cummax()
    return float((close / running_peak - 1).min())


def value_at_risk(returns, confidence=0.95):
    """Historical one-day VaR: the loss that was exceeded on only 5% of days."""
    return float(-np.percentile(returns, (1 - confidence) * 100))


def risk_summary(df):
    returns = daily_returns(df)
    return {
        "Last Close": float(df["Close"].iloc[-1]),
        "Total Return %": total_return(df) * 100,
        "Annual Return %": annual_return(returns) * 100,
        "Annual Volatility %": annual_volatility(returns) * 100,
        "Sharpe Ratio": sharpe_ratio(returns),
        "Max Drawdown %": max_drawdown(df["Close"]) * 100,
        "VaR 95% (1-day) %": value_at_risk(returns) * 100,
        "Best Day %": float(returns.max() * 100),
        "Worst Day %": float(returns.min() * 100),
        "Average Volume": float(df["Volume"].mean()),
    }


def compare_table(stocks):
    rows = {name: risk_summary(df) for name, df in stocks.items()}
    return pd.DataFrame(rows).T


def aligned_close(stocks):
    """Close prices of all stocks on the dates they have in common."""
    closes = {name: df.set_index("Date")["Close"] for name, df in stocks.items()}
    return pd.concat(closes, axis=1, join="inner").dropna()


def normalised_prices(stocks):
    closes = aligned_close(stocks)
    return closes / closes.iloc[0] * 100


def return_correlation(stocks):
    return aligned_close(stocks).pct_change().dropna().corr()
