import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from datetime import datetime, timezone


def generate_seed(
    inventory: dict,
    quotes: list,
    news_headlines: list,
    sentiment_score: float,
    technical_signals: dict,
) -> str:
    timestamp = datetime.now(timezone.utc).isoformat()

    inv_date = inventory.get("report_date", "N/A")
    crude_stocks = inventory.get("crude_stocks_mb", "N/A")
    wow_change = inventory.get("wow_change_pct", None)
    inv_signal = inventory.get("signal", "N/A")

    if wow_change is not None:
        direction = "draw" if wow_change < 0 else "build"
        wow_str = f"{wow_change:+.2f}% ({direction})"
    else:
        wow_str = "N/A"

    lines = [
        "=== MARKET SEED DOCUMENT ===",
        f"Generated: {timestamp}",
        "",
        "--- OIL INVENTORY (CORE SIGNAL) ---",
        f"Report Date: {inv_date}",
        f"Crude Stocks: {crude_stocks} million barrels",
        f"WoW Change: {wow_str}",
        f"Signal: {inv_signal}",
        "",
        "--- PRICE SUMMARY ---",
    ]

    for q in quotes:
        ticker = q.get("ticker", "?")
        price = q.get("price", "N/A")
        change_pct = q.get("change_pct", None)
        sig = q.get("signal", "")
        change_str = f"{change_pct:+.2f}%" if change_pct is not None else "N/A"
        lines.append(f"{ticker:<6} {price:>10}  {change_str:>8}  {sig}")

    lines += ["", "--- TECHNICAL ANALYSIS ---"]

    for ticker, data in technical_signals.items():
        rsi = data.get("rsi", "N/A")
        trend = data.get("signal", "N/A")
        score = data.get("score", "N/A")
        lines.append(f"{ticker:<6} RSI={rsi}  trend={trend}  score={score}")

    lines += [
        "",
        "--- NEWS SENTIMENT ---",
        f"Score: {sentiment_score:.1f}/100",
        "Top Headlines:",
    ]

    for headline in news_headlines:
        lines.append(f"- {headline}")

    lines += [
        "",
        "--- SIMULATION CONTEXT ---",
        "Focus: Energy markets, oil stocks (XOM, CVX, OXY, USO), broad market (SPY, QQQ)",
        "Agent types to simulate: institutional oil traders, retail investors, short sellers, "
        "energy analysts, financial media, OPEC watchers",
    ]

    return "\n".join(lines)
