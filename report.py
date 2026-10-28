"""Builds the plain-text analytical report."""
from datetime import datetime

import analysis

DISCLAIMER = "Historical analysis and model predictions do not guarantee future market performance."


def build_report(stocks, selected, forecast_result):
    table = analysis.compare_table(stocks)
    lines = ["QUANTPILOT - ANALYTICAL REPORT",
             "Generated: " + datetime.now().strftime("%d %b %Y, %H:%M"),
             "Note: " + DISCLAIMER, "", "1. DATA SUMMARY", "-" * 60]
    for name, df in stocks.items():
        lines.append(f"{name:<8} {df['Date'].iloc[0]:%d %b %Y} to {df['Date'].iloc[-1]:%d %b %Y}"
                     f"   {len(df)} trading days   last close {df['Close'].iloc[-1]:.2f}")

    shown = table[["Total Return %", "Annual Return %", "Annual Volatility %", "Sharpe Ratio",
                   "Max Drawdown %", "VaR 95% (1-day) %"]].round(2)
    lines += ["", "2. RISK AND RETURN", "-" * 60, shown.to_string(),
              f"(Sharpe ratio uses an assumed risk-free rate of {analysis.RISK_FREE_RATE:.0%} a year.)"]

    lines += ["", "3. OBSERVATIONS", "-" * 60,
              f"- Highest total return: {table['Total Return %'].idxmax()} "
              f"({table['Total Return %'].max():.2f}%)",
              f"- Lowest total return: {table['Total Return %'].idxmin()} "
              f"({table['Total Return %'].min():.2f}%)",
              f"- Most volatile: {table['Annual Volatility %'].idxmax()} "
              f"({table['Annual Volatility %'].max():.2f}% a year)",
              f"- Least volatile: {table['Annual Volatility %'].idxmin()} "
              f"({table['Annual Volatility %'].min():.2f}% a year)",
              f"- Best Sharpe ratio: {table['Sharpe Ratio'].idxmax()} ({table['Sharpe Ratio'].max():.2f})",
              f"- Deepest drawdown: {table['Max Drawdown %'].idxmin()} "
              f"({table['Max Drawdown %'].min():.2f}%)"]
    if len(stocks) > 1:
        corr = analysis.return_correlation(stocks)
        pairs = [(corr.iloc[i, j], corr.index[i], corr.columns[j])
                 for i in range(len(corr)) for j in range(i + 1, len(corr))]
        best = max(pairs)
        lines.append(f"- Most correlated pair: {best[1]} and {best[2]} ({best[0]:.2f})")

    m, n = forecast_result["model"], forecast_result["naive"]
    verdict = ("beats" if m["MAE"] < n["MAE"] else "does not beat")
    lines += ["", f"4. FORECAST EVALUATION FOR {selected}", "-" * 60,
              f"Model: Linear Regression, next-day close. Training rows {forecast_result['train_rows']}, "
              f"test rows {forecast_result['test_rows']}.",
              f"Test period: {forecast_result['test_start']:%d %b %Y} to {forecast_result['test_end']:%d %b %Y}",
              f"MAE {m['MAE']:.2f} | RMSE {m['RMSE']:.2f} | MAPE {m['MAPE %']:.2f}% | R2 {m['R2']:.3f}",
              f"Baseline (tomorrow = today): MAE {n['MAE']:.2f} | RMSE {n['RMSE']:.2f}",
              f"Direction predicted correctly on {forecast_result['directional_accuracy']:.1f}% of test days.",
              f"On this test the model {verdict} the baseline.",
              f"Model estimate for the next trading day: {forecast_result['next_day']:.2f} "
              f"({forecast_result['next_day_change %']:+.2f}% from the last close).",
              "", DISCLAIMER]
    return "\n".join(lines)


def save_report(text, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path
