# 🛢️ Trade Assist Pro
### AI-Powered Trading Intelligence Platform

> Combining real-time market data, oil inventory signals, multi-agent behavioral simulation, and machine learning to generate day trading and options strategy recommendations across stocks, ETFs, futures, and crypto.

[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-red?style=flat-square&logo=streamlit)](https://streamlit.io)
[![MiroFish](https://img.shields.io/badge/Simulation-MiroFish-green?style=flat-square)](https://github.com/666ghj/MiroFish)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Status](https://img.shields.io/badge/Status-In%20Development-orange?style=flat-square)]()

> ⚠️ **Disclaimer:** This is a portfolio and research project built for educational purposes. It is **not financial advice**. Never trade real money based solely on any automated system. Options trading and day trading carry significant risk of loss..

---

## 📌 Table of Contents

- [What It Does](#-what-it-does)
- [Architecture](#-architecture)
- [Markets Covered](#-markets-covered)
- [Trading Strategies](#-trading-strategies)
- [Options Strategies](#-options-strategies)
- [Data Sources](#-data-sources)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Dashboard Preview](#-dashboard-preview)
- [Build Phases](#-build-phases)
- [API Keys Required](#-api-keys-required)
- [Author](#-author)

---

## 🎯 What It Does

Trade Assist Pro is a **full-stack AI trading intelligence platform** that solves one core problem:

> *"Markets move because of data AND human behavior. Most tools only model the data. Trade Assist models both."*

### The Three Questions It Answers

```
1. "What is actually happening in the market right now?"
   → Answered by: Real-time data pipeline (6 sources)

2. "How will traders and investors REACT to this?"
   → Answered by: MiroFish multi-agent behavioral simulation

3. "What trading opportunity does this create?"
   → Answered by: Day trading + options strategy engine
```

### What Makes It Different

| Traditional Tools | Trade Assist Pro |
|---|---|
| Price data only | Price + behavior simulation |
| Generic signals | Oil inventory as core signal |
| Single strategy | 4 day trading + 4 options strategies |
| Static charts | AI-generated strategy recommendations |
| No context | MiroFish explains WHY the move happens |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TRADE ASSIST PRO                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  LAYER 1 — DATA INGESTION                                   │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │  EIA.gov │  NASDAQ  │ Finance  │  Motley  │Investop- │  │
│  │Inventory │  Prices  │  Charts  │   Fool   │  edia    │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
│                           ↓                                  │
│  LAYER 2 — SIGNAL PROCESSING                                │
│  ┌──────────────┬─────────────────┬──────────────────────┐  │
│  │  Inventory   │    Technical    │      Sentiment       │  │
│  │   Signal     │  (RSI/MACD/     │  (News + Analyst)    │  │
│  │ (Core ⭐)    │  VWAP/BB)       │                      │  │
│  └──────────────┴─────────────────┴──────────────────────┘  │
│                           ↓                                  │
│  LAYER 3 — STRATEGY ENGINE                                  │
│  ┌─────────────────────────┬───────────────────────────┐    │
│  │    DAY TRADING          │       OPTIONS             │    │
│  │  • Momentum             │  • Calls & Puts           │    │
│  │  • Mean Reversion       │  • Covered Calls          │    │
│  │  • VWAP                 │  • Straddles/Strangles    │    │
│  │  • News-Based           │  • Bull/Bear Spreads      │    │
│  └─────────────────────────┴───────────────────────────┘    │
│                           ↓                                  │
│  LAYER 4 — MIROFISH BEHAVIORAL SIMULATION                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Auto-generated seed → 20 AI agents × 10 rounds     │    │
│  │  Agent types: Oil traders, Hedge funds, Retail,      │    │
│  │  Short sellers, Analysts, Media                      │    │
│  └─────────────────────────────────────────────────────┘    │
│                           ↓                                  │
│  LAYER 5 — PREDICTION & RECOMMENDATION                      │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Combined Signal Score → BUY / SELL / HOLD          │    │
│  │  Specific Strategy Recommendation + Payoff Diagram  │    │
│  └─────────────────────────────────────────────────────┘    │
│                           ↓                                  │
│  LAYER 6 — STREAMLIT DASHBOARD                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Live Charts │ Signals │ Options │ MiroFish Report  │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Markets Covered

| Market | Tickers | Data Source | Update Frequency |
|--------|---------|-------------|-----------------|
| **Broad Market** | SPY, QQQ | NASDAQ + yfinance | Real-time |
| **Oil Stocks** | XOM, CVX, OXY | NASDAQ + yfinance | Real-time |
| **Oil Futures/ETFs** | USO, CL=F | NASDAQ + yfinance | Real-time |
| **Crypto** | BTC, ETH | CCXT (multiple exchanges) | Real-time |
| **Oil Inventory** | US Crude Stocks | EIA.gov API | Weekly (Wed) |

---

## 📈 Day Trading Strategies

### 1. 🚀 Momentum (Breakout Trading)
```
Logic:   Price breaks key level with high volume → follow the move
Signal:  🟢 BUY  — breaks above resistance on 2x+ average volume
         🔴 SELL — breaks below support on 2x+ average volume
Best on: Trending markets, post-news events
Risk:    False breakouts (whipsaws)
```

### 2. 🔄 Mean Reversion (Buy the Dip)
```
Logic:   Price deviates too far from average → expect snap-back
Signal:  🟢 BUY  — RSI < 30, price at lower Bollinger Band
         🔴 SELL — RSI > 70, price at upper Bollinger Band
Best on: Sideways/ranging markets
Risk:    Catching falling knives in strong downtrends
```

### 3. 🏦 VWAP Strategy (Institutional Levels)
```
Logic:   Institutions use VWAP as benchmark — trade around it
Signal:  🟢 BUY  — price reclaims VWAP from below
         🔴 SELL — price loses VWAP from above
Best on: Intraday trading, all markets
Risk:    Less effective at market open/close
```

### 4. 📰 News-Based (Event Driven)
```
Logic:   Known events create predictable volatility
Signal:  Pre-position before EIA reports, Fed meetings, earnings
         Trade the reaction after announcement
Key dates: EIA every Wednesday 10:30 AM ET
           OPEC meetings (scheduled)
           Fed meetings (scheduled)
Risk:    News can surprise in either direction
```

---

## 🎯 Options Strategies

### 1. 📞 Buying Calls & Puts (Directional)
```
When:    High conviction directional trade
CALL:    Buy when bullish — right to BUY at strike price
PUT:     Buy when bearish — right to SELL at strike price
Risk:    Limited to premium paid
Reward:  Unlimited (calls) / Large (puts)

Example: XOM at $112 → Buy $115 Call expiring 2 weeks
         If XOM → $120: +120% profit
         If XOM stays: lose premium paid
```

### 2. 💰 Covered Calls (Income Generation)
```
When:    Own 100 shares, want regular income
Logic:   Sell someone the right to buy your shares at higher price
         Collect premium immediately regardless of outcome
Risk:    Capped upside on owned shares
Reward:  Regular premium income (like dividends)

Example: Own 100 XOM at $112 → Sell $115 Call for $2.00
         Collect $200/month regardless
         Shares called away only if XOM > $115
```

### 3. ⚡ Straddles & Strangles (Volatility Plays)
```
When:    Big move expected but direction uncertain
         Perfect for: EIA reports, earnings, Fed days
STRADDLE: Buy call + put at SAME strike
STRANGLE: Buy call + put at DIFFERENT strikes (cheaper)
Risk:    Cost of both options
Reward:  Profits if price moves big in EITHER direction

Example: USO before EIA report
         Buy $78 Call + $78 Put (straddle) for $3.50
         If USO moves > 4.5% either way → profit
```

### 4. 📐 Spreads (Bull/Bear)
```
When:    Directional but want to reduce cost
BULL CALL SPREAD: Buy lower call + Sell higher call
BEAR PUT SPREAD:  Buy higher put + Sell lower put
Risk:    Limited to premium paid
Reward:  Limited to spread width minus premium

Example: SPY Bull Call Spread
         Buy $480 Call + Sell $490 Call
         Max profit: $10 | Max loss: premium paid
```

---

## 🛢️ Oil Inventory Signal (Core Signal)

The heartbeat of the entire system:

```
📦 INVENTORY DRAW (tanks emptying)
   → Supply < Demand
   → 🟢 BULLISH for oil prices
   → Buy USO calls, XOM/CVX/OXY long

📦 INVENTORY BUILD (tanks filling)
   → Supply > Demand
   → 🔴 BEARISH for oil prices
   → Buy USO puts, energy stocks short

Signal Levels:
  STRONG_BULLISH  → Draw > 2% WoW
  BULLISH         → Draw 0.5-2% WoW
  NEUTRAL         → Change < 0.5% WoW
  BEARISH         → Build 0.5-2% WoW
  STRONG_BEARISH  → Build > 2% WoW

Released: Every Wednesday 10:30 AM ET by EIA
```

---

## 📡 Data Sources

| Source | Data Type | Cost | Update |
|--------|-----------|------|--------|
| [EIA.gov](https://www.eia.gov/opendata/) | Oil inventory | Free | Weekly |
| [NASDAQ](https://www.nasdaq.com) | Stock prices & news | Free | Real-time |
| [FinanceCharts](https://www.financecharts.com) | Financial ratios | Free | Daily |
| [FreeFinancials](https://home.freefinancials.com) | Balance sheets | Free | Quarterly |
| [Motley Fool](https://www.fool.com) | Analyst sentiment | Free | Daily |
| [Investopedia](https://www.investopedia.com) | Market context | Free | Daily |
| [yfinance](https://pypi.org/project/yfinance/) | OHLCV + options | Free | Real-time |
| [CCXT](https://ccxt.readthedocs.io) | Crypto prices | Free | Real-time |
| [MiroFish](https://github.com/666ghj/MiroFish) | Agent simulation | Self-hosted | On demand |

---

## 🛠️ Tech Stack

```
Language:         Python 3.11+
Dashboard:        Streamlit + Plotly
Market Data:      yfinance, CCXT
Scraping:         BeautifulSoup4, Playwright
Technical Analysis: pandas-ta
ML Model:         XGBoost + scikit-learn
Agent Simulation: MiroFish (local)
LLM Backbone:     Groq (LLaMA 3.1)
Memory Graph:     Zep Cloud
Scheduling:       APScheduler
Database:         SQLAlchemy + SQLite
Config:           python-dotenv
```

---

## 📂 Project Structure

```
trade-assist/
│
├── 📁 data/
│   ├── scrapers/
│   │   ├── eia_scraper.py           # Oil inventory (core ⭐)
│   │   ├── nasdaq_scraper.py        # Stock prices & news
│   │   ├── financecharts_scraper.py # Financial ratios
│   │   ├── freefinancials_scraper.py# Balance sheet data
│   │   ├── investopedia_scraper.py  # Market context
│   │   ├── fool_scraper.py          # Analyst sentiment
│   │   ├── options_scraper.py       # Options chain data
│   │   ├── crypto_scraper.py        # BTC, ETH prices
│   │   └── news_scraper.py          # Breaking news feed
│   │
│   ├── processors/
│   │   ├── inventory_signal.py      # EIA → trading signal
│   │   ├── technical_signal.py      # RSI/MACD/VWAP/BB
│   │   └── sentiment_signal.py      # News sentiment scoring
│   │
│   └── storage/
│       └── database.py              # SQLAlchemy models
│
├── 📁 strategies/
│   ├── day_trading/
│   │   ├── momentum.py              # Breakout detection
│   │   ├── mean_reversion.py        # Oversold/overbought
│   │   ├── vwap.py                  # VWAP reclaim trades
│   │   └── news_based.py            # Event-driven signals
│   │
│   └── options/
│       ├── calls_puts.py            # Directional options
│       ├── covered_calls.py         # Income generation
│       ├── straddles.py             # Volatility plays
│       └── spreads.py               # Bull/Bear spreads
│
├── 📁 mirofish/
│   ├── seed_generator.py            # Auto-build seed docs
│   ├── mirofish_client.py           # MiroFish API client
│   └── report_parser.py             # Parse simulation output
│
├── 📁 models/
│   ├── price_model.py               # XGBoost price prediction
│   └── signal_combiner.py           # Combine all signals → final call
│
├── 📁 dashboard/
│   ├── app.py                       # Main Streamlit entry point
│   ├── pages/
│   │   ├── 1_markets.py             # Live market overview
│   │   ├── 2_day_trading.py         # Day trading signals
│   │   ├── 3_options.py             # Options strategies
│   │   └── 4_oil_intel.py           # Oil intelligence
│   └── components/
│       ├── charts.py                # Reusable Plotly charts
│       ├── options_payoff.py        # P&L payoff diagrams
│       └── signal_card.py           # Signal display cards
│
├── 📁 backtesting/
│   ├── engine.py                    # Strategy backtester
│   └── results/                     # Backtest output storage
│
├── 📁 alerts/
│   └── notifier.py                  # Signal alert system
│
├── 📁 tests/
│   └── ...                          # Unit + integration tests
│
├── 📄 config.py                     # Centralized config
├── 📄 requirements.txt              # Python dependencies
├── 📄 .env.example                  # API key template
├── 📄 .gitignore
└── 📄 README.md
```

---

## 🚀 Quick Start

### Prerequisites
```bash
# Required versions
Python  >= 3.11
Node.js >= 18     # For MiroFish
uv                # Python package manager
```

### 1. Clone The Repository
```bash
git clone https://github.com/Krsna-Code/trade-assist.git
cd trade-assist
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Configure Environment
```bash
cp .env.example .env
# Open .env and fill in your API keys
```

### 4. Start MiroFish (Required)
```bash
# In a separate terminal, from your MiroFish directory:
cd ../MiroFish
npm run dev
# MiroFish API will run on http://localhost:5001
```

### 5. Launch Dashboard
```bash
streamlit run dashboard/app.py
# Opens at http://localhost:8501
```

---

## 🔑 API Keys Required

| Service | Where To Get | Cost | Required |
|---------|-------------|------|----------|
| **EIA API** | [eia.gov/opendata/register.php](https://www.eia.gov/opendata/register.php) | Free | ✅ Yes |
| **Groq (LLM)** | [console.groq.com](https://console.groq.com) | Free tier | ✅ Yes |
| **Zep Cloud** | [app.getzep.com](https://app.getzep.com) | Free tier | ✅ Yes |
| **NewsAPI** | [newsapi.org/register](https://newsapi.org/register) | Free (100/day) | ✅ Yes |
| **Alpaca** | [alpaca.markets](https://alpaca.markets) | Free (paper) | ⚡ Optional |

---

## 📅 Build Phases

```
✅ PHASE 0 — Project Setup (Complete)
   └── Repo structure, config, README

🔨 PHASE 1 — Data Pipeline (In Progress)
   └── All scrapers + live market data

⏳ PHASE 2 — Day Trading Engine
   └── 4 strategy signal generators

⏳ PHASE 3 — Options Engine
   └── Chain data + payoff diagrams + Greeks

⏳ PHASE 4 — MiroFish Integration
   └── Auto simulation + behavioral signals

⏳ PHASE 5 — Full Dashboard
   └── All 4 pages + backtesting + alerts
```

---

## 📊 Signal Weighting System

```
Final Recommendation = Weighted combination of:

┌──────────────────────────────────┬────────┐
│ Signal Source                    │ Weight │
├──────────────────────────────────┼────────┤
│ 🛢️  Oil Inventory (EIA)          │  30%   │
│ 📈  Technical (RSI/MACD/VWAP)    │  25%   │
│ 🤖  MiroFish Behavioral          │  25%   │
│ 📰  News Sentiment               │  10%   │
│ 🤖  ML Price Model (XGBoost)     │  10%   │
└──────────────────────────────────┴────────┘

Output:
🟢 STRONG BUY  — Score > 75
🟢 BUY         — Score 60-75
🟡 HOLD        — Score 40-60
🔴 SELL        — Score 25-40
🔴 STRONG SELL — Score < 25
```

---

## 🧠 How MiroFish Integration Works

```
Step 1: All scraped data compiled into seed document
        (prices + inventory + news + sentiment)

Step 2: Seed sent to MiroFish running on localhost:5001

Step 3: MiroFish spawns 20 AI agents:
        • Institutional oil traders (5 agents)
        • Retail investors (5 agents)
        • Short sellers (3 agents)
        • Energy analysts (3 agents)
        • Financial media (2 agents)
        • OPEC watchers (2 agents)

Step 4: Agents run 10 rounds of interaction
        Each round: read news → form opinion → interact

Step 5: Dominant behavior pattern extracted
        → Converted to directional signal

Step 6: Behavioral signal combined with technical signals
        → Final trade recommendation generated
```

---

## 💼 Skills Demonstrated

This project demonstrates proficiency in:

```
Data Engineering:
  ✅ Multi-source data pipelines
  ✅ Web scraping (static + dynamic)
  ✅ API integration
  ✅ Data cleaning + processing
  ✅ Scheduled automation

AI/ML Engineering:
  ✅ LLM integration (OpenAI SDK pattern)
  ✅ Multi-agent systems (MiroFish/OASIS)
  ✅ Prompt engineering
  ✅ Feature engineering
  ✅ XGBoost time-series modeling

Financial Domain:
  ✅ Technical analysis
  ✅ Options pricing concepts
  ✅ Alternative data (oil inventory)
  ✅ Market microstructure

Software Engineering:
  ✅ Clean architecture (layered design)
  ✅ Configuration management
  ✅ Environment variable security
  ✅ Modular, testable code
  ✅ Professional documentation
```

---

## 👨‍💻 Author

**Krsna Yenugula**
Senior Machine Learning Engineer
*Financial Services | AI Systems | Data Infrastructure*

[![GitHub](https://img.shields.io/badge/GitHub-Krsna--Code-black?style=flat-square&logo=github)](https://github.com/Krsna-Code)

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built with curiosity, caffeine, and a belief that markets are fundamentally human.*
