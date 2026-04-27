"""News feed scraper via NewsAPI (no fragile HTML scraping)."""
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
from config import NEWS_API_KEY

NEWSAPI_BASE = "https://newsapi.org/v2/everything"

OIL_KEYWORDS = "crude oil OR WTI OR Brent OR EIA inventory OR OPEC OR energy stocks"
MARKET_KEYWORDS = "S&P 500 OR stock market OR Federal Reserve OR interest rates"


def _fetch_articles(query: str, days_back: int = 2, page_size: int = 20) -> list[dict]:
    if not NEWS_API_KEY:
        print("[news_scraper] NEWS_API_KEY not set — returning empty list")
        return []

    from_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%SZ")
    params = {
        "q":        query,
        "from":     from_date,
        "sortBy":   "publishedAt",
        "pageSize": page_size,
        "language": "en",
        "apiKey":   NEWS_API_KEY,
    }
    resp = requests.get(NEWSAPI_BASE, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json().get("articles", [])


def fetch_oil_news(days_back: int = 2) -> pd.DataFrame:
    articles = _fetch_articles(OIL_KEYWORDS, days_back=days_back)
    return _to_dataframe(articles)


def fetch_market_news(days_back: int = 1) -> pd.DataFrame:
    articles = _fetch_articles(MARKET_KEYWORDS, days_back=days_back)
    return _to_dataframe(articles)


def _to_dataframe(articles: list[dict]) -> pd.DataFrame:
    rows = []
    for a in articles:
        rows.append({
            "published_at": pd.to_datetime(a.get("publishedAt")),
            "source":       a.get("source", {}).get("name", ""),
            "title":        a.get("title", ""),
            "description":  a.get("description", ""),
            "url":          a.get("url", ""),
        })
    if not rows:
        return pd.DataFrame(columns=["published_at", "source", "title", "description", "url"])
    return pd.DataFrame(rows).sort_values("published_at", ascending=False).reset_index(drop=True)


def get_headlines(topic: str = "oil", n: int = 10) -> list[str]:
    df = fetch_oil_news() if topic == "oil" else fetch_market_news()
    return df["title"].head(n).tolist()


if __name__ == "__main__":
    print(fetch_oil_news().head())
