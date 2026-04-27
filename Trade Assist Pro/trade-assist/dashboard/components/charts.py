import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots


def candlestick_chart(df: pd.DataFrame, ticker: str, show_volume: bool = True) -> go.Figure:
    rows = 2 if show_volume else 1
    row_heights = [0.7, 0.3] if show_volume else [1.0]

    fig = make_subplots(
        rows=rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
    )

    fig.add_trace(
        go.Candlestick(
            x=df["date"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name=ticker,
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
        ),
        row=1,
        col=1,
    )

    if len(df) >= 20:
        sma20 = df["close"].rolling(20).mean()
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=sma20,
                mode="lines",
                name="SMA 20",
                line=dict(color="#ffa726", width=1.2),
            ),
            row=1,
            col=1,
        )

    if len(df) >= 50:
        sma50 = df["close"].rolling(50).mean()
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=sma50,
                mode="lines",
                name="SMA 50",
                line=dict(color="#ab47bc", width=1.2),
            ),
            row=1,
            col=1,
        )

    if show_volume and "volume" in df.columns:
        colors = [
            "#26a69a" if c >= o else "#ef5350"
            for c, o in zip(df["close"], df["open"])
        ]
        fig.add_trace(
            go.Bar(
                x=df["date"],
                y=df["volume"],
                name="Volume",
                marker_color=colors,
                showlegend=False,
            ),
            row=2,
            col=1,
        )
        fig.update_yaxes(title_text="Volume", row=2, col=1)

    fig.update_layout(
        title=f"{ticker} — Price Chart",
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=20, t=60, b=20),
    )
    fig.update_yaxes(title_text="Price (USD)", row=1, col=1)
    return fig


def signal_gauge(score: float, title: str = "Signal Score") -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            title={"text": title, "font": {"size": 18}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": "#ffffff", "thickness": 0.25},
                "bgcolor": "#1e1e1e",
                "steps": [
                    {"range": [0, 25], "color": "#ef5350"},
                    {"range": [25, 40], "color": "#ffa726"},
                    {"range": [40, 60], "color": "#78909c"},
                    {"range": [60, 75], "color": "#a5d6a7"},
                    {"range": [75, 100], "color": "#26a69a"},
                ],
                "threshold": {
                    "line": {"color": "white", "width": 3},
                    "thickness": 0.8,
                    "value": score,
                },
            },
            number={"suffix": "", "font": {"size": 28}},
        )
    )
    fig.update_layout(
        template="plotly_dark",
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


def inventory_bar_chart(df: pd.DataFrame) -> go.Figure:
    colors = ["#ef5350" if v >= 0 else "#26a69a" for v in df["wow_change_mb"]]

    fig = go.Figure(
        go.Bar(
            x=df["report_date"],
            y=df["wow_change_mb"],
            marker_color=colors,
            name="WoW Change (Mb)",
        )
    )
    fig.update_layout(
        title="Weekly Inventory Change (Mb)",
        xaxis_title="Report Date",
        yaxis_title="WoW Change (Mb)",
        template="plotly_dark",
        margin=dict(l=40, r=20, t=60, b=40),
    )
    fig.add_hline(y=0, line_color="white", line_width=0.8)
    return fig


def equity_curve_chart(equity_curve: list) -> go.Figure:
    dates = [p["date"] for p in equity_curve]
    equity = [p["equity"] for p in equity_curve]

    fig = go.Figure(
        go.Scatter(
            x=dates,
            y=equity,
            mode="lines",
            name="Equity",
            line=dict(color="#26a69a", width=2),
            fill="tozeroy",
            fillcolor="rgba(38,166,154,0.15)",
        )
    )
    fig.update_layout(
        title="Backtest Equity Curve",
        xaxis_title="Date",
        yaxis_title="Portfolio Value (USD)",
        template="plotly_dark",
        margin=dict(l=40, r=20, t=60, b=40),
    )
    return fig
