import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import streamlit as st
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Scraper / processor imports — each wrapped so a missing module shows a clear
# error rather than crashing the whole page.
# ---------------------------------------------------------------------------
try:
    from data.scrapers.nasdaq_scraper import fetch_ohlcv
except Exception as _e:
    st.error(f"Failed to import nasdaq_scraper: {_e}")
    fetch_ohlcv = None

try:
    from data.processors.sentiment_signal import compute_sentiment_signal
except Exception as _e:
    st.error(f"Failed to import sentiment_signal: {_e}")
    compute_sentiment_signal = None

try:
    from data.processors.inventory_signal import compute_inventory_signal
except Exception as _e:
    st.error(f"Failed to import inventory_signal: {_e}")
    compute_inventory_signal = None

try:
    from strategies.day_trading.momentum import momentum_signal
except Exception as _e:
    st.error(f"Failed to import momentum strategy: {_e}")
    momentum_signal = None

try:
    from strategies.day_trading.mean_reversion import mean_reversion_signal
except Exception as _e:
    st.error(f"Failed to import mean_reversion strategy: {_e}")
    mean_reversion_signal = None

try:
    from strategies.day_trading.vwap import vwap_signal
except Exception as _e:
    st.error(f"Failed to import vwap strategy: {_e}")
    vwap_signal = None

try:
    from strategies.day_trading.news_based import news_signal
except Exception as _e:
    st.error(f"Failed to import news_based strategy: {_e}")
    news_signal = None

try:
    from dashboard.components.charts import candlestick_chart
except Exception as _e:
    st.error(f"Failed to import charts component: {_e}")
    candlestick_chart = None

# ---------------------------------------------------------------------------
# Cached data fetchers
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300)
def cached_ohlcv(ticker: str, timeframe: str):
    if fetch_ohlcv is None:
        return None
    try:
        return fetch_ohlcv(ticker, timeframe)
    except Exception as exc:
        st.error(f"Error fetching OHLCV for {ticker}: {exc}")
        return None


@st.cache_data(ttl=300)
def cached_sentiment():
    if compute_sentiment_signal is None:
        return {}
    try:
        return compute_sentiment_signal()
    except Exception as exc:
        st.error(f"Error computing sentiment signal: {exc}")
        return {}


@st.cache_data(ttl=300)
def cached_inventory():
    if compute_inventory_signal is None:
        return {}
    try:
        return compute_inventory_signal()
    except Exception as exc:
        st.error(f"Error computing inventory signal: {exc}")
        return {}


# ---------------------------------------------------------------------------
# Helper: render one strategy card inside a column
# ---------------------------------------------------------------------------

