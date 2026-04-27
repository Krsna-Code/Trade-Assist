import os
import sys

import pandas as pd
import pandas_ta  # noqa: F401  – registers the .ta accessor on pd.DataFrame

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from config import (
    RSI_PERIOD,
    MACD_FAST,
    MACD_SLOW,
    MACD_SIGNAL,
    BB_PERIOD,
    BB_STD,
    VOLUME_MA_PERIOD,
)

_SIGNAL_THRESHOLDS = [
    (75, "STRONG_BULLISH"),
    (60, "BULLISH"),
    (40, "NEUTRAL"),
    (25, "BEARISH"),
]


def _score_to_signal(score: float) -> str:
    for threshold, label in _SIGNAL_THRESHOLDS:
        if score > threshold:
            return label
    return "STRONG_BEARISH"


def _score_rsi(rsi: float) -> float:
    if rsi < 30:
        return 80
    if rsi < 45:
        return 65
    if rsi < 55:
        return 50
    if rsi <= 70:
        return 60
    return 20


def _score_macd(hist: float, prev_hist: float) -> float:
    if hist > 0 and hist > prev_hist:
        return 70
    if hist > 0:
        return 60
    if hist < 0 and hist < prev_hist:
        return 25
    return 35


def _score_bb(close: float, lower: float, upper: float) -> float:
    if close < lower:
        return 75
    if close > upper:
        return 25
    return 50


def _score_vwap(close: float, vwap: float) -> float:
    return 65 if close > vwap else 35


def _score_volume(current_vol: float, vol_ma: float) -> float:
    return 70 if current_vol > 2 * vol_ma else 50


def compute_technical_signal(df: pd.DataFrame, ticker: str = "") -> dict:
    df = df.copy()

    rsi_series = df.ta.rsi(length=RSI_PERIOD)
    macd_df = df.ta.macd(fast=MACD_FAST, slow=MACD_SLOW, signal=MACD_SIGNAL)
    bb_df = df.ta.bbands(length=BB_PERIOD, std=BB_STD)
    vwap_series = df.ta.vwap()

    vol_ma = df["volume"].rolling(window=VOLUME_MA_PERIOD).mean()

    rsi_val = float(rsi_series.iloc[-1])

    hist_col = [c for c in macd_df.columns if "MACDh" in c][0]
    macd_hist = float(macd_df[hist_col].iloc[-1])
    macd_hist_prev = float(macd_df[hist_col].iloc[-2])

    lower_col = [c for c in bb_df.columns if "BBL" in c][0]
    upper_col = [c for c in bb_df.columns if "BBU" in c][0]
    bb_lower = float(bb_df[lower_col].iloc[-1])
    bb_upper = float(bb_df[upper_col].iloc[-1])

    close = float(df["close"].iloc[-1])
    vwap_val = float(vwap_series.iloc[-1])
    current_vol = float(df["volume"].iloc[-1])
    vol_ma_val = float(vol_ma.iloc[-1])

    rsi_score = _score_rsi(rsi_val)
    macd_score = _score_macd(macd_hist, macd_hist_prev)
    bb_score = _score_bb(close, bb_lower, bb_upper)
    vwap_score = _score_vwap(close, vwap_val)
    vol_score = _score_volume(current_vol, vol_ma_val)

    composite = (rsi_score + macd_score + bb_score + vwap_score + vol_score) / 5.0
    signal = _score_to_signal(composite)

    bb_position = "below_lower" if close < bb_lower else ("above_upper" if close > bb_upper else "inside")
    vwap_position = "above" if close > vwap_val else "below"
    volume_ratio = round(current_vol / vol_ma_val, 3) if vol_ma_val else None

    return {
        "signal": signal,
        "score": round(composite, 2),
        "rsi": round(rsi_val, 2),
        "macd_hist": round(macd_hist, 4),
        "bb_position": bb_position,
        "vwap_position": vwap_position,
        "volume_ratio": volume_ratio,
        "ticker": ticker,
    }
