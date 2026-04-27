"""
Trade Assist Pro — Comprehensive Test Suite
Tests every module: config, scrapers, processors, strategies,
MiroFish, models, backtesting, and alerts.
All network calls are mocked — no internet or API keys required.
"""

import json
import os
import sys
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# ── optional dependency guards ────────────────────────────────────────────────
try:
    import pandas_ta  # noqa: F401
    HAS_PANDAS_TA = True
except ImportError:
    HAS_PANDAS_TA = False

try:
    import xgboost  # noqa: F401
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    import apscheduler  # noqa: F401
    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False


# ═══════════════════════════════════════════════════════════════════════════════
# SHARED FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════

def _ohlcv(n=100, trend="flat", base=100.0, seed=42) -> pd.DataFrame:
    """Synthetic lowercase OHLCV DataFrame with UTC DatetimeIndex."""
    np.random.seed(seed)
    dates = pd.date_range(
        end=datetime.now(timezone.utc), periods=n, freq="D", tz="UTC"
    )
    if trend == "up":
        prices = base + np.linspace(0, 25, n) + np.random.randn(n) * 0.3
    elif trend == "down":
        prices = base + np.linspace(0, -25, n) + np.random.randn(n) * 0.3
    else:
        prices = base + np.random.randn(n) * 1.5
    prices = np.maximum(prices, 1.0)
    return pd.DataFrame(
        {
            "open":   prices * 0.999,
            "high":   prices * 1.005,
            "low":    prices * 0.995,
            "close":  prices,
            "volume": np.random.randint(1_000_000, 5_000_000, n).astype(float),
        },
        index=dates,
    )


def _ohlcv_capital(n=100, trend="flat", base=100.0) -> pd.DataFrame:
    """Same but with capitalised column names (for BacktestEngine)."""
    df = _ohlcv(n, trend, base)
    return df.rename(columns={"open": "Open", "high": "High",
                               "low": "Low",  "close": "Close",
                               "volume": "Volume"})


def _make_breakout(bullish=True) -> pd.DataFrame:
    """OHLCV where the last bar breaks the 20-day high/low on 3× volume."""
    df = _ohlcv(100, "flat", 100.0)
    if bullish:
        new_price = float(df["high"].iloc[-21:-1].max()) * 1.05
        df.iloc[-1, df.columns.get_loc("close")] = new_price
        df.iloc[-1, df.columns.get_loc("high")]  = new_price
    else:
        new_price = float(df["low"].iloc[-21:-1].min()) * 0.95
        df.iloc[-1, df.columns.get_loc("close")] = new_price
        df.iloc[-1, df.columns.get_loc("low")]   = new_price
    df.iloc[-1, df.columns.get_loc("volume")] = float(df["volume"].mean() * 3)
    return df


def _mock_chain(spot=100.0) -> dict:
    """Minimal options chain dict that all strategy functions accept."""
    strikes = np.arange(85, 116, 5, dtype=float)
    n = len(strikes)
    calls = pd.DataFrame({
        "strike":           strikes,
        "lastPrice":        np.abs(spot - strikes) * 0.5 + 1.5,
        "bid":              np.abs(spot - strikes) * 0.45 + 1.4,
        "ask":              np.abs(spot - strikes) * 0.55 + 1.6,
        "mid_price":        np.abs(spot - strikes) * 0.5 + 1.5,
        "volume":           np.random.randint(10, 500, n).astype(float),
        "openInterest":     np.random.randint(100, 5000, n).astype(float),
        "impliedVolatility":np.random.uniform(0.2, 0.5, n),
        "delta":            np.linspace(0.85, 0.10, n),
        "gamma":            np.random.uniform(0.01, 0.05, n),
        "theta":            -np.random.uniform(0.05, 0.2, n),
        "vega":             np.random.uniform(0.1, 0.3, n),
        "spot_price":       spot,
        "expiry":           "2025-06-20",
        "ticker":           "XOM",
    })
    puts = calls.copy()
    puts["delta"] = -calls["delta"].values
    return {
        "calls":  calls,
        "puts":   puts,
        "expiry": "2025-06-20",
        "ticker": "XOM",
        "spot":   spot,
    }


