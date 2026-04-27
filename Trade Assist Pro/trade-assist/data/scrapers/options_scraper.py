"""Options chain scraper with Greeks via yfinance."""
import yfinance as yf
import pandas as pd
from typing import Optional
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
from config import OPTIONS_DELTA_MIN, OPTIONS_DELTA_MAX, OPTIONS_MAX_THETA_PCT


def get_expiry_dates(ticker: str) -> list[str]:
    return list(yf.Ticker(ticker).options)


def fetch_chain(ticker: str, expiry: Optional[str] = None) -> dict:
    """Return calls and puts DataFrames for the nearest (or specified) expiry.

    Each row includes: strike, lastPrice, bid, ask, volume, openInterest,
    impliedVolatility, delta, gamma, theta, vega (where available).
    """
    t = yf.Ticker(ticker)
    expiries = t.options
    if not expiries:
        raise ValueError(f"No options available for {ticker}")

    target = expiry if expiry else expiries[0]
    chain  = t.option_chain(target)

    calls = chain.calls.copy()
    puts  = chain.puts.copy()

    for df in (calls, puts):
        df["expiry"]     = target
        df["ticker"]     = ticker
        df["mid_price"]  = (df["bid"] + df["ask"]) / 2
        df["spot_price"] = t.fast_info.last_price

    return {"calls": calls, "puts": puts, "expiry": target, "ticker": ticker}


def get_filtered_options(ticker: str, expiry: Optional[str] = None) -> dict:
    """Return only options that pass the delta and theta filters from config."""
    chain = fetch_chain(ticker, expiry)
    spot  = chain["calls"]["spot_price"].iloc[0]

    def _filter(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        if "delta" not in df.columns:
            return df
        delta_abs = df["delta"].abs()
        df = df[(delta_abs >= OPTIONS_DELTA_MIN) & (delta_abs <= OPTIONS_DELTA_MAX)]
        if "theta" in df.columns and "lastPrice" in df.columns:
            df = df[df["lastPrice"] > 0]
            df["theta_pct"] = df["theta"].abs() / df["lastPrice"]
            df = df[df["theta_pct"] <= OPTIONS_MAX_THETA_PCT]
        return df

    return {
        "calls":  _filter(chain["calls"]),
        "puts":   _filter(chain["puts"]),
        "expiry": chain["expiry"],
        "ticker": ticker,
        "spot":   spot,
    }


def get_iv_rank(ticker: str, lookback_days: int = 252) -> float:
    """Estimate IV rank: where current IV sits relative to its 1-year range (0–100)."""
    t     = yf.Ticker(ticker)
    hist  = t.history(period="1y")
    if hist.empty:
        return 50.0
    hist["returns"]    = hist["Close"].pct_change()
    hist["hist_vol"]   = hist["returns"].rolling(20).std() * (252 ** 0.5)
    current_iv = hist["hist_vol"].iloc[-1]
    iv_min     = hist["hist_vol"].min()
    iv_max     = hist["hist_vol"].max()
    if iv_max == iv_min:
        return 50.0
    return round((current_iv - iv_min) / (iv_max - iv_min) * 100, 2)


if __name__ == "__main__":
    chain = fetch_chain("XOM")
    print(chain["calls"][["strike", "lastPrice", "impliedVolatility", "delta", "theta"]].head())
