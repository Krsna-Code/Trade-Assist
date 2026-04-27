import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pandas as pd
from datetime import datetime, timezone


def spread_signal(df: pd.DataFrame, chain: dict, direction: str = "bull", ticker: str = "") -> dict:
    _default = {
        "strategy": f"{direction}_spread",
        "ticker": ticker,
        "signal": "HOLD",
        "score": 50,
        "direction": direction,
        "long_strike": None,
        "short_strike": None,
        "net_debit": None,
        "max_profit": None,
        "max_loss": None,
        "breakeven": None,
        "risk_reward_ratio": None,
        "expiry": None,
        "reason": "Insufficient data or error computing spread signal.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        direction = direction.lower().strip()
        if direction not in ("bull", "bear"):
            return {**_default, "reason": f"Invalid direction '{direction}'; must be 'bull' or 'bear'."}

        if df is None or len(df) < 2:
            return _default

        if not chain:
            return {**_default, "reason": "Option chain is empty or None."}

        expiry: str = chain.get("expiry", "")
        spot: float = float(chain.get("spot", df["close"].iloc[-1]))

        if direction == "bull":
            options_df: pd.DataFrame = chain.get("calls", pd.DataFrame())
            side_label = "Bull Call Spread"
            long_target_delta = 0.50
            short_target_delta = 0.25
        else:
            options_df: pd.DataFrame = chain.get("puts", pd.DataFrame())
            side_label = "Bear Put Spread"
            long_target_delta = -0.50
            short_target_delta = -0.25

        if options_df is None or options_df.empty:
            return {
                **_default,
                "reason": f"No {'call' if direction == 'bull' else 'put'} contracts available in chain.",
            }

        for col in ("delta", "strike", "lastPrice"):
            if col not in options_df.columns:
                return {**_default, "reason": f"Option chain missing required column: '{col}'."}

        options_clean = options_df.dropna(subset=["delta", "strike", "lastPrice"]).copy()
        if len(options_clean) < 2:
            return {**_default, "reason": "Need at least 2 valid contracts to construct a spread."}

        options_clean["_long_dist"] = (options_clean["delta"] - long_target_delta).abs()
        options_clean["_short_dist"] = (options_clean["delta"] - short_target_delta).abs()

        long_leg = options_clean.loc[options_clean["_long_dist"].idxmin()]
        long_strike = float(long_leg["strike"])
        long_premium = float(long_leg["lastPrice"])
        long_delta = float(long_leg["delta"])

        short_candidates = options_clean[options_clean["strike"] != long_strike].copy()
        if short_candidates.empty:
            return {**_default, "reason": "Cannot find a separate contract for the short leg."}

        short_leg = short_candidates.loc[short_candidates["_short_dist"].idxmin()]
        short_strike = float(short_leg["strike"])
        short_premium = float(short_leg["lastPrice"])
        short_delta = float(short_leg["delta"])

        net_debit = round(long_premium - short_premium, 4)
        spread_width = abs(short_strike - long_strike)
        max_profit = round(spread_width - net_debit, 4)
        max_loss = round(net_debit, 4)

        if direction == "bull":
            breakeven = round(long_strike + net_debit, 4)
            reason = (
                f"{side_label}: buy call at strike={long_strike} (delta={long_delta:.2f}), "
                f"sell call at strike={short_strike} (delta={short_delta:.2f}). "
                f"Net debit={net_debit:.2f}, max profit={max_profit:.2f}, breakeven={breakeven:.2f}."
            )
        else:
            breakeven = round(long_strike - net_debit, 4)
            reason = (
                f"{side_label}: buy put at strike={long_strike} (delta={long_delta:.2f}), "
                f"sell put at strike={short_strike} (delta={short_delta:.2f}). "
                f"Net debit={net_debit:.2f}, max profit={max_profit:.2f}, breakeven={breakeven:.2f}."
            )

        risk_reward_ratio = round(max_profit / max_loss, 2) if max_loss > 0 else None

        return {
            "strategy": f"{direction}_spread",
            "ticker": ticker,
            "direction": direction,
            "long_strike": long_strike,
            "short_strike": short_strike,
            "net_debit": net_debit,
            "max_profit": max_profit,
            "max_loss": max_loss,
            "breakeven": breakeven,
            "risk_reward_ratio": risk_reward_ratio,
            "expiry": expiry,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as exc:
        return {**_default, "reason": f"Error computing spread signal: {exc}"}
