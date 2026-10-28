# QuantPilot - Stock Market Data Analytics System

A Python desktop application that loads historical stock prices from CSV files, calculates
returns, moving averages, volatility and risk measures, compares several stocks, draws charts,
tests a simple Linear Regression forecast and writes an analytical report.

**Note:** Historical analysis and model predictions do not guarantee future market performance.
The sample files in `data/` are SIMULATED prices for fictional companies, not real market data.

## Run (Windows, VS Code)
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    python main.py

## CSV format
Columns: Date (YYYY-MM-DD), Open, High, Low, Close, Volume. The file name becomes the stock
name (ALPHA.csv -> ALPHA). Select several files at once to compare stocks.

## Other commands
    python generate_sample_data.py          # recreate the simulated sample files
    python -m unittest discover -s tests    # run the tests