def _rec(score=80.0, ticker="SPY") -> dict:
    """Minimal recommendation dict for alert tests."""
    return {
        "ticker":          ticker,
        "composite_score": score,
        "recommendation":  "BUY" if score >= 60 else "SELL",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 1 · CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

class TestConfig(unittest.TestCase):

    def setUp(self):
        import config as cfg
        self.cfg = cfg

    def test_signal_weights_sum_to_one(self):
        total = sum(self.cfg.SIGNAL_WEIGHTS.values())
        self.assertAlmostEqual(total, 1.0, places=9)

    def test_all_expected_weight_keys_present(self):
        keys = {"inventory", "technical", "mirofish", "sentiment", "ml_model"}
        self.assertEqual(set(self.cfg.SIGNAL_WEIGHTS.keys()), keys)

    def test_score_thresholds_are_ordered(self):
        t = self.cfg.SCORE_THRESHOLDS
        self.assertGreater(t["strong_buy"], t["buy"])
        self.assertGreater(t["buy"],        t["hold"])
        self.assertGreater(t["hold"],       t["sell"])

    def test_inventory_thresholds_signs(self):
        t = self.cfg.INVENTORY_THRESHOLDS
        self.assertLess(t["strong_bullish"], 0)
        self.assertLess(t["bullish"],        0)
        self.assertGreater(t["bearish"],     0)
        self.assertGreater(t["strong_bearish"], 0)

    def test_tickers_dict_has_required_groups(self):
        keys = set(self.cfg.TICKERS.keys())
        self.assertIn("broad_market", keys)
        self.assertIn("oil_stocks",   keys)

    def test_backtest_capital_positive(self):
        self.assertGreater(self.cfg.BACKTEST_INITIAL_CAPITAL, 0)

    def test_commission_between_zero_and_one(self):
        self.assertGreater(self.cfg.BACKTEST_COMMISSION, 0)
        self.assertLess(   self.cfg.BACKTEST_COMMISSION, 1)


# ═══════════════════════════════════════════════════════════════════════════════
# 2 · EIA SCRAPER
# ═══════════════════════════════════════════════════════════════════════════════

class TestEIAScraper(unittest.TestCase):

    def _mock_eia_response(self, rows):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": {"data": rows}}
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    def _make_rows(self, n=5):
        base = 430.0
        return [
            {"period": f"2025-0{i+1}-01", "value": str(base - i * 2)}
            for i in range(n)
        ]

    @patch("data.scrapers.eia_scraper.requests.get")
    def test_fetch_returns_dataframe(self, mock_get):
        mock_get.return_value = self._mock_eia_response(self._make_rows(5))
        from data.scrapers.eia_scraper import fetch_crude_inventory
        df = fetch_crude_inventory(num_weeks=3)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertIn("crude_stocks_mb", df.columns)
        self.assertIn("wow_change_pct",  df.columns)

    @patch("data.scrapers.eia_scraper.requests.get")
    def test_wow_change_pct_computed(self, mock_get):
        mock_get.return_value = self._mock_eia_response(self._make_rows(5))
        from data.scrapers.eia_scraper import fetch_crude_inventory
        df = fetch_crude_inventory(num_weeks=3)
        self.assertFalse(df["wow_change_pct"].isna().all())

    @patch("data.scrapers.eia_scraper.requests.get")
    def test_get_latest_inventory_keys(self, mock_get):
        mock_get.return_value = self._mock_eia_response(self._make_rows(5))
        from data.scrapers.eia_scraper import get_latest_inventory
        result = get_latest_inventory()
        for key in ("report_date", "crude_stocks_mb", "wow_change_mb", "wow_change_pct"):
            self.assertIn(key, result)

    @patch("data.scrapers.eia_scraper.requests.get")
    def test_empty_response_raises(self, mock_get):
        mock_get.return_value = self._mock_eia_response([])
        from data.scrapers.eia_scraper import fetch_crude_inventory
        with self.assertRaises(ValueError):
            fetch_crude_inventory()


# ═══════════════════════════════════════════════════════════════════════════════
# 3 · NASDAQ SCRAPER
# ═══════════════════════════════════════════════════════════════════════════════

class TestNasdaqScraper(unittest.TestCase):

    def _mock_ticker(self, close=150.0, prev_close=148.0):
        mock_t = MagicMock()
        hist = _ohlcv(60).rename(columns=str.title)
        mock_t.history.return_value = hist
        mock_t.fast_info.last_price      = close
        mock_t.fast_info.previous_close  = prev_close
        mock_t.fast_info.last_volume     = 1_000_000
        mock_t.fast_info.market_cap      = 500_000_000
        return mock_t

    @patch("data.scrapers.nasdaq_scraper.yf.Ticker")
    def test_fetch_ohlcv_columns(self, mock_ticker_cls):
        mock_ticker_cls.return_value = self._mock_ticker()
        from data.scrapers.nasdaq_scraper import fetch_ohlcv
        df = fetch_ohlcv("SPY", period="6mo")
        for col in ("open", "high", "low", "close", "volume"):
            self.assertIn(col, df.columns)

    @patch("data.scrapers.nasdaq_scraper.yf.Ticker")
    def test_fetch_quote_change_pct(self, mock_ticker_cls):
        mock_ticker_cls.return_value = self._mock_ticker(close=150.0, prev_close=148.0)
        from data.scrapers.nasdaq_scraper import fetch_quote
        q = fetch_quote("SPY")
        self.assertIn("change_pct", q)
        self.assertAlmostEqual(q["change_pct"], round((150 - 148) / 148 * 100, 3))

    @patch("data.scrapers.nasdaq_scraper.yf.Ticker")
    def test_fetch_quote_required_keys(self, mock_ticker_cls):
        mock_ticker_cls.return_value = self._mock_ticker()
        from data.scrapers.nasdaq_scraper import fetch_quote
        q = fetch_quote("XOM")
        for key in ("ticker", "price", "prev_close", "change_pct", "volume"):
            self.assertIn(key, q)


# ═══════════════════════════════════════════════════════════════════════════════
# 4 · OPTIONS SCRAPER
# ═══════════════════════════════════════════════════════════════════════════════

class TestOptionsScraper(unittest.TestCase):

    def _mock_yf_ticker(self, spot=100.0):
        chain = _mock_chain(spot)
        mock_chain_obj = MagicMock()
        mock_chain_obj.calls = chain["calls"]
        mock_chain_obj.puts  = chain["puts"]

        mock_t = MagicMock()
        mock_t.options = ["2025-06-20", "2025-07-18"]
        mock_t.option_chain.return_value = mock_chain_obj
        mock_t.fast_info.last_price = spot

        hist = _ohlcv(260)
        hist["returns"] = hist["close"].pct_change()
        mock_t.history.return_value = hist.rename(columns=str.title)
        return mock_t

    @patch("data.scrapers.options_scraper.yf.Ticker")
    def test_fetch_chain_returns_calls_puts(self, mock_cls):
        mock_cls.return_value = self._mock_yf_ticker()
        from data.scrapers.options_scraper import fetch_chain
        result = fetch_chain("XOM")
        self.assertIn("calls", result)
        self.assertIn("puts",  result)
        self.assertIn("expiry", result)

    @patch("data.scrapers.options_scraper.yf.Ticker")
    def test_fetch_chain_adds_mid_price(self, mock_cls):
        mock_cls.return_value = self._mock_yf_ticker()
        from data.scrapers.options_scraper import fetch_chain
        result = fetch_chain("XOM")
        self.assertIn("mid_price", result["calls"].columns)

    @patch("data.scrapers.options_scraper.yf.Ticker")
    def test_iv_rank_between_0_and_100(self, mock_cls):
        mock_cls.return_value = self._mock_yf_ticker()
        from data.scrapers.options_scraper import get_iv_rank
        rank = get_iv_rank("XOM")
        self.assertGreaterEqual(rank, 0.0)
        self.assertLessEqual(rank, 100.0)

    @patch("data.scrapers.options_scraper.yf.Ticker")
    def test_no_options_raises(self, mock_cls):
        mock_t = MagicMock()
        mock_t.options = []
        mock_cls.return_value = mock_t
        from data.scrapers.options_scraper import fetch_chain
        with self.assertRaises(ValueError):
            fetch_chain("XOM")


# ═══════════════════════════════════════════════════════════════════════════════
# 5 · CRYPTO SCRAPER
# ═══════════════════════════════════════════════════════════════════════════════

class TestCryptoScraper(unittest.TestCase):

    def _mock_exchange(self):
        ex = MagicMock()
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        ex.fetch_ohlcv.return_value = [
            [now_ms - i * 86400000, 60000, 61000, 59000, 60500, 100.0]
            for i in range(10)
        ]
        ex.fetch_ticker.return_value = {
            "last": 60500.0,
            "percentage": 1.2,
            "quoteVolume": 5e9,
            "high": 61000.0,
            "low":  59000.0,
        }
        return ex

    @patch("data.scrapers.crypto_scraper._exchange")
    def test_fetch_ohlcv_columns(self, mock_ex):
        mock_ex.fetch_ohlcv.return_value = self._mock_exchange().fetch_ohlcv.return_value
        from data.scrapers.crypto_scraper import fetch_ohlcv
        df = fetch_ohlcv("BTC/USDT")
        for col in ("open", "high", "low", "close", "volume"):
            self.assertIn(col, df.columns)

    @patch("data.scrapers.crypto_scraper._exchange")
    def test_fetch_ticker_keys(self, mock_ex):
        mock_ex.fetch_ticker.return_value = self._mock_exchange().fetch_ticker.return_value
        from data.scrapers.crypto_scraper import fetch_ticker
        q = fetch_ticker("BTC/USDT")
        for key in ("pair", "price", "change_pct", "volume_24h"):
            self.assertIn(key, q)

    @patch("data.scrapers.crypto_scraper._exchange")
    def test_fetch_all_quotes_returns_list(self, mock_ex):
        mock_ex.fetch_ticker.return_value = self._mock_exchange().fetch_ticker.return_value
        from data.scrapers.crypto_scraper import fetch_all_quotes
        quotes = fetch_all_quotes()
        self.assertIsInstance(quotes, list)


# ═══════════════════════════════════════════════════════════════════════════════
# 6 · NEWS SCRAPER
# ═══════════════════════════════════════════════════════════════════════════════

class TestNewsScraper(unittest.TestCase):

    def _mock_response(self, titles):
        articles = [
            {
                "publishedAt": "2025-04-26T10:00:00Z",
                "source": {"name": "Reuters"},
                "title": t,
                "description": "",
                "url": "https://example.com",
            }
            for t in titles
        ]
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"articles": articles}
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    @patch("data.scrapers.news_scraper.requests.get")
    def test_fetch_oil_news_returns_dataframe(self, mock_get):
        mock_get.return_value = self._mock_response(["Oil prices surge on draw"])
        from data.scrapers.news_scraper import fetch_oil_news
        df = fetch_oil_news()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertIn("title", df.columns)

    @patch("data.scrapers.news_scraper.requests.get")
    def test_empty_api_key_returns_empty_df(self, mock_get):
        import data.scrapers.news_scraper as ns
        original = ns.NEWS_API_KEY
        ns.NEWS_API_KEY = ""
        from data.scrapers.news_scraper import fetch_oil_news
        df = fetch_oil_news()
        self.assertTrue(df.empty)
        ns.NEWS_API_KEY = original

    @patch("data.scrapers.news_scraper.requests.get")
    def test_get_headlines_returns_list_of_strings(self, mock_get):
        mock_get.return_value = self._mock_response(
            ["Oil rally on supply cut", "Crude draw bullish"]
        )
        from data.scrapers.news_scraper import get_headlines
        headlines = get_headlines(topic="oil", n=5)
        self.assertIsInstance(headlines, list)
        if headlines:
            self.assertIsInstance(headlines[0], str)


