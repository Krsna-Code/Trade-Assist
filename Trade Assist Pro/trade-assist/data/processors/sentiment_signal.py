import os
import re
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from data.scrapers.news_scraper import fetch_oil_news, fetch_market_news

BULLISH_WORDS = [
    "surge", "rally", "gain", "rise", "bull", "strong", "beat", "exceed",
    "draw", "shortage", "supply cut", "opec cut", "demand",
]

BEARISH_WORDS = [
    "fall", "drop", "crash", "bear", "weak", "miss", "build", "glut",
    "oversupply", "recession", "slowdown", "rate hike",
]

_SIGNAL_THRESHOLDS = [
    (75, "STRONG_BULLISH"),
    (60, "BULLISH"),
    (40, "NEUTRAL"),
    (25, "BEARISH"),
]


def _score_to_signal(score: float) -> str:
    for threshold, label in _SIGNAL_THRESHOLDS:
        if score > threshold:
            return label
    return "STRONG_BEARISH"


def score_headline(text: str) -> float:
    lower = text.lower()
    bullish_hits = sum(1 for w in BULLISH_WORDS if re.search(r"\b" + re.escape(w) + r"\b", lower))
    bearish_hits = sum(1 for w in BEARISH_WORDS if re.search(r"\b" + re.escape(w) + r"\b", lower))
    total = bullish_hits + bearish_hits
    if total == 0:
        return 0.0
    return (bullish_hits - bearish_hits) / total


def compute_sentiment_signal(days_back: int = 2) -> dict:
    oil_df = fetch_oil_news(days_back=days_back)
    market_df = fetch_market_news(days_back=days_back)
    combined = pd.concat([oil_df, market_df], ignore_index=True)
    all_articles = combined.to_dict("records")

    if not all_articles:
        return {
            "signal": "NEUTRAL",
            "score": 50.0,
            "mean_sentiment": 0.0,
            "num_articles": 0,
            "top_headlines": [],
        }

    headlines = [a.get("headline", a.get("title", "")) for a in all_articles]
    headlines = [h for h in headlines if h]

    scores = [score_headline(h) for h in headlines]
    mean_sentiment = sum(scores) / len(scores)

    scaled_score = round(mean_sentiment * 50 + 50, 2)
    signal = _score_to_signal(scaled_score)

    scored_pairs = sorted(zip(scores, headlines), key=lambda x: abs(x[0]), reverse=True)
    top_headlines = [h for _, h in scored_pairs[:5]]

    return {
        "signal": signal,
        "score": scaled_score,
        "mean_sentiment": round(mean_sentiment, 4),
        "num_articles": len(headlines),
        "top_headlines": top_headlines,
    }
