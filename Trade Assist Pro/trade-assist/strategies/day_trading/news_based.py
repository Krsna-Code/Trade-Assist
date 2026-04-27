import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from datetime import datetime, timezone

_INVENTORY_SCORE_MAP = {
    "STRONG_BULLISH": 95,
    "BULLISH": 75,
    "NEUTRAL": 50,
    "BEARISH": 25,
    "STRONG_BEARISH": 5,
}


def news_signal(sentiment_score: float, inventory_signal: str, ticker: str = "") -> dict:
    _default = {
        "strategy": "news_based",
        "ticker": ticker,
        "signal": "HOLD",
        "score": 50,
        "entry": None,
        "stop_loss": None,
        "target": None,
        "reason": "Insufficient or conflicting news/inventory signals.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        inv = inventory_signal.upper().strip() if isinstance(inventory_signal, str) else "NEUTRAL"
        inv_score = _INVENTORY_SCORE_MAP.get(inv, 50)
        composite_score = round(sentiment_score * 0.5 + inv_score * 0.5, 2)

        if inv == "STRONG_BULLISH" and sentiment_score > 65:
            signal = "STRONG_BUY"
            reason = (
                f"Strong bullish inventory signal combined with high sentiment "
                f"score ({sentiment_score:.1f}) supports aggressive long entry."
            )
        elif inv == "BULLISH" and sentiment_score > 55:
            signal = "BUY"
            reason = (
                f"Bullish inventory signal and positive sentiment "
                f"({sentiment_score:.1f}) favour a long position."
            )
        elif inv == "STRONG_BEARISH" and sentiment_score < 35:
            signal = "STRONG_SELL"
            reason = (
                f"Strong bearish inventory signal combined with low sentiment "
                f"({sentiment_score:.1f}) supports aggressive short entry."
            )
        elif inv == "BEARISH" and sentiment_score < 45:
            signal = "SELL"
            reason = (
                f"Bearish inventory signal and negative sentiment "
                f"({sentiment_score:.1f}) favour a short position."
            )
        else:
            return {
                **_default,
                "score": composite_score,
                "reason": (
                    f"No strong directional confluence: inventory={inv}, "
                    f"sentiment={sentiment_score:.1f}, composite={composite_score}."
                ),
            }

        return {
            "strategy": "news_based",
            "ticker": ticker,
            "signal": signal,
            "score": composite_score,
            "entry": None,
            "stop_loss": None,
            "target": None,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as exc:
        return {**_default, "reason": f"Error computing news signal: {exc}"}