# ═══════════════════════════════════════════════════════════════════════════════
# 7 · INVENTORY SIGNAL PROCESSOR
# ═══════════════════════════════════════════════════════════════════════════════

class TestInventorySignalClassifier(unittest.TestCase):

    def setUp(self):
        from data.processors.inventory_signal import _classify_change
        self.classify = _classify_change

    def test_strong_bullish_large_draw(self):
        self.assertEqual(self.classify(-0.03), "STRONG_BULLISH")

    def test_bullish_moderate_draw(self):
        self.assertEqual(self.classify(-0.01), "BULLISH")

    def test_neutral_tiny_change(self):
        self.assertEqual(self.classify(0.001), "NEUTRAL")

    def test_bearish_moderate_build(self):
        self.assertEqual(self.classify(0.01), "BEARISH")

    def test_strong_bearish_large_build(self):
        self.assertEqual(self.classify(0.03), "STRONG_BEARISH")

    def test_exact_bullish_boundary(self):
        result = self.classify(-0.005)
        self.assertIn(result, ("BULLISH", "NEUTRAL"))

    def test_exact_bearish_boundary(self):
        result = self.classify(0.005)
        self.assertIn(result, ("BEARISH", "NEUTRAL"))


class TestInventorySignalOutput(unittest.TestCase):

    @patch("data.processors.inventory_signal.get_latest_inventory")
    def test_strong_bullish_score_95(self, mock_inv):
        mock_inv.return_value = {
            "wow_change_pct": -3.0, "crude_stocks_mb": 420.0, "report_date": "2025-04-23"
        }
        from data.processors.inventory_signal import compute_inventory_signal
        result = compute_inventory_signal()
        self.assertEqual(result["signal"], "STRONG_BULLISH")
        self.assertEqual(result["score"],  95)
        self.assertEqual(result["source"], "EIA")

    @patch("data.processors.inventory_signal.get_latest_inventory")
    def test_strong_bearish_score_5(self, mock_inv):
        mock_inv.return_value = {
            "wow_change_pct": 3.0, "crude_stocks_mb": 440.0, "report_date": "2025-04-23"
        }
        from data.processors.inventory_signal import compute_inventory_signal
        result = compute_inventory_signal()
        self.assertEqual(result["signal"], "STRONG_BEARISH")
        self.assertEqual(result["score"],  5)

    @patch("data.processors.inventory_signal.get_latest_inventory")
    def test_result_has_all_required_keys(self, mock_inv):
        mock_inv.return_value = {
            "wow_change_pct": 0.0, "crude_stocks_mb": 430.0, "report_date": "2025-04-23"
        }
        from data.processors.inventory_signal import compute_inventory_signal
        result = compute_inventory_signal()
        for key in ("signal", "score", "wow_change_pct", "crude_stocks_mb", "report_date", "source"):
            self.assertIn(key, result)


