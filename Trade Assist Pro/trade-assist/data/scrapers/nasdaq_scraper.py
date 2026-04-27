"""Stock price data via yfinance (replaces fragile NASDAQ scraping)."""
import yfinance as yf
import pandas as pd
from datetime import datetime, timezone
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
from config import TICKERS


def fetch_ohlcv(ticker: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    """Return OHLCV DataFrame for a single ticker."""
    t = yf.Ticker(ticker)
    df = t.history(period=period, interval=interval, auto_adjust=True)
    if df.empty:
        raise ValueError(f"No data returned for {ticker}")
    df.index = pd.to_datetime(df.index)
    df.index.name = "timestamp"
    return df[["Open", "High", "Low", "Close", "Volume"]].rename(
        columns=str.lower
    )


def fetch_all_tickers(period: str = "6mo") -> dict[str, pd.DataFrame]:
    """Fetch OHLCV for every configured ticker. Returns {ticker: DataFrame}."""
    all_tickers = [t for group in TICKERS.values() for t in group]
    result = {}
    for ticker in all_tickers:
        try:
            result[ticker] = fetch_ohlcv(ticker, period=period)
        except Exception as e:
            print(f"[nasdaq_scraper] {ticker} failed: {e}")
    return result


def fetch_quote(ticker: str) -> dict:
    """Return the latest price snapshot for a ticker."""
    t = yf.Ticker(ticker)
    info = t.fast_info
    return {
        "ticker":        ticker,
        "price":         round(info.last_price, 4),
        "prev_close":    round(info.previous_close, 4),
        "change_pct":    round((info.last_price - info.previous_close) / info.previous_close * 100, 3),
        "volume":        int(info.last_volume),
        "market_cap":    getattr(info, "market_cap", None),
        "fetched_at":    datetime.now(timezone.utc).isoformat(),
    }


def fetch_all_quotes() -> list[dict]:
    all_tickers = [t for group in TICKERS.values() for t in group]
    quotes = []
    for ticker in all_tickers:
        try:
            quotes.append(fetch_quote(ticker))
        except Exception as e:
            print(f"[nasdaq_scraper] quote {ticker} failed: {e}")
    return quotes


if __name__ == "__main__":
    for q in fetch_all_quotes():
        print(q)
