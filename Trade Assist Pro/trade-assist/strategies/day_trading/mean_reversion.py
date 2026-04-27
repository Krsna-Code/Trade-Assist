import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

import pandas as pd
import pandas_ta as _pandas_ta  # side-effect import — registers the df.ta accessor
_ = _pandas_ta
from datetime import datetime, timezone
from config import RSI_PERIOD, BB_PERIOD


def mean_reversion_signal(df: pd.DataFrame, ticker: str = "") -> dict:
    _default = {
        "strategy": "mean_reversion",
        "ticker": ticker,
        "signal": "HOLD",
        "score": 50,
        "entry": None,
        "stop_loss": None,
        "target": None,
        "reason": "Insufficient data or error computing mean reversion signal.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        if df is None or len(df) < max(RSI_PERIOD, BB_PERIOD) + 5:
            return _default

        df = df.copy()
        df.ta.rsi(length=RSI_PERIOD, append=True)
        df.ta.bbands(length=BB_PERIOD, std=2, append=True)

        rsi_col = f"RSI_{RSI_PERIOD}"
        lower_col = f"BBL_{BB_PERIOD}_2.0"
        mid_col = f"BBM_{BB_PERIOD}_2.0"
        upper_col = f"BBU_{BB_PERIOD}_2.0"

        for col in (rsi_col, lower_col, mid_col, upper_col):
            if col not in df.columns:
                return {**_default, "reason": f"Missing computed column: {col}"}

        rsi = df[rsi_col].iloc[-1]
        lower_bb = df[lower_col].iloc[-1]
        mid_bb = df[mid_col].iloc[-1]
        upper_bb = df[upper_col].iloc[-1]
        close = df["close"].iloc[-1]

        if any(pd.isna(v) for v in (rsi, lower_bb, mid_bb, upper_bb)):
            return {**_default, "reason": "NaN values in RSI or Bollinger Bands calculation."}

        if rsi < 30 and close <= lower_bb:
            signal, score = "STRONG_BUY", 90
            stop_loss = round(lower_bb * 0.99, 4)
            target = round(mid_bb, 4)
            reason = (
                f"RSI={rsi:.1f} (oversold) and price ({close:.2f}) at/below "
                f"lower BB ({lower_bb:.2f}); strong mean reversion setup."
            )
        elif rsi < 40 and close <= lower_bb:
            signal, score = "BUY", 72
            stop_loss = round(lower_bb * 0.99, 4)
            target = round(mid_bb, 4)
            reason = (
                f"RSI={rsi:.1f} and price ({close:.2f}) at/below "
                f"lower BB ({lower_bb:.2f}); mean reversion long setup."
            )
        elif rsi > 70 and close >= upper_bb:
            signal, score = "STRONG_SELL", 10
            stop_loss = round(upper_bb * 1.01, 4)
            target = round(mid_bb, 4)
            reason = (
                f"RSI={rsi:.1f} (overbought) and price ({close:.2f}) at/above "
                f"upper BB ({upper_bb:.2f}); strong mean reversion short setup."
            )
        elif rsi > 60 and close >= upper_bb:
            signal, score = "SELL", 28
            stop_loss = round(upper_bb * 1.01, 4)
            target = round(mid_bb, 4)
            reason = (
                f"RSI={rsi:.1f} and price ({close:.2f}) at/above "
                f"upper BB ({upper_bb:.2f}); mean reversion short setup."
            )
        else:
            return {
                **_default,
                "entry": round(close, 4),
                "reason": (
                    f"No mean reversion extreme detected. RSI={rsi:.1f}, "
                    f"price={close:.2f}, BB=[{lower_bb:.2f}, {upper_bb:.2f}]."
                ),
            }

        return {
            "strategy": "mean_reversion",
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
        return {**_default, "reason": f"Error computing mean reversion signal: {exc}"}