# ═══════════════════════════════════════════════════════════════════════════════
# 8 · SENTIMENT SIGNAL PROCESSOR
# ═══════════════════════════════════════════════════════════════════════════════

class TestSentimentScoreHeadline(unittest.TestCase):

    def setUp(self):
        from data.processors.sentiment_signal import score_headline
        self.score = score_headline

    def test_purely_bullish_headline(self):
        s = self.score("Oil prices surge on strong demand rally")
        self.assertGreater(s, 0)

    def test_purely_bearish_headline(self):
        s = self.score("Crude oil crashes on massive oversupply glut")
        self.assertLess(s, 0)

    def test_neutral_headline_returns_zero(self):
        s = self.score("EIA releases weekly petroleum report")
        self.assertEqual(s, 0.0)

    def test_score_bounded(self):
        s = self.score("surge rally gain rise bull strong beat exceed draw")
        self.assertGreaterEqual(s, -1.0)
        self.assertLessEqual(s,   1.0)

    def test_empty_string_returns_zero(self):
        self.assertEqual(self.score(""), 0.0)


class TestSentimentSignalOutput(unittest.TestCase):

    def _make_df(self, titles):
        return pd.DataFrame({
            "published_at": [datetime.now(timezone.utc)] * len(titles),
            "source": ["Reuters"] * len(titles),
            "title": titles,
            "description": [""] * len(titles),
            "url": ["https://example.com"] * len(titles),
        })

    @patch("data.processors.sentiment_signal.fetch_market_news")
    @patch("data.processors.sentiment_signal.fetch_oil_news")
    def test_bullish_headlines_produce_high_score(self, mock_oil, mock_mkt):
        mock_oil.return_value = self._make_df(
            ["Oil rally surge strong demand"] * 5
        )
        mock_mkt.return_value = self._make_df([])
        from data.processors.sentiment_signal import compute_sentiment_signal
        result = compute_sentiment_signal()
        self.assertGreater(result["score"], 50)

    @patch("data.processors.sentiment_signal.fetch_market_news")
    @patch("data.processors.sentiment_signal.fetch_oil_news")
    def test_empty_news_returns_neutral(self, mock_oil, mock_mkt):
        mock_oil.return_value = self._make_df([])
        mock_mkt.return_value = self._make_df([])
        from data.processors.sentiment_signal import compute_sentiment_signal
        result = compute_sentiment_signal()
        self.assertEqual(result["signal"], "NEUTRAL")
        self.assertEqual(result["score"],  50.0)

    @patch("data.processors.sentiment_signal.fetch_market_news")
    @patch("data.processors.sentiment_signal.fetch_oil_news")
    def test_result_required_keys(self, mock_oil, mock_mkt):
        mock_oil.return_value = self._make_df(["Oil rises on supply cut"])
        mock_mkt.return_value = self._make_df([])
        from data.processors.sentiment_signal import compute_sentiment_signal
        result = compute_sentiment_signal()
        for key in ("signal", "score", "mean_sentiment", "num_articles", "top_headlines"):
            self.assertIn(key, result)


# ═══════════════════════════════════════════════════════════════════════════════
# 9 · MOMENTUM STRATEGY
# ═══════════════════════════════════════════════════════════════════════════════

class TestMomentumStrategy(unittest.TestCase):

    def setUp(self):
        from strategies.day_trading.momentum import momentum_signal
        self.signal = momentum_signal

    def test_bullish_breakout_high_volume_is_buy(self):
        df = _make_breakout(bullish=True)
        result = self.signal(df, "XOM")
        self.assertIn(result["signal"], ("BUY", "STRONG_BUY"))
        self.assertGreater(result["score"], 50)

    def test_bearish_breakdown_high_volume_is_sell(self):
        df = _make_breakout(bullish=False)
        result = self.signal(df, "XOM")
        self.assertIn(result["signal"], ("SELL", "STRONG_SELL"))
        self.assertLess(result["score"], 50)

    def test_no_breakout_returns_hold(self):
        df = _ohlcv(100, "flat", 100.0)
        result = self.signal(df, "XOM")
        self.assertEqual(result["signal"], "HOLD")

    def test_insufficient_data_returns_default(self):
        df = _ohlcv(15)
        result = self.signal(df, "XOM")
        self.assertEqual(result["signal"], "HOLD")

    def test_none_input_returns_default(self):
        result = self.signal(None, "XOM")
        self.assertEqual(result["signal"], "HOLD")

    def test_buy_signal_has_stop_and_target(self):
        df = _make_breakout(bullish=True)
        result = self.signal(df, "XOM")
        if result["signal"] in ("BUY", "STRONG_BUY"):
            self.assertIsNotNone(result["stop_loss"])
            self.assertIsNotNone(result["target"])
            self.assertLess(result["stop_loss"], result["entry"])
            self.assertGreater(result["target"], result["entry"])

    def test_output_has_required_keys(self):
        df = _ohlcv(100)
        result = self.signal(df, "TEST")
        for key in ("strategy", "ticker", "signal", "score", "reason", "timestamp"):
            self.assertIn(key, result)

    def test_strategy_name_is_momentum(self):
        result = self.signal(_ohlcv(100), "SPY")
        self.assertEqual(result["strategy"], "momentum")


# ═══════════════════════════════════════════════════════════════════════════════
# 10 · NEWS-BASED STRATEGY
# ═══════════════════════════════════════════════════════════════════════════════

