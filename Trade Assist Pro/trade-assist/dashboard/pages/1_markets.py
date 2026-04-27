import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from data.scrapers.nasdaq_scraper import fetch_all_quotes
from data.scrapers.crypto_scraper import fetch_all_quotes as fetch_crypto_quotes
from dashboard.components.charts import candlestick_chart
from data.scrapers.nasdaq_scraper import fetch_ohlcv
import pandas as pd
from datetime import datetime, timezone

st.set_page_config(page_title="Markets Overview", page_icon="📊", layout="wide")
st.title("📊 Markets Overview")

# --- Market status ---
def _market_status() -> tuple:
    now_utc = datetime.now(timezone.utc)
    weekday = now_utc.weekday()
    hour = now_utc.hour
    minute = now_utc.minute
    total_minutes = hour * 60 + minute
    is_weekday = weekday < 5
    # NYSE: 14:30–21:00 UTC
    is_open = is_weekday and 870 <= total_minutes < 1260
    return is_open, now_utc

is_open, now_utc = _market_status()
status_col, time_col = st.columns([1, 3])
with status_col:
    if is_open:
        st.success("Market Open")
    else:
        st.error("Market Closed")
with time_col:
    st.caption(f"Current UTC time: {now_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC")

st.divider()


# --- Cached data loaders ---
@st.cache_data(ttl=300)
def load_stock_quotes():
    return fetch_all_quotes()


@st.cache_data(ttl=300)
def load_crypto_quotes():
    return fetch_crypto_quotes()


@st.cache_data(ttl=300)
def load_ohlcv(ticker: str):
    return fetch_ohlcv(ticker)


# --- Stock quotes ---
st.subheader("Equities")
try:
    stock_data = load_stock_quotes()
    if stock_data:
        df_stocks = pd.DataFrame(stock_data)
        num_cols = min(4, len(df_stocks))
        cols = st.columns(num_cols)
        for idx, row in df_stocks.iterrows():
            col = cols[idx % num_cols]
            change_pct = row.get("change_pct", 0.0)
            delta_color = "normal"
            with col:
                st.metric(
                    label=row.get("ticker", "—"),
                    value=f"${row.get('price', 0.0):.2f}",
                    delta=f"{change_pct:+.2f}%",
                    delta_color=delta_color,
                )
                volume = row.get("volume", None)
                if volume is not None:
                    st.caption(f"Vol: {int(volume):,}")
    else:
        st.info("No stock quote data available.")
except Exception as e:
    st.error(f"Failed to load stock quotes: {e}")

st.divider()

# --- Crypto quotes ---
st.subheader("Crypto")
try:
    crypto_data = load_crypto_quotes()
    if crypto_data:
        df_crypto = pd.DataFrame(crypto_data)
        num_cols = min(4, len(df_crypto))
        cols = st.columns(num_cols)
        for idx, row in df_crypto.iterrows():
            col = cols[idx % num_cols]
            change_pct = row.get("change_pct", 0.0)
            with col:
                st.metric(
                    label=row.get("ticker", row.get("symbol", "—")),
                    value=f"${row.get('price', 0.0):,.2f}",
                    delta=f"{change_pct:+.2f}%",
                )
    else:
        st.info("No crypto quote data available.")
except Exception as e:
    st.error(f"Failed to load crypto quotes: {e}")

st.divider()

# --- Candlestick chart ---
st.subheader("Price Chart")
try:
    stock_data_for_select = load_stock_quotes()
    tickers = [q.get("ticker") for q in stock_data_for_select if q.get("ticker")] if stock_data_for_select else []
    if not tickers:
        tickers = ["XOM", "CVX", "CL=F", "BTC-USD"]

    selected_ticker = st.selectbox("Select Ticker", tickers)

    if selected_ticker:
        ohlcv = load_ohlcv(selected_ticker)
        if ohlcv is not None and not ohlcv.empty:
            fig = candlestick_chart(ohlcv, selected_ticker, show_volume=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"No OHLCV data available for {selected_ticker}.")
except Exception as e:
    st.error(f"Failed to render chart: {e}")
