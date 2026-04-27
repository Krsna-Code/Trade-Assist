import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pandas as pd
import pandas_ta as _pandas_ta  # side-effect import — registers the df.ta accessor
_ = _pandas_ta
from datetime import datetime, timezone
from config import RSI_PERIOD, BB_PERIOD


def calls_puts_signal(df: pd.DataFrame, chain: dict, ticker: str = "") -> dict:
    _default = {
        "strategy": "calls_puts",
        "ticker": ticker,
        "signal": "HOLD",
        "score": 50,
        "direction": None,
        "strike": None,
        "expiry": None,
        "delta": None,
        "premium": None,
        "max_loss": None,
        "breakeven": None,
        "reason": "Insufficient data or error computing calls/puts signal.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        if df is None or len(df) < max(RSI_PERIOD, BB_PERIOD) + 5:
            return _default
        if not chain or "calls" not in chain or "puts" not in chain:
            return {**_default, "reason": "Option chain missing 'calls' or 'puts' key."}

        calls_df: pd.DataFrame = chain["calls"]
        puts_df: pd.DataFrame = chain["puts"]
        expiry: str = chain.get("expiry", "")
        spot: float = float(chain.get("spot", df["close"].iloc[-1]))  # used for breakeven context

        df = df.copy()
        df.ta.rsi(length=RSI_PERIOD, append=True)
        sma_col = f"SMA_{BB_PERIOD}"
        df.ta.sma(length=BB_PERIOD, append=True)

        rsi_col = f"RSI_{RSI_PERIOD}"
        if rsi_col not in df.columns or sma_col not in df.columns:
            return {**_default, "reason": "RSI or SMA column missing after indicator computation."}

        rsi = df[rsi_col].iloc[-1]
        sma = df[sma_col].iloc[-1]
        close = df["close"].iloc[-1]

        if pd.isna(rsi) or pd.isna(sma):
            return {**_default, "reason": "NaN in RSI or SMA values."}

        favour_puts = rsi < 45 and close < sma
        favour_calls = rsi > 55 and close > sma

        if favour_calls:
            direction = "CALL"
            options = calls_df.copy() if not calls_df.empty else pd.DataFrame()
            reason_prefix = f"RSI={rsi:.1f} and price above SMA ({sma:.2f}) favour calls."
        elif favour_puts:
            direction = "PUT"
            options = puts_df.copy() if not puts_df.empty else pd.DataFrame()
            reason_prefix = f"RSI={rsi:.1f} and price below SMA ({sma:.2f}) favour puts."
        else:
            return {
                **_default,
                "reason": (
                    f"No clear directional bias: RSI={rsi:.1f}, "
                    f"close={close:.2f}, SMA={sma:.2f}."
                ),
            }

        if options.empty:
            return {**_default, "reason": f"No {direction} contracts available in chain."}

        for col in ("delta", "strike", "lastPrice"):
            if col not in options.columns:
                return {**_default, "reason": f"Option chain missing required column: '{col}'."}

        options = options.dropna(subset=["delta", "strike", "lastPrice"])
        if options.empty:
            return {**_default, "reason": f"All {direction} contracts have NaN delta/strike/premium."}

        target_delta = 0.45 if direction == "CALL" else -0.45
        options = options.copy()
        options["_delta_dist"] = (options["delta"] - target_delta).abs()
        best = options.loc[options["_delta_dist"].idxmin()]

        strike = float(best["strike"])
        delta = float(best["delta"])
        premium = float(best["lastPrice"])
        max_loss = round(premium, 4)
        breakeven = round(strike + premium, 4) if direction == "CALL" else round(strike - premium, 4)

        return {
            "strategy": "calls_puts",
            "ticker": ticker,
            "direction": direction,
            "strike": strike,
            "expiry": expiry,
            "delta": round(delta, 4),
            "premium": round(premium, 4),
            "max_loss": max_loss,
            "breakeven": breakeven,
            "reason": (
                f"{reason_prefix} Selected {direction} strike={strike} "
                f"(delta={delta:.2f}, premium={premium:.2f}, breakeven={breakeven:.2f})."
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as exc:
        return {**_default, "reason": f"Error computing calls/puts signal: {exc}"}