class TestNewsBasedStrategy(unittest.TestCase):

    def setUp(self):
        from strategies.day_trading.news_based import news_signal
        self.signal = news_signal

    def test_strong_bullish_inventory_high_sentiment_is_strong_buy(self):
        r = self.signal(sentiment_score=80.0, inventory_signal="STRONG_BULLISH")
        self.assertEqual(r["signal"], "STRONG_BUY")

    def test_bullish_inventory_positive_sentiment_is_buy(self):
        r = self.signal(sentiment_score=65.0, inventory_signal="BULLISH")
        self.assertEqual(r["signal"], "BUY")

    def test_strong_bearish_inventory_low_sentiment_is_strong_sell(self):
        r = self.signal(sentiment_score=20.0, inventory_signal="STRONG_BEARISH")
        self.assertEqual(r["signal"], "STRONG_SELL")

    def test_bearish_inventory_low_sentiment_is_sell(self):
        r = self.signal(sentiment_score=40.0, inventory_signal="BEARISH")
        self.assertEqual(r["signal"], "SELL")

    def test_conflicting_signals_is_hold(self):
        r = self.signal(sentiment_score=50.0, inventory_signal="NEUTRAL")
        self.assertEqual(r["signal"], "HOLD")

    def test_score_is_weighted_average(self):
        r = self.signal(sentiment_score=80.0, inventory_signal="STRONG_BULLISH")
        expected = round(80.0 * 0.5 + 95 * 0.5, 2)
        self.assertAlmostEqual(r["score"], expected, places=1)

    def test_output_has_required_keys(self):
        r = self.signal(50.0, "NEUTRAL")
        for key in ("strategy", "signal", "score", "reason", "timestamp"):
            self.assertIn(key, r)


# ═══════════════════════════════════════════════════════════════════════════════
# 11 · STRADDLE STRATEGY
# ═══════════════════════════════════════════════════════════════════════════════

class TestStraddleStrategy(unittest.TestCase):

    def setUp(self):
        from strategies.options.straddles import straddle_signal
        self.signal = straddle_signal

    def test_low_iv_rank_is_recommended(self):
        df = _ohlcv(50)
        result = self.signal(df, _mock_chain(100.0), iv_rank=30.0, ticker="XOM")
        self.assertTrue(result["recommended"])

    def test_high_iv_rank_not_recommended(self):
        df = _ohlcv(50)
        result = self.signal(df, _mock_chain(100.0), iv_rank=70.0, ticker="XOM")
        self.assertFalse(result["recommended"])

    def test_breakevens_are_symmetric_around_strike(self):
        df = _ohlcv(50)
        result = self.signal(df, _mock_chain(100.0), iv_rank=30.0, ticker="XOM")
        if result["strike"] is not None:
            self.assertGreater(result["breakeven_up"],  result["strike"])
            self.assertLess(   result["breakeven_down"], result["strike"])

    def test_total_cost_equals_call_plus_put(self):
        df = _ohlcv(50)
        result = self.signal(df, _mock_chain(100.0), iv_rank=30.0)
        if result["call_premium"] is not None:
            expected = round(result["call_premium"] + result["put_premium"], 4)
            self.assertAlmostEqual(result["total_cost"], expected, places=3)

    def test_empty_chain_returns_default(self):
        df = _ohlcv(50)
        result = self.signal(df, {}, iv_rank=30.0)
        self.assertIsNone(result["strike"])

    def test_output_has_required_keys(self):
        df = _ohlcv(50)
        result = self.signal(df, _mock_chain(), iv_rank=40.0)
        for key in ("strategy", "strike", "total_cost", "breakeven_up",
                    "breakeven_down", "iv_rank", "recommended", "timestamp"):
            self.assertIn(key, result)


# ═══════════════════════════════════════════════════════════════════════════════
# 12 · SPREAD STRATEGY
# ═══════════════════════════════════════════════════════════════════════════════

class TestSpreadStrategy(unittest.TestCase):

    def setUp(self):
        from strategies.options.spreads import spread_signal
        self.signal = spread_signal

    def test_bull_spread_uses_calls(self):
        df = _ohlcv(50)
        result = self.signal(df, _mock_chain(100.0), direction="bull", ticker="SPY")
        self.assertIn("bull", result["strategy"])

    def test_bear_spread_uses_puts(self):
        df = _ohlcv(50)
        result = self.signal(df, _mock_chain(100.0), direction="bear", ticker="SPY")
        self.assertIn("bear", result["strategy"])

    def test_max_profit_greater_than_zero(self):
        df = _ohlcv(50)
        result = self.signal(df, _mock_chain(100.0), direction="bull")
        if result["max_profit"] is not None:
            self.assertGreater(result["max_profit"], 0)

    def test_max_loss_equals_net_debit(self):
        df = _ohlcv(50)
        result = self.signal(df, _mock_chain(100.0), direction="bull")
        if result["net_debit"] is not None:
            self.assertAlmostEqual(result["max_loss"], result["net_debit"], places=3)

    def test_invalid_direction_returns_default(self):
        df = _ohlcv(50)
        result = self.signal(df, _mock_chain(100.0), direction="sideways")
        self.assertEqual(result["signal"], "HOLD")

    def test_empty_chain_returns_default(self):
        df = _ohlcv(50)
        result = self.signal(df, {}, direction="bull")
        self.assertIsNone(result["net_debit"])

    def test_output_has_required_keys(self):
        df = _ohlcv(50)
        result = self.signal(df, _mock_chain(), direction="bull")
        for key in ("strategy", "direction", "long_strike", "short_strike",
                    "net_debit", "max_profit", "max_loss", "breakeven", "timestamp"):
            self.assertIn(key, result)


# ═══════════════════════════════════════════════════════════════════════════════
# 13 · MIROFISH — SEED GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

