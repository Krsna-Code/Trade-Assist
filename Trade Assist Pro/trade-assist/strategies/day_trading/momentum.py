import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

import pandas as pd
from datetime import datetime, timezone
from config import VOLUME_MA_PERIOD


def momentum_signal(df: pd.DataFrame, ticker: str = "") -> dict:
    _default = {
        "strategy": "momentum",
        "ticker": ticker,
        "signal": "HOLD",
        "score": 50,
        "entry": None,
        "stop_loss": None,
        "target": None,
        "reason": "Insufficient data or error computing momentum signal.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        if df is None or len(df) < 21:
            return _default

        df = df.copy()
        close = df["close"].iloc[-1]
        high_20 = df["high"].iloc[-21:-1].max()
        low_20 = df["low"].iloc[-21:-1].min()
        vol_ma = df["volume"].iloc[-21:-1].rolling(VOLUME_MA_PERIOD).mean().iloc[-1]
        current_vol = df["volume"].iloc[-1]

        if pd.isna(vol_ma) or vol_ma == 0:
            return _default

        vol_ratio = current_vol / vol_ma
        breakout_up = close > high_20
        breakout_down = close < low_20

        if breakout_up:
            if vol_ratio > 2.0:
                signal, score = "BUY", 85
                reason = (
                    f"Price broke above 20-day high ({high_20:.2f}) "
                    f"on strong volume ({vol_ratio:.1f}x avg)."
                )
            elif vol_ratio >= 1.5:
                signal, score = "BUY", 70
                reason = (
                    f"Price broke above 20-day high ({high_20:.2f}) "
                    f"on elevated volume ({vol_ratio:.1f}x avg)."
                )
            else:
                signal, score = "BUY", 55
                reason = (
                    f"Price broke above 20-day high ({high_20:.2f}) "
                    f"but volume is weak ({vol_ratio:.1f}x avg)."
                )
            entry = close
            stop_loss = round(entry * 0.98, 4)
            target = round(entry * 1.04, 4)
        elif breakout_down:
            if vol_ratio > 2.0:
                signal, score = "SELL", 15
                reason = (
                    f"Price broke below 20-day low ({low_20:.2f}) "
                    f"on strong volume ({vol_ratio:.1f}x avg)."
                )
            else:
                signal, score = "SELL", 30
                reason = (
                    f"Price broke below 20-day low ({low_20:.2f}) "
                    f"on volume ({vol_ratio:.1f}x avg)."
                )
            entry = close
            stop_loss = round(entry * 1.02, 4)
            target = round(entry * 0.96, 4)
        else:
            return {**_default, "reason": "No breakout detected; price within recent 20-day range."}

        return {
            "strategy": "momentum",
            "ticker": ticker,
            "signal": signal,
            "score": score,
            "entry": round(close, 4),
            "stop_loss": stop_loss,
            "target": target,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as exc:
        return {**_default, "reason": f"Error computing momentum signal: {exc}"}
