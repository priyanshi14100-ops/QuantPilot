import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.figure import Figure

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import analysis, charts, data_loader, forecast, report  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data"


def sample_stocks():
    return data_loader.load_many(sorted(DATA.glob("*.csv")))[0]


class TestLoading(unittest.TestCase):
    def test_sample_files_load(self):
        stocks = sample_stocks()
        self.assertEqual(sorted(stocks), ["ALPHA", "BRAVO", "CHARLIE", "DELTA"])
        for df in stocks.values():
            self.assertEqual(list(df.columns), data_loader.REQUIRED_COLUMNS)
            self.assertTrue(df["Date"].is_monotonic_increasing)

    def test_missing_column_message(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "BAD.csv"
            pd.read_csv(DATA / "ALPHA.csv").drop(columns=["Volume", "High"]).to_csv(path, index=False)
            with self.assertRaises(ValueError) as ctx:
                data_loader.load_stock(path)
            self.assertIn("High", str(ctx.exception))
            self.assertIn("Volume", str(ctx.exception))

    def test_bad_rows_removed(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "DIRTY.csv"
            df = pd.read_csv(DATA / "ALPHA.csv")
            df["Close"] = df["Close"].astype(object)
            df.loc[5, "Close"] = "abc"
            df.loc[9, "Date"] = "not a date"
            df.loc[12, "Close"] = -4
            df.to_csv(path, index=False)
            clean = data_loader.load_stock(path)
            self.assertEqual(len(clean), len(df) - 3)

    def test_too_few_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "SHORT.csv"
            pd.read_csv(DATA / "ALPHA.csv").head(20).to_csv(path, index=False)
            with self.assertRaises(ValueError):
                data_loader.load_stock(path)


class TestAnalysis(unittest.TestCase):
    def test_daily_return(self):
        df = pd.DataFrame({"Close": [100.0, 102.0, 99.96]})
        self.assertTrue(np.allclose(analysis.daily_returns(df), [0.02, -0.02]))

    def test_moving_average(self):
        df = pd.DataFrame({"Close": np.arange(1.0, 61.0), "Volume": 1})
        out = analysis.add_indicators(df)
        self.assertAlmostEqual(out["SMA_20"].iloc[19], 10.5)
        self.assertTrue(np.isnan(out["SMA_20"].iloc[18]))

    def test_volatility(self):
        returns = pd.Series([0.01, -0.02, 0.015, 0.0, -0.005])
        self.assertAlmostEqual(analysis.annual_volatility(returns),
                               float(np.std(returns, ddof=1) * np.sqrt(252)))

    def test_max_drawdown(self):
        self.assertAlmostEqual(analysis.max_drawdown(pd.Series([100, 120, 90, 110.0])), -0.25)

    def test_var_and_total_return(self):
        returns = pd.Series(np.linspace(-0.05, 0.05, 101))
        self.assertAlmostEqual(analysis.value_at_risk(returns), 0.045, places=6)
        self.assertAlmostEqual(analysis.total_return(pd.DataFrame({"Close": [50.0, 75.0]})), 0.5)

    def test_comparison_and_correlation(self):
        stocks = sample_stocks()
        self.assertEqual(len(analysis.compare_table(stocks)), 4)
        corr = analysis.return_correlation(stocks)
        self.assertTrue(np.allclose(np.diag(corr), 1.0))
        self.assertAlmostEqual(analysis.normalised_prices(stocks).iloc[0].mean(), 100.0)


class TestForecast(unittest.TestCase):
    def test_split_is_chronological_and_metrics_finite(self):
        result = forecast.run_forecast(sample_stocks()["ALPHA"])
        self.assertLess(result["train_end"], result["test_start"])
        total = result["train_rows"] + result["test_rows"]
        self.assertEqual(result["train_rows"], int(total * 0.8))
        for value in result["model"].values():
            self.assertTrue(np.isfinite(value))
        self.assertTrue(0 <= result["directional_accuracy"] <= 100)

    def test_features_use_no_future_data(self):
        df = sample_stocks()["BRAVO"]
        data = forecast.build_features(df).dropna().reset_index(drop=True)
        row = data.iloc[10]
        position = df.index[df["Date"] == row["Date"]][0]
        self.assertEqual(row["Close_t"], df["Close"].iloc[position])
        self.assertEqual(row["Target"], df["Close"].iloc[position + 1])


class TestOutputs(unittest.TestCase):
    def test_all_charts_return_figures(self):
        stocks = sample_stocks()
        df = stocks["ALPHA"]
        result = forecast.run_forecast(df)
        figs = [charts.create_price_volume_chart(df, "ALPHA"), charts.create_returns_chart(df, "ALPHA"),
                charts.create_comparison_chart(stocks), charts.create_risk_return_chart(stocks),
                charts.create_forecast_chart(result, "ALPHA"),
                charts.create_comparison_chart({"ALPHA": df})]
        for fig in figs:
            self.assertIsInstance(fig, Figure)

    def test_report_text_and_file(self):
        stocks = sample_stocks()
        text = report.build_report(stocks, "ALPHA", forecast.run_forecast(stocks["ALPHA"]))
        self.assertIn(report.DISCLAIMER, text)
        for name in stocks:
            self.assertIn(name, text)
        with tempfile.TemporaryDirectory() as folder:
            path = report.save_report(text, Path(folder) / "r.txt")
            self.assertTrue(path.exists() and path.stat().st_size > 500)


if __name__ == "__main__":
    unittest.main(verbosity=2)
