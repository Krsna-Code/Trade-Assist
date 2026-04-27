import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from data.scrapers.eia_scraper import get_latest_inventory
from config import INVENTORY_THRESHOLDS

_SCORE_MAP = {
    "STRONG_BULLISH": 95,
    "BULLISH": 75,
    "NEUTRAL": 50,
    "BEARISH": 25,
    "STRONG_BEARISH": 5,
}


def _classify_change(wow_fraction: float) -> str:
    if wow_fraction <= INVENTORY_THRESHOLDS["strong_bullish"]:
        return "STRONG_BULLISH"
    if wow_fraction <= INVENTORY_THRESHOLDS["bullish"]:
        return "BULLISH"
    if wow_fraction < INVENTORY_THRESHOLDS["bearish"]:
        return "NEUTRAL"
    if wow_fraction < INVENTORY_THRESHOLDS["strong_bearish"]:
        return "BEARISH"
    return "STRONG_BEARISH"


def compute_inventory_signal() -> dict:
    data = get_latest_inventory()

    wow_change_pct = data["wow_change_pct"]
    wow_fraction = wow_change_pct / 100.0

    signal = _classify_change(wow_fraction)
    score = _SCORE_MAP[signal]

    return {
        "signal": signal,
        "score": score,
        "wow_change_pct": wow_change_pct,
        "crude_stocks_mb": data["crude_stocks_mb"],
        "report_date": data["report_date"],
        "source": "EIA",
    }
