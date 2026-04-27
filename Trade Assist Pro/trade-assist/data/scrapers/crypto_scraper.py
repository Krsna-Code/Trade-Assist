"""Crypto price data via CCXT (Binance public endpoint, no API key needed)."""
import ccxt
import pandas as pd
from datetime import datetime, timezone
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
from config import CRYPTO_PAIRS

_exchange = ccxt.binance({"enableRateLimit": True})


def fetch_ohlcv(pair: str, timeframe: str = "1d", limit: int = 180) -> pd.DataFrame:
    """Return OHLCV DataFrame for a crypto pair."""
    raw = _exchange.fetch_ohlcv(pair, timeframe=timeframe, limit=limit)
    df  = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df.set_index("timestamp", inplace=True)
    return df


def fetch_ticker(pair: str) -> dict:
    """Return latest quote for a crypto pair."""
    t = _exchange.fetch_ticker(pair)
    return {
        "pair":       pair,
        "price":      t["last"],
        "change_pct": round(t["percentage"] or 0, 3),
        "volume_24h": t["quoteVolume"],
        "high_24h":   t["high"],
        "low_24h":    t["low"],
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def fetch_all_quotes() -> list[dict]:
    quotes = []
    for pair in CRYPTO_PAIRS:
        try:
            quotes.append(fetch_ticker(pair))
        except Exception as e:
            print(f"[crypto_scraper] {pair} failed: {e}")
    return quotes


def fetch_all_ohlcv(timeframe: str = "1d", limit: int = 180) -> dict[str, pd.DataFrame]:
    result = {}
    for pair in CRYPTO_PAIRS:
        try:
            result[pair] = fetch_ohlcv(pair, timeframe=timeframe, limit=limit)
        except Exception as e:
            print(f"[crypto_scraper] OHLCV {pair} failed: {e}")
    return result


if __name__ == "__main__":
    for q in fetch_all_quotes():
        print(q)
