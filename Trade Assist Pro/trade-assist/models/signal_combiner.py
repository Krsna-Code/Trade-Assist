import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import SIGNAL_WEIGHTS, SCORE_THRESHOLDS
from datetime import datetime, timezone


def combine_signals(
    inventory_signal: dict,
    technical_signal: dict,
    mirofish_signal: dict,
    sentiment_signal: dict,
    ml_signal: dict,
    ticker: str = "",
) -> dict:
    inventory_score  = float(inventory_signal.get("score",  50))
    technical_score  = float(technical_signal.get("score",  50))
    mirofish_score   = float(mirofish_signal.get("score",   50))
    sentiment_score  = float(sentiment_signal.get("score",  50))
    ml_score         = float(ml_signal.get("score",         50))

    weights = SIGNAL_WEIGHTS if isinstance(SIGNAL_WEIGHTS, dict) else {}
    w_inv  = weights.get("inventory",  0.30)
    w_tech = weights.get("technical",  0.25)
    w_miro = weights.get("mirofish",   0.25)
    w_sent = weights.get("sentiment",  0.10)
    w_ml   = weights.get("ml",         0.10)

    composite = (
        inventory_score  * w_inv  +
        technical_score  * w_tech +
        mirofish_score   * w_miro +
        sentiment_score  * w_sent +
        ml_score         * w_ml
    )
    composite = round(composite, 4)

    thresholds = SCORE_THRESHOLDS if isinstance(SCORE_THRESHOLDS, dict) else {}
    strong_buy  = thresholds.get("strong_buy",  75)
    buy         = thresholds.get("buy",         60)
    hold        = thresholds.get("hold",        40)
    sell        = thresholds.get("sell",        25)

    if composite > strong_buy:
        recommendation = "STRONG BUY"
        nearest_boundary = strong_buy
    elif composite > buy:
        recommendation = "BUY"
        nearest_boundary = buy
    elif composite > hold:
        recommendation = "HOLD"
        nearest_boundary = hold
    elif composite > sell:
        recommendation = "SELL"
        nearest_boundary = sell
    else:
        recommendation = "STRONG SELL"
        nearest_boundary = sell

    confidence = round(abs(composite - nearest_boundary), 4)

    weighted_contributions = {
        "inventory":  inventory_score  * w_inv,
        "technical":  technical_score  * w_tech,
        "mirofish":   mirofish_score   * w_miro,
        "sentiment":  sentiment_score  * w_sent,
        "ml":         ml_score         * w_ml,
    }
    dominant_signal = max(weighted_contributions, key=weighted_contributions.get)

    return {
        "ticker": ticker,
        "composite_score": composite,
        "recommendation": recommendation,
        "confidence": confidence,
        "breakdown": {
            "inventory_score":  inventory_score,
            "technical_score":  technical_score,
            "mirofish_score":   mirofish_score,
            "sentiment_score":  sentiment_score,
            "ml_score":         ml_score,
        },
        "dominant_signal": dominant_signal,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
