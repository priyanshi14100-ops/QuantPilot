"""A basic price-forecasting model (Linear Regression) and its evaluation."""
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

FEATURES = ["Close_t", "Close_t1", "Close_t2", "Close_t3", "Close_t4",
            "SMA_5", "SMA_20", "Return_1", "Volume_Change"]


def build_features(df):
    """One row per day. Every feature uses information up to that day only;
    the target is the NEXT day's closing price."""
    close = df["Close"]
    data = pd.DataFrame({"Date": df["Date"]})
    data["Close_t"] = close
    for k in range(1, 5):
        data[f"Close_t{k}"] = close.shift(k)
    data["SMA_5"] = close.rolling(5).mean()
    data["SMA_20"] = close.rolling(20).mean()
    data["Return_1"] = close.pct_change()
    data["Volume_Change"] = df["Volume"].pct_change()
    data["Target"] = close.shift(-1)
    return data


def run_forecast(df, test_size=0.2):
    data = build_features(df)
    latest = data.iloc[[-1]]                      # last day: its target is unknown
    data = data.dropna().reset_index(drop=True)

    split = int(len(data) * (1 - test_size))     # time order is kept: no shuffling
    train, test = data.iloc[:split], data.iloc[split:]

    model = make_pipeline(StandardScaler(), LinearRegression())
    model.fit(train[FEATURES], train["Target"])
    predicted = model.predict(test[FEATURES])
    actual = test["Target"].to_numpy()
    naive = test["Close_t"].to_numpy()            # baseline: tomorrow = today

    def errors(pred):
        return {
            "MAE": float(mean_absolute_error(actual, pred)),
            "RMSE": float(np.sqrt(mean_squared_error(actual, pred))),
            "MAPE %": float(np.mean(np.abs((actual - pred) / actual)) * 100),
            "R2": float(r2_score(actual, pred)),
        }

    direction_hits = np.sign(predicted - naive) == np.sign(actual - naive)
    next_day = float(model.predict(latest[FEATURES])[0])
    last_close = float(df["Close"].iloc[-1])

    result_frame = pd.DataFrame({"Date": test["Date"].to_numpy(), "Actual": actual,
                                 "Predicted": predicted, "Naive": naive})
    return {
        "model": errors(predicted),
        "naive": errors(naive),
        "directional_accuracy": float(np.mean(direction_hits) * 100),
        "train_rows": len(train),
        "test_rows": len(test),
        "train_end": train["Date"].iloc[-1],
        "test_start": test["Date"].iloc[0],
        "test_end": test["Date"].iloc[-1],
        "last_close": last_close,
        "next_day": next_day,
        "next_day_change %": (next_day / last_close - 1) * 100,
        "frame": result_frame,
    }
