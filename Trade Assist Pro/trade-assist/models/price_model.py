import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score
import joblib
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
__import__("pandas_ta")  # side-effect import: registers df.ta accessor


def _build_features(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()

    data["returns_1d"] = data["Close"].pct_change(1)
    data["returns_3d"] = data["Close"].pct_change(3)
    data["returns_5d"] = data["Close"].pct_change(5)

    data["volume_ratio"] = data["Volume"] / data["Volume"].rolling(20).mean()

    data["rsi_14"] = data.ta.rsi(length=14)

    macd = data.ta.macd()
    if macd is not None and not macd.empty:
        hist_col = [c for c in macd.columns if "MACDh" in c]
        data["macd_hist"] = macd[hist_col[0]] if hist_col else 0.0
    else:
        data["macd_hist"] = 0.0

    bb = data.ta.bbands(length=20)
    if bb is not None and not bb.empty:
        lower_col = [c for c in bb.columns if "BBL" in c]
        upper_col = [c for c in bb.columns if "BBU" in c]
        if lower_col and upper_col:
            lower = bb[lower_col[0]]
            upper = bb[upper_col[0]]
            band_range = upper - lower
            data["bb_pct"] = (data["Close"] - lower) / band_range.replace(0, np.nan)
        else:
            data["bb_pct"] = 0.5
    else:
        data["bb_pct"] = 0.5

    sma20 = data["Close"].rolling(20).mean()
    sma50 = data["Close"].rolling(50).mean()
    data["price_vs_sma20"] = (data["Close"] / sma20.replace(0, np.nan)) - 1
    data["price_vs_sma50"] = (data["Close"] / sma50.replace(0, np.nan)) - 1

    data["high_low_range"] = (data["High"] - data["Low"]) / data["Close"].replace(0, np.nan)

    data["target"] = (data["Close"].shift(-1) > data["Close"]).astype(int)

    return data


FEATURE_COLS = [
    "returns_1d", "returns_3d", "returns_5d",
    "volume_ratio", "rsi_14", "macd_hist", "bb_pct",
    "price_vs_sma20", "price_vs_sma50", "high_low_range",
]


class PriceModel:
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = f"models/saved/{ticker}_model.pkl"

    def train(self, df: pd.DataFrame) -> dict:
        data = _build_features(df)
        data = data.dropna(subset=FEATURE_COLS + ["target"])

        X = data[FEATURE_COLS].values
        y = data["target"].values

        X_scaled = self.scaler.fit_transform(X)

        self.model = XGBClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            use_label_encoder=False,
            eval_metric="logloss",
            random_state=42,
        )

        tscv = TimeSeriesSplit(n_splits=5)
        scores = []
        for train_idx, val_idx in tscv.split(X_scaled):
            X_tr, X_val = X_scaled[train_idx], X_scaled[val_idx]
            y_tr, y_val = y[train_idx], y[val_idx]
            self.model.fit(X_tr, y_tr)
            preds = self.model.predict(X_val)
            scores.append(accuracy_score(y_val, preds))

        self.model.fit(X_scaled, y)

        return {
            "accuracy": float(np.mean(scores)),
            "n_samples": len(y),
            "ticker": self.ticker,
        }

    def predict(self, df: pd.DataFrame) -> dict:
        data = _build_features(df)
        data = data.dropna(subset=FEATURE_COLS)

        if data.empty:
            return {
                "direction": "NEUTRAL",
                "probability": 0.5,
                "score": 50.0,
                "signal": "NEUTRAL",
                "ticker": self.ticker,
            }

        X = data[FEATURE_COLS].iloc[[-1]].values
        X_scaled = self.scaler.transform(X)

        proba = self.model.predict_proba(X_scaled)[0]
        up_prob = float(proba[1])

        direction = "UP" if up_prob >= 0.5 else "DOWN"
        score = round(up_prob * 100, 2)

        if up_prob >= 0.6:
            signal = "BULLISH"
        elif up_prob <= 0.4:
            signal = "BEARISH"
        else:
            signal = "NEUTRAL"

        return {
            "direction": direction,
            "probability": up_prob,
            "score": score,
            "signal": signal,
            "ticker": self.ticker,
        }

    def save(self):
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump({"model": self.model, "scaler": self.scaler}, self.model_path)

    def load(self):
        payload = joblib.load(self.model_path)
        self.model = payload["model"]
        self.scaler = payload["scaler"]


def get_signal(df: pd.DataFrame, ticker: str) -> dict:
    pm = PriceModel(ticker)
    try:
        pm.load()
    except (FileNotFoundError, KeyError):
        pm.train(df)
        pm.save()
    return pm.predict(df)
