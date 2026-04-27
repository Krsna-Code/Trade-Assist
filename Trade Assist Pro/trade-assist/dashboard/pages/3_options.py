import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import streamlit as st
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Import scrapers
# ---------------------------------------------------------------------------
try:
    from data.scrapers.nasdaq_scraper import fetch_ohlcv
except Exception as _e:
    st.error(f"Failed to import nasdaq_scraper: {_e}")
    fetch_ohlcv = None

try:
    from data.scrapers.options_scraper import fetch_chain, get_iv_rank
except Exception as _e:
    st.error(f"Failed to import options_scraper: {_e}")
    fetch_chain = None
    get_iv_rank = None

# ---------------------------------------------------------------------------
# Import strategies
# ---------------------------------------------------------------------------
try:
    from strategies.options.calls_puts import calls_puts_signal
except Exception as _e:
    st.error(f"Failed to import calls_puts strategy: {_e}")
    calls_puts_signal = None

try:
    from strategies.options.covered_calls import covered_call_signal
except Exception as _e:
    st.error(f"Failed to import covered_calls strategy: {_e}")
    covered_call_signal = None

try:
    from strategies.options.straddles import straddle_signal
except Exception as _e:
    st.error(f"Failed to import straddles strategy: {_e}")
    straddle_signal = None

try:
    from strategies.options.spreads import spread_signal
except Exception as _e:
    st.error(f"Failed to import spreads strategy: {_e}")
    spread_signal = None

# ---------------------------------------------------------------------------
# Import payoff chart builders
# ---------------------------------------------------------------------------
try:
    from dashboard.components.options_payoff import (
        long_call_payoff,
        long_put_payoff,
        covered_call_payoff,
        straddle_payoff,
        bull_call_spread_payoff,
    )
except Exception as _e:
    st.error(f"Failed to import options_payoff component: {_e}")
    long_call_payoff = None
    long_put_payoff = None
    covered_call_payoff = None
    straddle_payoff = None
    bull_call_spread_payoff = None

# ---------------------------------------------------------------------------
# Cached fetchers
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300)
def cached_ohlcv(ticker: str):
    if fetch_ohlcv is None:
        return None
    try:
        return fetch_ohlcv(ticker, "1d")
    except Exception as exc:
        st.error(f"Error fetching OHLCV for {ticker}: {exc}")
        return None


@st.cache_data(ttl=300)
def cached_chain(ticker: str, expiry: str):
    if fetch_chain is None:
        return None
    try:
        return fetch_chain(ticker, expiry)
    except Exception as exc:
        st.error(f"Error fetching options chain for {ticker}: {exc}")
        return None


@st.cache_data(ttl=300)
def cached_iv_rank(ticker: str):
    if get_iv_rank is None:
        return None
    try:
        return get_iv_rank(ticker)
    except Exception as exc:
        st.error(f"Error fetching IV rank for {ticker}: {exc}")
        return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iv_rank_colour(iv_rank: float) -> str:
    if iv_rank < 30:
        return "green"
    if iv_rank <= 60:
        return "orange"
    return "red"


def _iv_rank_text(iv_rank: float) -> str:
    if iv_rank < 30:
        return "Low IV — options are cheap. Favour buying strategies (debit spreads, long calls/puts, straddles)."
    if iv_rank <= 60:
        return "Moderate IV — balanced environment. Directional plays with defined risk are reasonable."
    return "High IV — options are expensive. Favour selling strategies (covered calls, credit spreads, iron condors)."


def _apply_dark(fig):
    if fig is not None:
        fig.update_layout(template="plotly_dark")
    return fig


def _safe_chart(fn, *args):
    if fn is None:
        return None
    try:
        return _apply_dark(fn(*args))
    except Exception as exc:
        st.error(f"Chart error: {exc}")
        return None


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Options Strategies", page_icon="🎯", layout="wide")
st.title("🎯 Options Strategies")

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

OIL_AND_BROAD = ["XOM", "CVX", "OXY", "USO", "COP", "PSX", "SPY", "QQQ", "IWM"]
EXPIRY_MAP = {"Nearest": "nearest", "2 weeks": "2w", "Monthly": "monthly"}

with st.sidebar:
    st.header("Controls")
    ticker = st.selectbox("Ticker", options=OIL_AND_BROAD, index=0)
    expiry_label = st.radio("Expiry", options=list(EXPIRY_MAP.keys()), index=0)

expiry = EXPIRY_MAP[expiry_label]

# ---------------------------------------------------------------------------
# Fetch data
# ---------------------------------------------------------------------------

with st.spinner(f"Loading data for {ticker}…"):
    df = cached_ohlcv(ticker)
    chain = cached_chain(ticker, expiry)
    iv_rank_raw = cached_iv_rank(ticker)

iv_rank = float(iv_rank_raw) if iv_rank_raw is not None else 0.0

# ---------------------------------------------------------------------------
# IV Rank banner
# ---------------------------------------------------------------------------

colour = _iv_rank_colour(iv_rank)
interp = _iv_rank_text(iv_rank)

iv_col, info_col = st.columns([1, 3])
with iv_col:
    st.markdown(
        f"<h2 style='color:{colour}'>IV Rank: {iv_rank:.0f}</h2>",
        unsafe_allow_html=True,
    )