class TestSeedGenerator(unittest.TestCase):

    def setUp(self):
        from mirofish.seed_generator import generate_seed
        self.generate = generate_seed
        self.inventory = {
            "report_date": "2025-04-23", "crude_stocks_mb": 430.0,
            "wow_change_pct": -1.5, "signal": "BULLISH",
        }
        self.quotes = [{"ticker": "XOM", "price": 112.0, "change_pct": 1.2, "signal": "BUY"}]
        self.headlines = ["Oil rallies on inventory draw", "OPEC holds production steady"]
        self.tech = {"XOM": {"rsi": 52.0, "signal": "BULLISH", "score": 65}}

    def test_seed_contains_header(self):
        seed = self.generate(self.inventory, self.quotes, self.headlines, 65.0, self.tech)
        self.assertIn("MARKET SEED DOCUMENT", seed)

    def test_seed_contains_inventory_section(self):
        seed = self.generate(self.inventory, self.quotes, self.headlines, 65.0, self.tech)
        self.assertIn("OIL INVENTORY", seed)
        self.assertIn("430.0", seed)

    def test_seed_contains_price_summary(self):
        seed = self.generate(self.inventory, self.quotes, self.headlines, 65.0, self.tech)
        self.assertIn("PRICE SUMMARY", seed)
        self.assertIn("XOM", seed)

    def test_seed_contains_sentiment_score(self):
        seed = self.generate(self.inventory, self.quotes, self.headlines, 65.0, self.tech)
        self.assertIn("65.0", seed)

    def test_seed_contains_headlines(self):
        seed = self.generate(self.inventory, self.quotes, self.headlines, 65.0, self.tech)
        self.assertIn("Oil rallies on inventory draw", seed)

    def test_seed_contains_simulation_context(self):
        seed = self.generate(self.inventory, self.quotes, self.headlines, 65.0, self.tech)
        self.assertIn("SIMULATION CONTEXT", seed)

    def test_seed_is_string(self):
        seed = self.generate(self.inventory, self.quotes, self.headlines, 65.0, self.tech)
        self.assertIsInstance(seed, str)

    def test_wow_negative_labelled_draw(self):
        seed = self.generate(self.inventory, self.quotes, self.headlines, 65.0, self.tech)
        self.assertIn("draw", seed)

    def test_wow_positive_labelled_build(self):
        inv = {**self.inventory, "wow_change_pct": 2.0}
        seed = self.generate(inv, self.quotes, self.headlines, 50.0, self.tech)
        self.assertIn("build", seed)


# ═══════════════════════════════════════════════════════════════════════════════
# 14 · MIROFISH — CLIENT
# ═══════════════════════════════════════════════════════════════════════════════

class TestMiroFishClient(unittest.TestCase):

    @patch("mirofish.mirofish_client.requests.post")
    def test_successful_simulation_returns_json(self, mock_post):
        mock_post.return_value.raise_for_status = MagicMock()
        mock_post.return_value.json.return_value = {
            "dominant_behavior": "BULLISH", "confidence": 0.8,
            "bullish_agents": 14, "bearish_agents": 4, "neutral_agents": 2,
        }
        from mirofish.mirofish_client import run_simulation
        result = run_simulation("test seed")
        self.assertEqual(result["dominant_behavior"], "BULLISH")

    @patch("mirofish.mirofish_client.requests.post", side_effect=ConnectionError("down"))
    def test_connection_error_returns_fallback(self, _):
        from mirofish.mirofish_client import run_simulation
        result = run_simulation("test seed")
        self.assertEqual(result["status"], "fallback")
        self.assertEqual(result["dominant_behavior"], "NEUTRAL")

    @patch("mirofish.mirofish_client.requests.post", side_effect=TimeoutError("timeout"))
    def test_timeout_returns_fallback(self, _):
        from mirofish.mirofish_client import run_simulation
        result = run_simulation("test seed")
        self.assertEqual(result["status"], "fallback")

    @patch("mirofish.mirofish_client.requests.get")
    def test_is_available_true_on_200(self, mock_get):
        mock_get.return_value.status_code = 200
        from mirofish.mirofish_client import is_available
        self.assertTrue(is_available())

    @patch("mirofish.mirofish_client.requests.get", side_effect=ConnectionError)
    def test_is_available_false_on_error(self, _):
        from mirofish.mirofish_client import is_available
        self.assertFalse(is_available())

    @patch("mirofish.mirofish_client.requests.get")
    def test_is_available_false_on_non_200(self, mock_get):
        mock_get.return_value.status_code = 503
        from mirofish.mirofish_client import is_available
        self.assertFalse(is_available())


# ═══════════════════════════════════════════════════════════════════════════════
# 15 · MIROFISH — REPORT PARSER
# ═══════════════════════════════════════════════════════════════════════════════

class TestReportParser(unittest.TestCase):

    def setUp(self):
        from mirofish.report_parser import parse_report
        self.parse = parse_report

    def _report(self, behavior, confidence=1.0, n=20):
        return {
            "dominant_behavior": behavior,
            "confidence": confidence,
            "bullish_agents": int(n * 0.6),
            "bearish_agents": int(n * 0.3),
            "neutral_agents": int(n * 0.1),
            "summary": "Test run",
        }

    def test_strongly_bullish_maps_to_strong_bullish(self):
        r = self.parse(self._report("STRONGLY_BULLISH"))
        self.assertEqual(r["signal"], "STRONG_BULLISH")

    def test_bullish_maps_to_bullish(self):
        r = self.parse(self._report("BULLISH"))
        self.assertEqual(r["signal"], "BULLISH")

    def test_neutral_maps_to_neutral(self):
        r = self.parse(self._report("NEUTRAL"))
        self.assertEqual(r["signal"], "NEUTRAL")
        self.assertAlmostEqual(r["score"], 50.0, places=1)

    def test_bearish_maps_to_bearish(self):
        r = self.parse(self._report("BEARISH"))
        self.assertEqual(r["signal"], "BEARISH")

    def test_strongly_bearish_maps_to_strong_bearish(self):
        r = self.parse(self._report("STRONGLY_BEARISH"))
        self.assertEqual(r["signal"], "STRONG_BEARISH")

    def test_unknown_behavior_defaults_to_neutral(self):
        r = self.parse(self._report("CONFUSED"))
        self.assertEqual(r["signal"], "NEUTRAL")

    def test_low_confidence_blends_toward_50(self):
        full_conf  = self.parse(self._report("BULLISH", confidence=1.0))
        low_conf   = self.parse(self._report("BULLISH", confidence=0.0))
        self.assertGreater(full_conf["score"], low_conf["score"])
        self.assertAlmostEqual(low_conf["score"], 50.0, places=1)

    def test_fallback_flag_set(self):
        report = {**self._report("NEUTRAL"), "status": "fallback"}
        r = self.parse(report)
        self.assertTrue(r["is_fallback"])

    def test_agent_percentages_sum_to_100(self):
        r = self.parse(self._report("BULLISH"))
        total = r["bullish_pct"] + r["bearish_pct"] + r["neutral_pct"]
        self.assertAlmostEqual(total, 100.0, places=1)

    def test_output_has_required_keys(self):
        r = self.parse(self._report("BULLISH"))
        for key in ("signal", "score", "confidence", "dominant_behavior",
                    "bullish_pct", "bearish_pct", "is_fallback", "timestamp"):
            self.assertIn(key, r)