def _render_strategy_card(col, title: str, sig: dict):
    with col:
        st.markdown(f"**{title}**")
        if not sig:
            st.warning("No signal data available.")
            return

        signal_label = sig.get("signal", "N/A")
        score = sig.get("score", 0.0)
        entry = sig.get("entry", "—")
        stop = sig.get("stop", "—")
        target = sig.get("target", "—")

        colour = {"BUY": "🟢", "SELL": "🔴", "NEUTRAL": "⚪"}.get(
            str(signal_label).upper(), "⚪"
        )
        st.markdown(f"{colour} Signal: **{signal_label}**")

        # Score as a native progress bar (0-1 scale)
        clamped = max(0.0, min(1.0, float(score)))
        st.progress(clamped, text=f"Score: {clamped:.2f}")

        st.markdown(
            f"Entry: `{entry}` &nbsp;|&nbsp; Stop: `{stop}` &nbsp;|&nbsp; Target: `{target}`",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Day Trading Signals", page_icon="📈", layout="wide")
st.title("📈 Day Trading Signals")

# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------

TICKERS = ["SPY", "QQQ", "XOM", "CVX", "OXY", "USO"]

with st.sidebar:
    st.header("Controls")
    selected_tickers = st.multiselect(
        "Tickers",
        options=TICKERS,
        default=["SPY"],
    )
    timeframe = st.selectbox("Timeframe", options=["1d", "1h"], index=0)

if not selected_tickers:
    st.info("Select at least one ticker in the sidebar.")
    st.stop()

# ---------------------------------------------------------------------------
# EIA Wednesday reminder
# ---------------------------------------------------------------------------

_today_utc = datetime.now(timezone.utc)
_weekday = _today_utc.weekday()  # Monday=0 … Sunday=6
if _weekday in (1, 2):  # Tuesday or Wednesday
    day_name = "Tuesday" if _weekday == 1 else "Wednesday"
    st.info(
        f"📅 Today is {day_name}. EIA Weekly Petroleum Status Report releases every Wednesday "
        "at ~10:30 AM ET. Watch for crude inventory surprises that may move energy names."
    )

# ---------------------------------------------------------------------------
# Pre-fetch shared signals (sentiment + inventory) once for all tickers
# ---------------------------------------------------------------------------

with st.spinner("Loading shared signals…"):
    sentiment = cached_sentiment()
    inventory = cached_inventory()

sentiment_score = float(sentiment.get("score", 0.0))
inventory_sig = inventory.get("signal", "neutral")

# ---------------------------------------------------------------------------
# Per-ticker sections
# ---------------------------------------------------------------------------

for ticker in selected_tickers:
    st.divider()
    st.subheader(f"Ticker: {ticker}")

    with st.spinner(f"Fetching OHLCV for {ticker}…"):
        df = cached_ohlcv(ticker, timeframe)

    if df is None or (hasattr(df, "empty") and df.empty):
        st.error(f"No price data available for {ticker}.")
        continue

    # Candlestick chart
    if candlestick_chart is not None:
        try:
            fig = candlestick_chart(df, ticker)
            if fig is not None:
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
        except Exception as exc:
            st.error(f"Chart error for {ticker}: {exc}")

    # Compute the 4 strategy signals
    with st.spinner(f"Computing signals for {ticker}…"):
        sig_momentum = {}
        sig_mean_rev = {}
        sig_vwap = {}
        sig_news = {}

        if momentum_signal is not None:
            try:
                sig_momentum = momentum_signal(df, ticker) or {}
            except Exception as exc:
                st.error(f"Momentum signal error ({ticker}): {exc}")

        if mean_reversion_signal is not None:
            try:
                sig_mean_rev = mean_reversion_signal(df, ticker) or {}
            except Exception as exc:
                st.error(f"Mean-reversion signal error ({ticker}): {exc}")

        if vwap_signal is not None:
            try:
                sig_vwap = vwap_signal(df, ticker) or {}
            except Exception as exc:
                st.error(f"VWAP signal error ({ticker}): {exc}")

        if news_signal is not None:
            try:
                sig_news = news_signal(sentiment_score, inventory_sig, ticker) or {}
            except Exception as exc:
                st.error(f"News-based signal error ({ticker}): {exc}")

    # 2×2 grid of signal cards
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)

    with st.container():
        _render_strategy_card(row1_col1, "Momentum", sig_momentum)
        _render_strategy_card(row1_col2, "Mean Reversion", sig_mean_rev)
        _render_strategy_card(row2_col1, "VWAP", sig_vwap)
        _render_strategy_card(row2_col2, "News-Based", sig_news)

    # Combined score metric — average of the 4 strategy scores
    scores = []
    for sig in (sig_momentum, sig_mean_rev, sig_vwap, sig_news):
        raw = sig.get("score")
        if raw is not None:
            try:
                scores.append(float(raw))
            except (TypeError, ValueError):
                pass

    if scores:
        combined = sum(scores) / len(scores)
        st.metric(
            label=f"Combined Score — {ticker}",
            value=f"{combined:.2f}",
            help="Simple average of the 4 strategy scores (0 = max bearish, 1 = max bullish).",
        )
    else:
        st.metric(label=f"Combined Score — {ticker}", value="N/A")
