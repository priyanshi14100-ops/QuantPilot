"""Chart functions. Each one takes data and returns a Matplotlib Figure,
so the Tkinter window can place it inside a tab."""
import matplotlib.dates as mdates
import numpy as np
import seaborn as sns
from matplotlib.figure import Figure

import analysis

sns.set_theme(style="whitegrid")
COLOURS = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3"]
DATE_FORMAT = mdates.DateFormatter("%b %Y")


def _message_figure(text):
    fig = Figure(figsize=(9, 5), dpi=100)
    ax = fig.add_subplot(111)
    ax.axis("off")
    ax.text(0.5, 0.5, text, ha="center", va="center", fontsize=13)
    return fig


def create_price_volume_chart(df, ticker):
    d = analysis.add_indicators(df)
    fig = Figure(figsize=(9, 5.4), dpi=100)
    grid = fig.add_gridspec(2, 1, height_ratios=[3, 1], hspace=0.08)
    ax1 = fig.add_subplot(grid[0])
    ax2 = fig.add_subplot(grid[1], sharex=ax1)
    ax1.plot(d["Date"], d["Close"], color=COLOURS[0], linewidth=1.3, label="Close")
    ax1.plot(d["Date"], d["SMA_20"], color=COLOURS[1], linewidth=1.3, label="20-day average")
    ax1.plot(d["Date"], d["SMA_50"], color=COLOURS[2], linewidth=1.3, label="50-day average")
    ax1.set_title(f"{ticker}: Closing Price with Moving Averages")
    ax1.set_ylabel("Price")
    ax1.legend(loc="lower right")
    ax1.tick_params(labelbottom=False)
    ax2.bar(d["Date"], d["Volume"] / 1e6, color="#8C8C8C", width=1.0, linewidth=0)
    ax2.set_ylabel("Volume (millions)")
    ax2.xaxis.set_major_formatter(DATE_FORMAT)
    fig.subplots_adjust(left=0.09, right=0.97, top=0.93, bottom=0.09)
    return fig


def create_returns_chart(df, ticker):
    d = analysis.add_indicators(df)
    fig = Figure(figsize=(10, 4.4), dpi=100)
    ax1, ax2 = fig.subplots(1, 2, gridspec_kw={"width_ratios": [1, 1.3]})
    sns.histplot(d["Daily_Return"].dropna() * 100, bins=40, kde=True, color=COLOURS[0], ax=ax1)
    ax1.axvline(0, color="black", linewidth=0.8)
    ax1.set_title(f"{ticker}: Daily Returns")
    ax1.set_xlabel("Daily return (%)")
    ax1.set_ylabel("Number of days")
    ax2.plot(d["Date"], d["Volatility_20"] * 100, color=COLOURS[3], linewidth=1.3)
    ax2.set_title("20-day Rolling Volatility (annualised)")
    ax2.set_ylabel("Volatility (%)")
    ax2.xaxis.set_major_formatter(DATE_FORMAT)
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    fig.subplots_adjust(left=0.07, right=0.98, top=0.9, bottom=0.14, wspace=0.22)
    return fig


def create_comparison_chart(stocks):
    if len(stocks) < 2:
        return _message_figure("Load at least two stocks to compare them.")
    prices = analysis.normalised_prices(stocks)
    fig = Figure(figsize=(9, 5), dpi=100)
    ax = fig.add_subplot(111)
    for i, name in enumerate(prices.columns):
        ax.plot(prices.index, prices[name], label=name, color=COLOURS[i % len(COLOURS)], linewidth=1.5)
    ax.axhline(100, color="black", linewidth=0.8, linestyle="--")
    ax.set_title("Stock Comparison: Price Rebased to 100 at the Start")
    ax.set_ylabel("Rebased price")
    ax.xaxis.set_major_formatter(DATE_FORMAT)
    ax.legend(loc="upper left")
    fig.subplots_adjust(left=0.08, right=0.97, top=0.92, bottom=0.09)
    return fig


def create_risk_return_chart(stocks):
    if len(stocks) < 2:
        return _message_figure("Load at least two stocks to compare risk and return.")
    table = analysis.compare_table(stocks)
    fig = Figure(figsize=(10, 4.6), dpi=100)
    ax1, ax2 = fig.subplots(1, 2, gridspec_kw={"width_ratios": [1, 1.1]})
    sns.heatmap(analysis.return_correlation(stocks), annot=True, fmt=".2f", cmap="Blues",
                vmin=0, vmax=1, cbar=False, square=True, ax=ax1)
    ax1.set_title("Correlation of Daily Returns")
    for i, (name, row) in enumerate(table.iterrows()):
        ax2.scatter(row["Annual Volatility %"], row["Annual Return %"], s=110,
                    color=COLOURS[i % len(COLOURS)], zorder=3)
        ax2.annotate(name, (row["Annual Volatility %"], row["Annual Return %"]),
                     textcoords="offset points", xytext=(7, 6))
    ax2.axhline(0, color="black", linewidth=0.8)
    ax2.set_title("Risk versus Return")
    ax2.set_xlabel("Annual volatility (%)")
    ax2.set_ylabel("Annual return (%)")
    ax2.margins(0.15)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.9, bottom=0.14, wspace=0.28)
    return fig


def create_forecast_chart(result, ticker):
    frame = result["frame"]
    fig = Figure(figsize=(9, 4.8), dpi=100)
    ax = fig.add_subplot(111)
    ax.plot(frame["Date"], frame["Actual"], color=COLOURS[0], linewidth=1.5, label="Actual close")
    ax.plot(frame["Date"], frame["Predicted"], color=COLOURS[1], linewidth=1.3,
            linestyle="--", label="Model prediction")
    ax.set_title(f"{ticker}: Predicted versus Actual Close (test period, one day ahead)")
    ax.set_ylabel("Price")
    ax.xaxis.set_major_formatter(DATE_FORMAT)
    ax.legend(loc="upper left")
    fig.subplots_adjust(left=0.09, right=0.97, top=0.92, bottom=0.09)
    return fig