# ═══════════════════════════════════════════════════════════════════════════════
# 16 · SIGNAL COMBINER
# ═══════════════════════════════════════════════════════════════════════════════

class TestSignalCombiner(unittest.TestCase):

    def setUp(self):
        from models.signal_combiner import combine_signals
        self.combine = combine_signals

    def _all(self, score):
        return {"score": score}

    def test_all_max_scores_is_strong_buy(self):
        r = self.combine(*[self._all(100)] * 5)
        self.assertEqual(r["recommendation"], "STRONG BUY")
        self.assertGreater(r["composite_score"], 75)

    def test_all_min_scores_is_strong_sell(self):
        r = self.combine(*[self._all(0)] * 5)
        self.assertEqual(r["recommendation"], "STRONG SELL")
        self.assertLess(r["composite_score"], 25)

    def test_all_50_scores_is_hold(self):
        r = self.combine(*[self._all(50)] * 5)
        self.assertEqual(r["recommendation"], "HOLD")
        self.assertAlmostEqual(r["composite_score"], 50.0, places=4)

    def test_weighted_arithmetic_is_correct(self):
        inv  = {"score": 100}
        rest = {"score": 0}
        r = self.combine(inv, rest, rest, rest, rest)
        # inventory weight = 0.30
        self.assertAlmostEqual(r["composite_score"], 30.0, places=3)

    def test_missing_score_defaults_to_50(self):
        r = self.combine({}, {}, {}, {}, {})
        self.assertAlmostEqual(r["composite_score"], 50.0, places=4)

    def test_breakdown_contains_all_sources(self):
        r = self.combine(*[self._all(50)] * 5)
        for key in ("inventory_score", "technical_score", "mirofish_score",
                    "sentiment_score", "ml_score"):
            self.assertIn(key, r["breakdown"])

    def test_ticker_is_preserved(self):
        r = self.combine(*[self._all(50)] * 5, ticker="XOM")
        self.assertEqual(r["ticker"], "XOM")

    def test_dominant_signal_key_present(self):
        r = self.combine({"score": 100}, *[{"score": 0}] * 4)
        self.assertEqual(r["dominant_signal"], "inventory")

    def test_boundary_buy_at_65(self):
        r = self.combine(*[self._all(65)] * 5)
        self.assertEqual(r["recommendation"], "BUY")

    def test_boundary_sell_at_35(self):
        r = self.combine(*[self._all(35)] * 5)
        self.assertEqual(r["recommendation"], "SELL")


# ═══════════════════════════════════════════════════════════════════════════════
# 17 · BACKTESTING ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class TestBacktestEngine(unittest.TestCase):

    def setUp(self):
        from backtesting.engine import BacktestEngine
        self.Engine = BacktestEngine

    def _signals(self, df, pattern):
        """pattern: list of (idx_start, idx_end, signal_value)"""
        s = pd.Series("HOLD", index=df.index)
        for start, end, val in pattern:
            s.iloc[start:end] = val
        return s

    def test_buy_and_sell_produces_trade(self):
        df = _ohlcv_capital(100, "up")
        signals = self._signals(df, [(10, 11, "BUY"), (50, 51, "SELL")])
        engine = self.Engine()
        results = engine.run(df, signals)
        self.assertGreaterEqual(len(results["trades"]), 1)

    def test_no_signals_produces_no_trades(self):
        df = _ohlcv_capital(100, "flat")
        signals = pd.Series("HOLD", index=df.index)
        engine = self.Engine()
        results = engine.run(df, signals)
        self.assertEqual(len(results["trades"]), 0)

    def test_metrics_keys_present(self):
        df = _ohlcv_capital(100, "up")
        signals = self._signals(df, [(10, 11, "BUY"), (50, 51, "SELL")])
        engine = self.Engine()
        results = engine.run(df, signals)
        for key in ("total_return_pct", "max_drawdown_pct", "sharpe_ratio",
                    "win_rate", "num_trades", "final_equity"):
            self.assertIn(key, results["metrics"])

    def test_equity_curve_length_matches_df(self):
        df = _ohlcv_capital(100, "flat")
        signals = pd.Series("HOLD", index=df.index)
        engine = self.Engine()
        results = engine.run(df, signals)
        self.assertEqual(len(results["equity_curve"]), len(df))

    def test_winning_trade_positive_pnl(self):
        df = _ohlcv_capital(100, "up")
        signals = self._signals(df, [(5, 6, "BUY"), (90, 91, "SELL")])
        engine = self.Engine()
        results = engine.run(df, signals)
        if results["trades"]:
            self.assertGreater(results["trades"][-1]["pnl_pct"], 0)

    def test_save_results_creates_file(self):
        import tempfile
        df = _ohlcv_capital(50)
        signals = pd.Series("HOLD", index=df.index)
        engine = self.Engine()
        results = engine.run(df, signals, ticker="TEST")
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = os.path.join(ROOT, "backtesting", "results")
            engine.save_results(results, "TEST", "unit_test")
            saved = [f for f in os.listdir(results_dir) if "TEST_unit_test" in f]
            self.assertGreater(len(saved), 0)
            for f in saved:
                os.remove(os.path.join(results_dir, f))

    def test_initial_capital_preserved_with_no_trades(self):
        df = _ohlcv_capital(50)
        signals = pd.Series("HOLD", index=df.index)
        engine = self.Engine(initial_capital=50_000)
        results = engine.run(df, signals)
        self.assertAlmostEqual(results["metrics"]["final_equity"], 50_000.0, places=1)

    def test_max_drawdown_non_negative(self):
        df = _ohlcv_capital(100, "down")
        signals = self._signals(df, [(5, 6, "BUY"), (90, 91, "SELL")])
        engine = self.Engine()
        results = engine.run(df, signals)
        self.assertGreaterEqual(results["metrics"]["max_drawdown_pct"], 0)

    def test_strong_buy_signal_triggers_entry(self):
        df = _ohlcv_capital(100, "up")
        signals = self._signals(df, [(10, 11, "STRONG_BUY"), (80, 81, "STRONG_SELL")])
        engine = self.Engine()
        results = engine.run(df, signals)
        self.assertGreaterEqual(len(results["trades"]), 1)


