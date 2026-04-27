import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import streamlit as st
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Scraper imports
# ---------------------------------------------------------------------------
try:
    from data.scrapers.eia_scraper import fetch_crude_inventory, get_latest_inventory
except Exception as _e:
    st.error(f"Failed to import eia_scraper: {_e}")
    fetch_crude_inventory = None
    get_latest_inventory = None

try:
    from data.scrapers.news_scraper import fetch_oil_news
except Exception as _e:
    st.error(f"Failed to import news_scraper: {_e}")
    fetch_oil_news = None

# ---------------------------------------------------------------------------
# Processor imports
# ---------------------------------------------------------------------------
try:
    from data.processors.inventory_signal import compute_inventory_signal
except Exception as _e:
    st.error(f"Failed to import inventory_signal: {_e}")
    compute_inventory_signal = None

try:
    from data.processors.sentiment_signal import compute_sentiment_signal
except Exception as _e:
    st.error(f"Failed to import sentiment_signal: {_e}")
    compute_sentiment_signal = None

# ---------------------------------------------------------------------------
# MiroFish imports
# ---------------------------------------------------------------------------
try:
    from mirofish.mirofish_client import run_simulation, is_available
except Exception as _e:
    st.error(f"Failed to import mirofish_client: {_e}")
    run_simulation = None
    is_available = None

try:
    from mirofish.seed_generator import generate_seed
except Exception as _e:
    st.error(f"Failed to import seed_generator: {_e}")
    generate_seed = None

try:
    from mirofish.report_parser import parse_report
except Exception as _e:
    st.error(f"Failed to import report_parser: {_e}")
    parse_report = None

# ---------------------------------------------------------------------------
# Signal combiner import
# ---------------------------------------------------------------------------
try:
    from models.signal_combiner import combine_signals
except Exception as _e:
    st.error(f"Failed to import signal_combiner: {_e}")
    combine_signals = None

# ---------------------------------------------------------------------------
# Dashboard component imports
# ---------------------------------------------------------------------------
try:
    from dashboard.components.charts import inventory_bar_chart, signal_gauge
except Exception as _e:
    st.error(f"Failed to import charts component: {_e}")
    inventory_bar_chart = None
    signal_gauge = None

try:
    from dashboard.components.signal_card import render_signal_card
except Exception as _e:
    st.error(f"Failed to import signal_card component: {_e}")
    render_signal_card = None

# ---------------------------------------------------------------------------
# Cached data fetchers
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def cached_crude_inventory(num_weeks: int = 12):
    if fetch_crude_inventory is None:
        return None
    try:
        return fetch_crude_inventory(num_weeks)
    except Exception as exc:
        st.error(f"Error fetching crude inventory history: {exc}")
        return None


@st.cache_data(ttl=3600)
def cached_latest_inventory():
    if get_latest_inventory is None:
        return {}
    try:
        return get_latest_inventory() or {}
    except Exception as exc:
        st.error(f"Error fetching latest inventory: {exc}")
        return {}


@st.cache_data(ttl=300)
def cached_inventory_signal():
    if compute_inventory_signal is None:
        return {}
    try:
        return compute_inventory_signal() or {}
    except Exception as exc:
        st.error(f"Error computing inventory signal: {exc}")
        return {}


@st.cache_data(ttl=300)
def cached_sentiment_signal():
    if compute_sentiment_signal is None:
        return {}
    try:
        return compute_sentiment_signal() or {}
    except Exception as exc:
        st.error(f"Error computing sentiment signal: {exc}")
        return {}


@st.cache_data(ttl=300)
def cached_oil_news():
    if fetch_oil_news is None:
        return []
    try:
        return fetch_oil_news() or []
    except Exception as exc:
        st.error(f"Error fetching oil news: {exc}")
        return []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _signal_colour(signal: str) -> str:
    s = str(signal).upper()
    if "BULL" in s:
        return "green"
    if "BEAR" in s:
        return "red"
    return "grey"


def _signal_recommendation(signal: str) -> str:
    s = str(signal).upper()
    if "BULL" in s:
        return "Consider: USO calls, XOM / CVX / OXY long positions, COP long."
    if "BEAR" in s:
        return "Consider: USO puts, XOM / CVX / OXY short or put positions, reduce energy exposure."
    return "Mixed signals — wait for confirmation before entering directional trades."


