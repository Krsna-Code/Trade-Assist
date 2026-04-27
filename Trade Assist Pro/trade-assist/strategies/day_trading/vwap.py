import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

import pandas as pd
import pandas_ta as _pandas_ta  # side-effect import — registers the df.ta accessor
_ = _pandas_ta
from datetime import datetime, timezone
from config import VOLUME_MA_PERIOD


def vwap_signal(df: pd.DataFrame, ticker: str = "") -> dict:
    _default = {
        "strategy": "vwap",
        "ticker": ticker,
        "signal": "HOLD",
        "score": 50,
        "entry": None,
        "stop_loss": None,
        "target": None,
        "reason": "Insufficient data or error computing VWAP signal.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        if df is None or len(df) < VOLUME_MA_PERIOD + 2:
            return _default

        df = df.copy()
        df.ta.vwap(append=True)

        vwap_col = next((c for c in df.columns if c.upper().startswith("VWAP")), None)
        if vwap_col is None:
            return {**_default, "reason": "VWAP column not found after pandas_ta computation."}

        close = df["close"].iloc[-1]
        prev_close = df["close"].iloc[-2]
        vwap_now = df[vwap_col].iloc[-1]
        vwap_prev = df[vwap_col].iloc[-2]

        if pd.isna(vwap_now) or pd.isna(vwap_prev):
            return {**_default, "reason": "NaN values in VWAP calculation."}

        vol_ma = df["volume"].rolling(VOLUME_MA_PERIOD).mean().iloc[-1]
        current_vol = df["volume"].iloc[-1]

        if pd.isna(vol_ma) or vol_ma == 0:
            return {**_default, "reason": "Cannot compute volume moving average."}

        volume_spike = current_vol > 1.5 * vol_ma

        reclaim = (prev_close < vwap_prev) and (close > vwap_now)
        lose = (prev_close > vwap_prev) and (close < vwap_now)
        above_trending = close > vwap_now and not reclaim
        below_trending = close < vwap_now and not lose

        if reclaim and volume_spike:
            signal, score = "BUY", 70
            stop_loss = round(vwap_now * 0.995, 4)
            target = round(close * 1.015, 4)
            reason = (
                f"Price reclaimed VWAP ({vwap_now:.2f}) from below "
                f"with volume spike ({current_vol / vol_ma:.1f}x avg)."
            )
        elif lose and volume_spike:
            signal, score = "SELL", 30
            stop_loss = round(vwap_now * 1.005, 4)
            target = round(close * 0.985, 4)
            reason = (
                f"Price lost VWAP ({vwap_now:.2f}) from above "
                f"with volume spike ({current_vol / vol_ma:.1f}x avg)."
            )
        elif above_trending:
            signal, score = "BUY", 62
            stop_loss = round(vwap_now * 0.995, 4)
            target = round(close * 1.015, 4)
            reason = (
                f"Price ({close:.2f}) trending above VWAP ({vwap_now:.2f}); "
                f"mild bullish bias."
            )
        elif below_trending:
            signal, score = "SELL", 38
            stop_loss = round(vwap_now * 1.005, 4)
            target = round(close * 0.985, 4)
            reason = (
                f"Price ({close:.2f}) trending below VWAP ({vwap_now:.2f}); "
                f"mild bearish bias."
            )
        else:
            return {
                **_default,
                "entry": round(close, 4),
                "reason": f"Price ({close:.2f}) near VWAP ({vwap_now:.2f}); no clear directional signal.",
            }

        return {
            "strategy": "vwap",
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
        return {**_default, "reason": f"Error computing VWAP signal: {exc}"}
