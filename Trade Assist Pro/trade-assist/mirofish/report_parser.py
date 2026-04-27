import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from datetime import datetime, timezone

_BEHAVIOR_MAP = {
    "STRONGLY_BULLISH": ("STRONG_BULLISH", 92),
    "STRONG_BUY":       ("STRONG_BULLISH", 92),
    "BULLISH":          ("BULLISH",        72),
    "BUY":              ("BULLISH",        72),
    "NEUTRAL":          ("NEUTRAL",        50),
    "HOLD":             ("NEUTRAL",        50),
    "BEARISH":          ("BEARISH",        28),
    "SELL":             ("BEARISH",        28),
    "STRONGLY_BEARISH": ("STRONG_BEARISH",  8),
    "STRONG_SELL":      ("STRONG_BEARISH",  8),
}


def parse_report(report: dict) -> dict:
    dominant_behavior = report.get("dominant_behavior", "NEUTRAL")
    confidence = float(report.get("confidence", 0.5))
    bullish_agents = int(report.get("bullish_agents", 0))
    bearish_agents = int(report.get("bearish_agents", 0))
    neutral_agents = int(report.get("neutral_agents", 0))
    summary = report.get("summary", "")

    signal, base_score = _BEHAVIOR_MAP.get(
        dominant_behavior.upper(), ("NEUTRAL", 50)
    )

    final_score = round(base_score * confidence + 50 * (1 - confidence), 2)

    total_agents = bullish_agents + bearish_agents + neutral_agents
    if total_agents > 0:
        bullish_pct = round(bullish_agents / total_agents * 100, 1)
        bearish_pct = round(bearish_agents / total_agents * 100, 1)
        neutral_pct = round(neutral_agents / total_agents * 100, 1)
    else:
        bullish_pct = bearish_pct = neutral_pct = 0.0

    return {
        "signal": signal,
        "score": final_score,
        "confidence": confidence,
        "dominant_behavior": dominant_behavior,
        "bullish_pct": bullish_pct,
        "bearish_pct": bearish_pct,
        "neutral_pct": neutral_pct,
        "summary": summary,
        "source": "mirofish",
        "is_fallback": report.get("status") == "fallback",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
