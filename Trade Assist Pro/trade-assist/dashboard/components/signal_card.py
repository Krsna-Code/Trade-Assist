import streamlit as st


_DIRECTION_COLORS = {
    "STRONG BUY": "green",
    "BUY": "green",
    "HOLD": "grey",
    "SELL": "red",
    "STRONG SELL": "red",
}

_BADGE_CSS = {
    "green": "background:#1b5e20;color:#a5d6a7;padding:2px 10px;border-radius:12px;font-weight:bold;",
    "red": "background:#b71c1c;color:#ef9a9a;padding:2px 10px;border-radius:12px;font-weight:bold;",
    "grey": "background:#37474f;color:#cfd8dc;padding:2px 10px;border-radius:12px;font-weight:bold;",
}


def _direction_badge(direction: str) -> str:
    color = _DIRECTION_COLORS.get(direction.upper(), "grey")
    css = _BADGE_CSS[color]
    return f'<span style="{css}">{direction.upper()}</span>'


def render_signal_card(signal_dict: dict, title: str = "Signal"):
    direction = signal_dict.get("direction", signal_dict.get("recommendation", "HOLD")).upper()
    score = float(signal_dict.get("score", signal_dict.get("composite_score", 50.0)))
    source = signal_dict.get("source", "—")
    timestamp = signal_dict.get("timestamp", "—")

    with st.container():
        st.markdown(f"**{title}** &nbsp; {_direction_badge(direction)}", unsafe_allow_html=True)
        st.progress(int(min(max(score, 0), 100)))
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Score", f"{score:.1f}")
        with col2:
            st.metric("Source", source)
        with col3:
            st.metric("Timestamp", str(timestamp)[:19] if timestamp != "—" else "—")


def render_recommendation_card(recommendation: dict):
    direction = recommendation.get("recommendation", "HOLD").upper()
    score = float(recommendation.get("composite_score", 50.0))
    breakdown = recommendation.get("breakdown", {})

    color = _DIRECTION_COLORS.get(direction, "grey")

    if color == "green":
        ctx = st.success
    elif color == "red":
        ctx = st.error
    else:
        ctx = st.warning

    with ctx(f"**{direction}**  —  Composite Score: {score:.1f} / 100"):
        pass

    st.metric(label="Composite Score", value=f"{score:.1f}", delta=direction)

    if breakdown:
        rows = [
            {"Signal": k, "Score": f"{v:.1f}" if isinstance(v, (int, float)) else str(v)}
            for k, v in breakdown.items()
        ]
        import pandas as pd
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
