"""EIA Weekly Petroleum Status Report — crude oil inventory scraper."""
import requests
import pandas as pd

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
from config import EIA_API_KEY, EIA_SERIES

EIA_BASE = "https://api.eia.gov/v2/seriesid/{series_id}"


def fetch_crude_inventory(num_weeks: int = 10) -> pd.DataFrame:
    """Return a DataFrame of weekly crude oil stock data from EIA.

    Columns: report_date, crude_stocks_mb, wow_change_mb, wow_change_pct
    """
    series_id = EIA_SERIES["crude_stocks"]
    url = EIA_BASE.format(series_id=series_id)
    params = {
        "api_key": EIA_API_KEY,
        "data[]": "value",
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": num_weeks + 1,
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    payload = resp.json()

    rows = payload.get("response", {}).get("data", [])
    if not rows:
        raise ValueError("EIA returned empty data — check API key or series ID.")

    df = pd.DataFrame(rows)
    df["report_date"]     = pd.to_datetime(df["period"])
    df["crude_stocks_mb"] = pd.to_numeric(df["value"], errors="coerce")
    df = df[["report_date", "crude_stocks_mb"]].sort_values("report_date").reset_index(drop=True)

    df["wow_change_mb"]  = df["crude_stocks_mb"].diff()
    df["wow_change_pct"] = df["wow_change_mb"] / df["crude_stocks_mb"].shift(1)

    return df.dropna().tail(num_weeks).reset_index(drop=True)


def get_latest_inventory() -> dict:
    """Return the most recent EIA inventory reading as a dict."""
    df = fetch_crude_inventory(num_weeks=2)
    latest = df.iloc[-1]
    return {
        "report_date":     latest["report_date"].strftime("%Y-%m-%d"),
        "crude_stocks_mb": round(float(latest["crude_stocks_mb"]), 2),
        "wow_change_mb":   round(float(latest["wow_change_mb"]), 2),
        "wow_change_pct":  round(float(latest["wow_change_pct"]) * 100, 3),
    }


if __name__ == "__main__":
    data = get_latest_inventory()
    print(data)
