import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pandas as pd
from datetime import datetime, timezone
from config import OPTIONS_MIN_IV_RANK_STRADDLE


def straddle_signal(df: pd.DataFrame, chain: dict, iv_rank: float, ticker: str = "") -> dict:
    _default = {
        "strategy": "straddle",
        "ticker": ticker,
        "signal": "HOLD",
        "score": 50,
        "strike": None,
        "expiry": None,
        "call_premium": None,
        "put_premium": None,
        "total_cost": None,
        "breakeven_up": None,
        "breakeven_down": None,
        "required_move_pct": None,
        "iv_rank": iv_rank,
        "recommended": False,
        "reason": "Insufficient data or error computing straddle signal.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        if df is None or len(df) < 2:
            return _default
        if not chain or "calls" not in chain or "puts" not in chain:
            return {**_default, "reason": "Option chain missing 'calls' or 'puts' key."}

        calls_df: pd.DataFrame = chain["calls"]
        puts_df: pd.DataFrame = chain["puts"]
        expiry: str = chain.get("expiry", "")
        spot: float = float(chain.get("spot", df["close"].iloc[-1]))

        recommended = iv_rank < OPTIONS_MIN_IV_RANK_STRADDLE

        if calls_df.empty or puts_df.empty:
            return {
                **_default,
                "recommended": recommended,
                "reason": "Calls or puts chain is empty; cannot compute straddle.",
            }

        for side, frame in (("calls", calls_df), ("puts", puts_df)):
            for col in ("delta", "strike", "lastPrice"):
                if col not in frame.columns:
                    return {**_default, "reason": f"Option chain '{side}' missing column: '{col}'."}

        calls_clean = calls_df.dropna(subset=["delta", "strike", "lastPrice"]).copy()
        puts_clean = puts_df.dropna(subset=["delta", "strike", "lastPrice"]).copy()

        if calls_clean.empty or puts_clean.empty:
            return {**_default, "recommended": recommended, "reason": "No valid contracts after dropping NaNs."}

        calls_clean["_delta_dist"] = (calls_clean["delta"] - 0.50).abs()
        puts_clean["_delta_dist"] = (puts_clean["delta"] - (-0.50)).abs()

        best_call = calls_clean.loc[calls_clean["_delta_dist"].idxmin()]
        best_put = puts_clean.loc[puts_clean["_delta_dist"].idxmin()]

        call_strike = float(best_call["strike"])
        put_strike = float(best_put["strike"])
        strike = round((call_strike + put_strike) / 2, 2)

        call_premium = float(best_call["lastPrice"])
        put_premium = float(best_put["lastPrice"])
        total_cost = round(call_premium + put_premium, 4)

        breakeven_up = round(strike + total_cost, 4)
        breakeven_down = round(strike - total_cost, 4)
        required_move_pct = round(total_cost / spot * 100, 2)

        if recommended:
            reason = (
                f"IV rank={iv_rank:.1f} (< {OPTIONS_MIN_IV_RANK_STRADDLE}) — options are cheap; "
                f"straddle recommended. Total cost={total_cost:.2f}, "
                f"breakevens=[{breakeven_down:.2f}, {breakeven_up:.2f}], "
                f"requires {required_move_pct:.1f}% move."
            )
        else:
            reason = (
                f"IV rank={iv_rank:.1f} (>= {OPTIONS_MIN_IV_RANK_STRADDLE}) — options are expensive; "
                f"straddle not recommended. Total cost={total_cost:.2f} would require "
                f"{required_move_pct:.1f}% move to profit."
            )

        return {
            "strategy": "straddle",
            "ticker": ticker,
            "strike": strike,
            "expiry": expiry,
            "call_premium": round(call_premium, 4),
            "put_premium": round(put_premium, 4),
            "total_cost": total_cost,
            "breakeven_up": breakeven_up,
            "breakeven_down": breakeven_down,
            "required_move_pct": required_move_pct,
            "iv_rank": iv_rank,
            "recommended": recommended,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as exc:
        return {**_default, "reason": f"Error computing straddle signal: {exc}"}
