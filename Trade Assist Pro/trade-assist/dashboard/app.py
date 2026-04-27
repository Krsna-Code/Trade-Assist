import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from datetime import datetime, timezone

st.set_page_config(
    page_title="Trade Assist Pro",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Sidebar ---
with st.sidebar:
    st.title("🛢️ Trade Assist Pro")
    st.caption("AI-powered energy & crypto trading signals")
    st.divider()

    last_updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    st.info(f"Last updated: {last_updated}")

    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.success("Cache cleared — data will reload.")

    st.divider()
    st.caption("Navigate using the pages above.")

# --- Main area ---
st.title("Welcome to Trade Assist Pro")
st.markdown(
    "Use the sidebar pages to explore markets, signals, backtests, and options analysis. "
    "Data refreshes every 5 minutes automatically, or click **Refresh Data** to force an update."
)

st.divider()

# Summary metrics row
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Markets Page", value="📊", delta="Live quotes & charts")
with col2:
    st.metric(label="Signals Page", value="🎯", delta="AI trade signals")
with col3:
    st.metric(label="Backtest Page", value="📈", delta="Strategy performance")
with col4:
    st.metric(label="Options Page", value="⚙️", delta="Payoff diagrams")

st.divider()

# Page descriptions
st.info(
    "**📊 Markets** — Real-time stock and crypto quotes, candlestick charts, "
    "volume analysis, and market-hours status."
)
st.info(
    "**🎯 Signals** — Composite AI trade signals combining technical, sentiment, "
    "and inventory data into a single actionable recommendation."
)
st.info(
    "**📈 Backtest** — Historical strategy back-testing with equity curve, "
    "drawdown analysis, and key performance statistics."
)
st.info(
    "**⚙️ Options** — Interactive options payoff diagrams for calls, puts, "
    "covered calls, straddles, and bull/bear spreads."
)