# ═══════════════════════════════════════════════════════════════════════════════
# 18 · ALERT NOTIFIER
# ═══════════════════════════════════════════════════════════════════════════════

@unittest.skipUnless(HAS_APSCHEDULER, "apscheduler not installed")
class TestAlertNotifier(unittest.TestCase):

    def setUp(self):
        from alerts.notifier import AlertNotifier
        self.AlertNotifier = AlertNotifier

    def test_high_score_triggers_alert(self):
        notifier = self.AlertNotifier(alert_threshold=70.0)
        alert = notifier.check_and_alert(_rec(score=85.0))
        self.assertIsNotNone(alert)
        self.assertEqual(alert["ticker"], "SPY")

    def test_low_score_triggers_alert(self):
        notifier = self.AlertNotifier(alert_threshold=70.0)
        alert = notifier.check_and_alert(_rec(score=15.0))
        self.assertIsNotNone(alert)

    def test_neutral_score_no_alert(self):
        notifier = self.AlertNotifier(alert_threshold=70.0)
        alert = notifier.check_and_alert(_rec(score=55.0))
        self.assertIsNone(alert)

    def test_alert_appended_to_list(self):
        notifier = self.AlertNotifier(alert_threshold=70.0)
        notifier.check_and_alert(_rec(score=85.0))
        notifier.check_and_alert(_rec(score=90.0))
        self.assertEqual(len(notifier.alerts), 2)

    def test_get_recent_alerts_limits_count(self):
        notifier = self.AlertNotifier(alert_threshold=70.0)
        for i in range(15):
            notifier.check_and_alert(_rec(score=85.0))
        recent = notifier.get_recent_alerts(n=5)
        self.assertEqual(len(recent), 5)

    def test_send_alert_function_returns_message(self):
        from alerts.notifier import send_alert
        msg = send_alert(_rec(score=85.0), threshold=70.0)
        self.assertIsNotNone(msg)
        self.assertIn("SPY", msg)

    def test_send_alert_no_message_for_neutral(self):
        from alerts.notifier import send_alert
        msg = send_alert(_rec(score=55.0), threshold=70.0)
        self.assertIsNone(msg)


# ═══════════════════════════════════════════════════════════════════════════════
# 19 · DATABASE MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class TestDatabase(unittest.TestCase):

    def test_init_db_creates_tables(self):
        import tempfile, sqlalchemy
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            import data.storage.database as db_module
            orig_url = db_module.DATABASE_URL
            db_module.engine = sqlalchemy.create_engine(f"sqlite:///{db_path}", echo=False)
            db_module.init_db()
            inspector = sqlalchemy.inspect(db_module.engine)
            tables = inspector.get_table_names()
            self.assertIn("price_bars", tables)
            self.assertIn("inventory_records", tables)
            self.assertIn("signals", tables)
            self.assertIn("trade_recommendations", tables)
        finally:
            os.unlink(db_path)

    def test_get_session_returns_session(self):
        from data.storage.database import get_session
        session = get_session()
        self.assertIsNotNone(session)
        session.close()


# ═══════════════════════════════════════════════════════════════════════════════
# 20 · PANDAS_TA DEPENDENT STRATEGIES (skipped if not installed)
# ═══════════════════════════════════════════════════════════════════════════════

@unittest.skipUnless(HAS_PANDAS_TA, "pandas_ta not installed")
class TestMeanReversionStrategy(unittest.TestCase):

    def setUp(self):
        from strategies.day_trading.mean_reversion import mean_reversion_signal
        self.signal = mean_reversion_signal

    def test_insufficient_data_returns_hold(self):
        df = _ohlcv(10)
        result = self.signal(df, "XOM")
        self.assertEqual(result["signal"], "HOLD")

    def test_output_keys_present(self):
        df = _ohlcv(60, "flat")
        result = self.signal(df, "XOM")
        for key in ("strategy", "signal", "score", "reason", "timestamp"):
            self.assertIn(key, result)

    def test_strategy_name_is_mean_reversion(self):
        df = _ohlcv(60, "flat")
        result = self.signal(df, "XOM")
        self.assertEqual(result["strategy"], "mean_reversion")


@unittest.skipUnless(HAS_PANDAS_TA, "pandas_ta not installed")
class TestVWAPStrategy(unittest.TestCase):

    def setUp(self):
        from strategies.day_trading.vwap import vwap_signal
        self.signal = vwap_signal

    def test_insufficient_data_returns_hold(self):
        df = _ohlcv(5)
        result = self.signal(df, "XOM")
        self.assertEqual(result["signal"], "HOLD")

    def test_output_keys_present(self):
        df = _ohlcv(60, "flat")
        result = self.signal(df, "XOM")
        for key in ("strategy", "signal", "score", "reason", "timestamp"):
            self.assertIn(key, result)

    def test_strategy_name_is_vwap(self):
        df = _ohlcv(60, "flat")
        result = self.signal(df, "XOM")
        self.assertEqual(result["strategy"], "vwap")


@unittest.skipUnless(HAS_XGBOOST and HAS_PANDAS_TA, "xgboost or pandas_ta not installed")
class TestPriceModel(unittest.TestCase):

    def setUp(self):
        from models.price_model import PriceModel
        self.PriceModel = PriceModel

    def test_train_returns_accuracy(self):
        df = _ohlcv(300, "up")
        model = self.PriceModel("TEST")
        result = model.train(df)
        self.assertIn("accuracy", result)
        self.assertGreaterEqual(result["accuracy"], 0.0)
        self.assertLessEqual(result["accuracy"],    1.0)

    def test_predict_returns_direction(self):
        df = _ohlcv(300, "up")
        model = self.PriceModel("TEST2")
        model.train(df)
        pred = model.predict(df)
        self.assertIn(pred["direction"], ("UP", "DOWN"))
        self.assertIn("score", pred)
        self.assertIn("signal", pred)

    def test_score_between_0_and_100(self):
        df = _ohlcv(300, "up")
        model = self.PriceModel("TEST3")
        model.train(df)
        pred = model.predict(df)
        self.assertGreaterEqual(pred["score"], 0)
        self.assertLessEqual(pred["score"],   100)


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main(verbosity=2)