def _apply_dark(fig):
    if fig is not None:
        try:
            fig.update_layout(template="plotly_dark")
        except Exception:
            pass
    return fig


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Oil Intelligence", page_icon="🛢️", layout="wide")
st.title("🛢️ Oil Intelligence")
st.caption(f"Last refreshed: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

with st.spinner("Loading EIA inventory data…"):
    latest_inv = cached_latest_inventory()
    inv_history_df = cached_crude_inventory(num_weeks=12)

with st.spinner("Computing signals…"):
    inv_signal_dict = cached_inventory_signal()
    sent_signal_dict = cached_sentiment_signal()

crude_stocks_mb = latest_inv.get("crude_stocks_mb", latest_inv.get("value"))
wow_change_mb = latest_inv.get("wow_change_mb", latest_inv.get("change"))
inv_signal_label = inv_signal_dict.get("signal", "NEUTRAL")
inv_score = float(inv_signal_dict.get("score", 0.5))

# ---------------------------------------------------------------------------
# Section 1 — Top 3 metrics row
# ---------------------------------------------------------------------------

st.subheader("EIA Crude Inventory Snapshot")
m1, m2, m3 = st.columns(3)

with m1:
    st.metric(
        label="Crude Stocks",
        value=f"{float(crude_stocks_mb):,.1f} Mb" if crude_stocks_mb is not None else "—",
    )

with m2:
    delta_val = None
    if wow_change_mb is not None:
        try:
            delta_val = float(wow_change_mb)
        except (TypeError, ValueError):
            pass
    st.metric(
        label="WoW Change",
        value=f"{delta_val:+.1f} Mb" if delta_val is not None else "—",
        delta=f"{delta_val:+.1f} Mb" if delta_val is not None else None,
    )

with m3:
    colour = _signal_colour(inv_signal_label)
    st.markdown(
        f"<div style='font-size:0.85rem;color:#888'>Signal</div>"
        f"<div style='font-size:1.6rem;font-weight:700;color:{colour}'>{inv_signal_label}</div>",
        unsafe_allow_html=True,
    )

st.divider()

# ---------------------------------------------------------------------------
# Section 2 — Inventory trend chart
# ---------------------------------------------------------------------------

st.subheader("12-Week Inventory Trend")
if inv_history_df is not None and inventory_bar_chart is not None:
    try:
        fig_inv = _apply_dark(inventory_bar_chart(inv_history_df))
        if fig_inv is not None:
            st.plotly_chart(fig_inv, use_container_width=True)
    except Exception as exc:
        st.error(f"Inventory chart error: {exc}")
else:
    st.info("Inventory history chart unavailable.")

st.divider()

# ---------------------------------------------------------------------------
# Section 3 — Signal explanation
# ---------------------------------------------------------------------------

st.subheader("Signal Interpretation")

sig_level = inv_signal_dict.get("level", inv_signal_label)
sig_score_pct = int(inv_score * 100)

exp_col, trade_col = st.columns(2)
with exp_col:
    st.markdown(f"**Level:** {sig_level}")
    st.markdown(f"**Score:** {sig_score_pct} / 100")
    sig_meaning = inv_signal_dict.get(
        "meaning",
        "Inventory draws below expectations are bullish for crude prices; builds are bearish.",
    )
    st.markdown(f"**What it means:** {sig_meaning}")

with trade_col:
    st.markdown("**Recommended Trades**")
    st.info(_signal_recommendation(inv_signal_label))

st.divider()

# ---------------------------------------------------------------------------
# Section 4 — MiroFish simulation
# ---------------------------------------------------------------------------

st.subheader("MiroFish AI Simulation")

mirofish_result = None
mirofish_ran = False

_miro_available = False
if is_available is not None:
    try:
        _miro_available = bool(is_available())
    except Exception as exc:
        st.error(f"MiroFish availability check failed: {exc}")

if _miro_available:
    if st.button("Run MiroFish Simulation", type="primary"):
        with st.spinner("Running MiroFish simulation…"):
            try:
                news_headlines = cached_oil_news()
                sentiment_score = float(sent_signal_dict.get("score", 0.5))
                quotes = {}

                seed = None
                if generate_seed is not None:
                    seed = generate_seed(
                        inventory=latest_inv,
                        quotes=quotes,
                        news_headlines=news_headlines,
                        sentiment_score=sentiment_score,
                        technical_signals={},
                    )

                report_raw = None
                if run_simulation is not None and seed is not None:
                    report_raw = run_simulation(seed)

                if parse_report is not None and report_raw is not None:
                    mirofish_result = parse_report(report_raw)
                    mirofish_ran = True

                if mirofish_result and render_signal_card is not None:
                    render_signal_card(mirofish_result, "MiroFish Simulation Result")
                elif mirofish_result:
                    st.json(mirofish_result)
                else:
                    st.warning("MiroFish returned no result.")

            except Exception as exc:
                st.error(f"MiroFish simulation error: {exc}")
else:
    st.warning(
        "MiroFish not running. Start it with: `cd ../MiroFish && npm run dev`"
    )

st.divider()

# ---------------------------------------------------------------------------
# Section 5 — News
# ---------------------------------------------------------------------------

st.subheader("Oil Market News")

with st.spinner("Fetching oil news…"):
    news_items = cached_oil_news()

sentiment_score_val = float(sent_signal_dict.get("score", 0.5))
sent_label = sent_signal_dict.get("signal", "NEUTRAL")
sent_colour = _signal_colour(sent_label)

news_col, sent_col = st.columns([3, 1])

with news_col:
    if news_items:
        for item in news_items[:10]:
            headline = item.get("title") or item.get("headline") or str(item)
            pub_raw = item.get("published_at") or item.get("publishedAt") or item.get("date")
            pub_str = ""
            if pub_raw:
                try:
                    if isinstance(pub_raw, str):
                        pub_str = f" — {pub_raw}"
                    else:
                        pub_str = f" — {pub_raw}"
                except Exception:
                    pub_str = ""
            url = item.get("url") or item.get("link") or "#"
            st.markdown(f"- [{headline}]({url}){pub_str}")
    else:
        st.info("No news headlines available.")

with sent_col:
    st.markdown("**Sentiment Score**")
    st.markdown(
        f"<div style='font-size:2rem;font-weight:700;color:{sent_colour}'>"
        f"{sentiment_score_val:.2f}</div>",
        unsafe_allow_html=True,
    )
    st.caption(f"Signal: {sent_label}")

st.divider()

# ---------------------------------------------------------------------------
# Section 6 — Combined signal gauge
# ---------------------------------------------------------------------------

st.subheader("Combined Signal")

sent_score = float(sent_signal_dict.get("score", 0.5))
miro_score = None
if mirofish_ran and mirofish_result:
    try:
        miro_score = float(mirofish_result.get("score", 0.5))
    except (TypeError, ValueError):
        miro_score = None

if miro_score is not None:
    # Weights: inventory 0.45, sentiment 0.20, MiroFish 0.35
    combined_score = 0.45 * inv_score + 0.20 * sent_score + 0.35 * miro_score
    weight_note = "Weights: Inventory 45% · Sentiment 20% · MiroFish 35%"
else:
    # Weights: inventory 0.70, sentiment 0.30
    combined_score = 0.70 * inv_score + 0.30 * sent_score
    weight_note = "Weights: Inventory 70% · Sentiment 30% (MiroFish not run)"

combined_score = max(0.0, min(1.0, combined_score))

if miro_score is not None:
    combined_label_parts = [
        f"Inventory: {inv_score:.2f}",
        f"Sentiment: {sent_score:.2f}",
        f"MiroFish: {miro_score:.2f}",
    ]
else:
    combined_label_parts = [
        f"Inventory: {inv_score:.2f}",
        f"Sentiment: {sent_score:.2f}",
    ]

gauge_col, detail_col = st.columns([2, 1])

with gauge_col:
    if signal_gauge is not None:
        try:
            fig_gauge = _apply_dark(signal_gauge(combined_score, "Combined Oil Signal"))
            if fig_gauge is not None:
                st.plotly_chart(fig_gauge, use_container_width=True)
        except Exception as exc:
            st.error(f"Gauge chart error: {exc}")
    else:
        st.metric("Combined Score", f"{combined_score:.2f}")

with detail_col:
    st.markdown("**Component Scores**")
    for part in combined_label_parts:
        st.markdown(f"- {part}")
    st.caption(weight_note)

    if combine_signals is not None:
        try:
            full_combined = combine_signals(
                inv=inv_signal_dict,
                tech={},
                miro=mirofish_result or {},
                sent=sent_signal_dict,
                ml={},
                ticker="OIL",
            )
            if full_combined:
                final_label = full_combined.get("signal", "NEUTRAL")
                final_colour = _signal_colour(final_label)
                st.markdown(
                    f"**Final Signal:** "
                    f"<span style='color:{final_colour};font-weight:700'>{final_label}</span>",
                    unsafe_allow_html=True,
                )
        except Exception as exc:
            st.error(f"Signal combiner error: {exc}")
