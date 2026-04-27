import plotly.graph_objects as go
import numpy as np


def _base_figure(title: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        title=title,
        template="plotly_dark",
        xaxis_title="Stock Price at Expiry (USD)",
        yaxis_title="Profit / Loss (USD)",
        margin=dict(l=40, r=20, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.add_hline(y=0, line_color="white", line_width=0.8, line_dash="dot")
    return fig


def _add_shading(fig: go.Figure, pnl: np.ndarray):
    fig.add_hrect(y0=0, y1=max(pnl.max(), 0.01), fillcolor="rgba(38,166,154,0.12)", line_width=0)
    fig.add_hrect(y0=min(pnl.min(), -0.01), y1=0, fillcolor="rgba(239,83,80,0.12)", line_width=0)


def long_call_payoff(strike: float, premium: float, spot: float) -> go.Figure:
    prices = np.linspace(spot * 0.7, spot * 1.3, 100)
    pnl = np.maximum(prices - strike, 0) - premium

    fig = _base_figure(f"Long Call  |  Strike={strike}  Premium={premium}")
    _add_shading(fig, pnl)

    breakeven = strike + premium
    fig.add_vline(x=breakeven, line_dash="dash", line_color="#ffa726", annotation_text=f"BE {breakeven:.2f}")

    fig.add_trace(
        go.Scatter(x=prices, y=pnl, mode="lines", name="P&L", line=dict(color="#26a69a", width=2))
    )
    return fig


def long_put_payoff(strike: float, premium: float, spot: float) -> go.Figure:
    prices = np.linspace(spot * 0.7, spot * 1.3, 100)
    pnl = np.maximum(strike - prices, 0) - premium

    fig = _base_figure(f"Long Put  |  Strike={strike}  Premium={premium}")
    _add_shading(fig, pnl)

    breakeven = strike - premium
    fig.add_vline(x=breakeven, line_dash="dash", line_color="#ffa726", annotation_text=f"BE {breakeven:.2f}")

    fig.add_trace(
        go.Scatter(x=prices, y=pnl, mode="lines", name="P&L", line=dict(color="#26a69a", width=2))
    )
    return fig


def covered_call_payoff(spot: float, strike: float, premium: float) -> go.Figure:
    prices = np.linspace(spot * 0.7, spot * 1.3, 100)
    stock_pnl = prices - spot
    short_call_pnl = premium - np.maximum(prices - strike, 0)
    pnl = stock_pnl + short_call_pnl

    fig = _base_figure(f"Covered Call  |  Spot={spot}  Strike={strike}  Premium={premium}")
    _add_shading(fig, pnl)

    breakeven = spot - premium
    fig.add_vline(x=breakeven, line_dash="dash", line_color="#ffa726", annotation_text=f"BE {breakeven:.2f}")

    fig.add_trace(
        go.Scatter(x=prices, y=pnl, mode="lines", name="P&L", line=dict(color="#26a69a", width=2))
    )
    return fig


def straddle_payoff(strike: float, call_premium: float, put_premium: float, spot: float) -> go.Figure:
    prices = np.linspace(spot * 0.7, spot * 1.3, 100)
    total_premium = call_premium + put_premium
    pnl = np.maximum(prices - strike, 0) + np.maximum(strike - prices, 0) - total_premium

    fig = _base_figure(
        f"Straddle  |  Strike={strike}  Call={call_premium}  Put={put_premium}"
    )
    _add_shading(fig, pnl)

    be_up = strike + total_premium
    be_dn = strike - total_premium
    fig.add_vline(x=be_up, line_dash="dash", line_color="#ffa726", annotation_text=f"BE {be_up:.2f}")
    fig.add_vline(x=be_dn, line_dash="dash", line_color="#ffa726", annotation_text=f"BE {be_dn:.2f}")

    fig.add_trace(
        go.Scatter(x=prices, y=pnl, mode="lines", name="P&L", line=dict(color="#26a69a", width=2))
    )
    return fig


def bull_call_spread_payoff(
    long_strike: float, short_strike: float, net_debit: float, spot: float
) -> go.Figure:
    prices = np.linspace(spot * 0.7, spot * 1.3, 100)
    long_call = np.maximum(prices - long_strike, 0)
    short_call = np.maximum(prices - short_strike, 0)
    pnl = long_call - short_call - net_debit

    fig = _base_figure(
        f"Bull Call Spread  |  Long={long_strike}  Short={short_strike}  Debit={net_debit}"
    )
    _add_shading(fig, pnl)

    breakeven = long_strike + net_debit
    fig.add_vline(x=breakeven, line_dash="dash", line_color="#ffa726", annotation_text=f"BE {breakeven:.2f}")

    fig.add_trace(
        go.Scatter(x=prices, y=pnl, mode="lines", name="P&L", line=dict(color="#26a69a", width=2))
    )
    return fig
