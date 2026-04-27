import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pandas as pd
import pandas_ta as _pandas_ta  # side-effect import — registers the df.ta accessor
_ = _pandas_ta
from datetime import datetime, timezone
from config import RSI_PERIOD, BB_PERIOD, OPTIONS_DELTA_MIN


def covered_call_signal(df: pd.DataFrame, chain: dict, ticker: str = "") -> dict:
    _default = {
        "strategy": "covered_call",
        "ticker": ticker,
        "signal": "HOLD",
        "score": 50,
        "strike": None,
        "expiry": None,
        "premium_per_share": None,
        "annualised_yield": None,
        "delta": None,
        "max_profit": None,
        "stop_loss_note": None,
        "reason": "Insufficient data or error computing covered call signal.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        if df is None or len(df) < max(RSI_PERIOD, BB_PERIOD) + 5:
            return _default
        if not chain or "calls" not in chain:
            return {**_default, "reason": "Option chain missing 'calls' key."}

        calls_df: pd.DataFrame = chain["calls"]
        expiry: str = chain.get("expiry", "")
        spot: float = float(chain.get("spot", df["close"].iloc[-1]))

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

        mild_bullish = 50 <= rsi <= 65 and close >= sma * 0.99
        if not mild_bullish:
            return {
                **_default,
                "reason": (
                    f"Conditions not met for covered call: RSI={rsi:.1f} "
                    f"(need 50-65), price={close:.2f}, SMA={sma:.2f}."
                ),
            }

        if calls_df.empty:
            return {**_default, "reason": "No call contracts available in chain."}

        for col in ("delta", "strike", "lastPrice"):
            if col not in calls_df.columns:
                return {**_default, "reason": f"Option chain missing required column: '{col}'."}

        otm_calls = calls_df[calls_df["strike"] > spot].dropna(subset=["delta", "strike", "lastPrice"])
        if otm_calls.empty:
            return {**_default, "reason": "No OTM call contracts found above current spot price."}

        target_delta = OPTIONS_DELTA_MIN  # 0.30 — conservative income
        otm_calls = otm_calls.copy()
        otm_calls["_delta_dist"] = (otm_calls["delta"] - target_delta).abs()
        best = otm_calls.loc[otm_calls["_delta_dist"].idxmin()]

        strike = float(best["strike"])
        delta = float(best["delta"])
        premium = float(best["lastPrice"])

        try:
            expiry_date = pd.to_datetime(expiry)
            today = pd.Timestamp.now(tz="UTC").normalize().tz_localize(None)
            weeks_to_expiry = max((expiry_date - today).days / 7, 0.01)
        except Exception:
            weeks_to_expiry = 4.0

        annualised_yield = round((premium / spot) * (52 / weeks_to_expiry) * 100, 2)
        stop_loss_note = f"Consider closing position if stock falls below {round(spot * 0.95, 2)}."

        return {
            "strategy": "covered_call",
            "ticker": ticker,
            "strike": strike,
            "expiry": expiry,
            "premium_per_share": round(premium, 4),
            "annualised_yield": annualised_yield,
            "delta": round(delta, 4),
            "max_profit": round(premium, 4),
            "stop_loss_note": stop_loss_note,
            "reason": (
                f"RSI={rsi:.1f} and price ({close:.2f}) above SMA ({sma:.2f}) indicate "
                f"mild bullish trend. Selling OTM call at strike={strike} "
                f"(delta={delta:.2f}) for premium={premium:.2f} "
                f"yields ~{annualised_yield:.1f}% annualised."
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as exc:
        return {**_default, "reason": f"Error computing covered call signal: {exc}"}