with info_col:
    st.markdown(f"**{interp}**")
    st.caption(f"Data as of {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

st.divider()

# ---------------------------------------------------------------------------
# Strategy tabs
# ---------------------------------------------------------------------------

tab_cp, tab_cc, tab_st, tab_sp = st.tabs(
    ["Calls & Puts", "Covered Calls", "Straddles", "Spreads"]
)

# --- Tab 1: Calls & Puts ---
with tab_cp:
    st.subheader("Calls & Puts")
    sig = {}
    if calls_puts_signal is not None and df is not None and chain is not None:
        try:
            sig = calls_puts_signal(df, chain, ticker) or {}
        except Exception as exc:
            st.error(f"Calls & Puts signal error: {exc}")

    if sig:
        direction = str(sig.get("direction", "CALL")).upper()
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Direction", direction)
        c2.metric("Strike", sig.get("strike", "—"))
        c3.metric("Expiry", sig.get("expiry", "—"))
        c4.metric("Delta", f"{sig.get('delta', '—')}")
        c5.metric("Premium", f"${sig.get('premium', '—')}")

        if direction == "CALL":
            fig = _safe_chart(long_call_payoff, sig.get("strike"), sig.get("premium"))
        else:
            fig = _safe_chart(long_put_payoff, sig.get("strike"), sig.get("premium"))

        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No Calls & Puts signal available. Ensure price and chain data loaded correctly.")

# --- Tab 2: Covered Calls ---
with tab_cc:
    st.subheader("Covered Calls")
    sig_cc = {}
    if covered_call_signal is not None and df is not None and chain is not None:
        try:
            sig_cc = covered_call_signal(df, chain, ticker) or {}
        except Exception as exc:
            st.error(f"Covered Call signal error: {exc}")

    if sig_cc:
        c1, c2, c3 = st.columns(3)
        c1.metric("Strike", sig_cc.get("strike", "—"))
        c2.metric("Premium", f"${sig_cc.get('premium', '—')}")
        ann_yield = sig_cc.get("annualised_yield")
        c3.metric(
            "Annualised Yield",
            f"{float(ann_yield)*100:.1f}%" if ann_yield is not None else "—",
        )

        fig_cc = _safe_chart(
            covered_call_payoff,
            sig_cc.get("strike"),
            sig_cc.get("premium"),
        )
        if fig_cc is not None:
            st.plotly_chart(fig_cc, use_container_width=True)
    else:
        st.info("No Covered Call signal available.")

# --- Tab 3: Straddles ---
with tab_st:
    st.subheader("Straddles")

    if iv_rank > 50:
        st.warning(
            f"IV Rank is {iv_rank:.0f} (> 50) — buying volatility is expensive. "
            "Consider selling a straddle instead."
        )

    sig_straddle = {}
    if straddle_signal is not None and df is not None and chain is not None:
        try:
            sig_straddle = straddle_signal(df, chain, iv_rank, ticker) or {}
        except Exception as exc:
            st.error(f"Straddle signal error: {exc}")

    if sig_straddle:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Cost", f"${sig_straddle.get('total_cost', '—')}")
        req_move = sig_straddle.get("required_move_pct")
        c2.metric(
            "Required Move",
            f"{float(req_move)*100:.1f}%" if req_move is not None else "—",
        )
        be = sig_straddle.get("breakevens", ("—", "—"))
        c3.metric("Breakevens", f"{be[0]} / {be[1]}" if isinstance(be, (list, tuple)) else str(be))

        fig_st = _safe_chart(
            straddle_payoff,
            sig_straddle.get("strike"),
            sig_straddle.get("total_cost"),
        )
        if fig_st is not None:
            st.plotly_chart(fig_st, use_container_width=True)
    else:
        st.info("No Straddle signal available.")

# --- Tab 4: Spreads ---
with tab_sp:
    st.subheader("Spreads")
    spread_dir = st.radio(
        "Direction", options=["bull", "bear"], horizontal=True, key="spread_dir"
    )

    sig_spread = {}
    if spread_signal is not None and df is not None and chain is not None:
        try:
            sig_spread = spread_signal(df, chain, spread_dir, ticker) or {}
        except Exception as exc:
            st.error(f"Spread signal error: {exc}")

    if sig_spread:
        cols = st.columns(len(sig_spread))
        for col, (k, v) in zip(cols, sig_spread.items()):
            col.metric(k.replace("_", " ").title(), str(v))

        fig_sp = _safe_chart(
            bull_call_spread_payoff,
            sig_spread.get("long_strike"),
            sig_spread.get("short_strike"),
            sig_spread.get("net_debit"),
        )
        if fig_sp is not None:
            st.plotly_chart(fig_sp, use_container_width=True)
    else:
        st.info("No Spread signal available.")

# ---------------------------------------------------------------------------
# Raw options chain table (calls side)
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Raw Options Chain — Calls")

CHAIN_COLS = ["strike", "bid", "ask", "volume", "openInterest", "impliedVolatility", "delta", "theta"]

if chain is not None:
    calls_df = None
    # chain may be a dict with 'calls' key, or a DataFrame directly
    if hasattr(chain, "columns"):
        calls_df = chain
    elif isinstance(chain, dict) and "calls" in chain:
        calls_df = chain["calls"]

    if calls_df is not None and hasattr(calls_df, "empty") and not calls_df.empty:
        display_cols = [c for c in CHAIN_COLS if c in calls_df.columns]
        st.dataframe(
            calls_df[display_cols].reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No calls data to display.")
else:
    st.info("Options chain not loaded.")
