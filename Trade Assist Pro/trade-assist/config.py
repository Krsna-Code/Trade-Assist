from dotenv import load_dotenv
import os

load_dotenv()

# ── API Keys ──────────────────────────────────────────────────────────────────
EIA_API_KEY      = os.getenv("EIA_API_KEY", "")
GROQ_API_KEY     = os.getenv("GROQ_API_KEY", "")
ZEP_API_KEY      = os.getenv("ZEP_API_KEY", "")
NEWS_API_KEY     = os.getenv("NEWS_API_KEY", "")
ALPACA_API_KEY   = os.getenv("ALPACA_API_KEY", "")
ALPACA_SECRET    = os.getenv("ALPACA_SECRET_KEY", "")

# ── Tickers ───────────────────────────────────────────────────────────────────
TICKERS = {
    "broad_market": ["SPY", "QQQ"],
    "oil_stocks":   ["XOM", "CVX", "OXY"],
    "oil_etfs":     ["USO"],
    "futures":      ["CL=F"],
}

CRYPTO_PAIRS = ["BTC/USDT", "ETH/USDT"]

# ── Signal weights (sum = 1.0) ────────────────────────────────────────────────
SIGNAL_WEIGHTS = {
    "inventory": 0.30,
    "technical": 0.25,
    "mirofish":  0.25,
    "sentiment": 0.10,
    "ml_model":  0.10,
}

# ── Score thresholds → recommendation ────────────────────────────────────────
SCORE_THRESHOLDS = {
    "strong_buy":  75,
    "buy":         60,
    "hold":        40,
    "sell":        25,
}

# ── EIA inventory change thresholds (fraction WoW) ───────────────────────────
INVENTORY_THRESHOLDS = {
    "strong_bullish": -0.02,
    "bullish":        -0.005,
    "bearish":         0.005,
    "strong_bearish":  0.02,
}

EIA_SERIES = {
    "crude_stocks": "PET.WCRSTUS1.W",
}

# ── MiroFish ──────────────────────────────────────────────────────────────────
MIROFISH_URL    = os.getenv("MIROFISH_URL", "http://localhost:5001")
MIROFISH_AGENTS = 20
MIROFISH_ROUNDS = 10

# ── Groq LLM ──────────────────────────────────────────────────────────────────
GROQ_MODEL = "llama-3.1-70b-versatile"

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///trade_assist.db")

# ── Technical analysis parameters ────────────────────────────────────────────
RSI_PERIOD       = 14
MACD_FAST        = 12
MACD_SLOW        = 26
MACD_SIGNAL      = 9
BB_PERIOD        = 20
BB_STD           = 2
VOLUME_MA_PERIOD = 20

# ── Options filters ───────────────────────────────────────────────────────────
OPTIONS_DELTA_MIN            = 0.30
OPTIONS_DELTA_MAX            = 0.60
OPTIONS_MAX_THETA_PCT        = 0.10
OPTIONS_MIN_IV_RANK_STRADDLE = 50

# ── Backtesting ───────────────────────────────────────────────────────────────
BACKTEST_LOOKBACK_YEARS  = 2
BACKTEST_INITIAL_CAPITAL = 100_000
BACKTEST_COMMISSION      = 0.001
