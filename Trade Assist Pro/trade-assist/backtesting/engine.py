import pandas as pd
import numpy as np
import json
from datetime import datetime, timezone
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import BACKTEST_INITIAL_CAPITAL, BACKTEST_COMMISSION

BUY_SIGNALS  = {"BUY", "STRONG BUY", "STRONG_BUY"}
SELL_SIGNALS = {"SELL", "STRONG SELL", "STRONG_SELL"}


class BacktestEngine:
    def __init__(
        self,
        initial_capital: float = BACKTEST_INITIAL_CAPITAL,
        commission: float = BACKTEST_COMMISSION,
    ):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.commission = commission
        self.trades = []
        self.equity_curve = []

    def run(self, df: pd.DataFrame, signals: pd.Series, ticker: str = "") -> dict:
        self.capital = self.initial_capital
        self.trades = []
        self.equity_curve = []

        position = None
        entry_price = 0.0
        entry_date = None
        shares = 0.0

        for date, row in df.iterrows():
            sig = str(signals.get(date, "HOLD")).upper()
            close = float(row["Close"])

            if position is None and sig in BUY_SIGNALS:
                invest = self.capital * 0.95
                cost = invest * self.commission
                shares = (invest - cost) / close
                entry_price = close
                entry_date = date
                self.capital -= invest
                position = "LONG"

            elif position == "LONG" and sig in SELL_SIGNALS:
                proceeds = shares * close
                cost = proceeds * self.commission
                net = proceeds - cost
                pnl_pct = ((close - entry_price) / entry_price) * 100 if entry_price else 0.0
                self.capital += net
                self.trades.append({
                    "entry_date": str(entry_date),
                    "exit_date": str(date),
                    "entry_price": entry_price,
                    "exit_price": close,
                    "shares": shares,
                    "pnl_pct": round(pnl_pct, 4),
                    "net_proceeds": round(net, 4),
                })
                position = None
                shares = 0.0

            current_equity = self.capital + (shares * close if position == "LONG" else 0.0)
            self.equity_curve.append({"date": str(date), "equity": round(current_equity, 4)})

        if position == "LONG":
            last_close = float(df["Close"].iloc[-1])
            proceeds = shares * last_close
            cost = proceeds * self.commission
            net = proceeds - cost
            pnl_pct = ((last_close - entry_price) / entry_price) * 100 if entry_price else 0.0
            self.capital += net
            self.trades.append({
                "entry_date": str(entry_date),
                "exit_date": str(df.index[-1]),
                "entry_price": entry_price,
                "exit_price": last_close,
                "shares": shares,
                "pnl_pct": round(pnl_pct, 4),
                "net_proceeds": round(net, 4),
            })

        metrics = self.calculate_metrics()
        return {
            "ticker": ticker,
            "metrics": metrics,
            "trades": self.trades,
            "equity_curve": self.equity_curve,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def calculate_metrics(self) -> dict:
        final_equity = self.capital
        initial = self.initial_capital

        total_return_pct = ((final_equity - initial) / initial * 100) if initial else 0.0

        equities = [e["equity"] for e in self.equity_curve]
        n_days = len(equities)
        years = n_days / 252 if n_days > 0 else 1.0
        if years > 0 and initial > 0:
            annualised_return_pct = ((final_equity / initial) ** (1 / years) - 1) * 100
        else:
            annualised_return_pct = 0.0

        max_drawdown_pct = 0.0
        if equities:
            peak = equities[0]
            for eq in equities:
                if eq > peak:
                    peak = eq
                dd = ((peak - eq) / peak * 100) if peak else 0.0
                if dd > max_drawdown_pct:
                    max_drawdown_pct = dd

        sharpe_ratio = 0.0
        if len(equities) > 1:
            eq_series = pd.Series(equities)
            daily_returns = eq_series.pct_change().dropna()
            excess = daily_returns - (0.02 / 252)
            std = excess.std()
            sharpe_ratio = float((excess.mean() / std) * (252 ** 0.5)) if std > 0 else 0.0

        num_trades = len(self.trades)
        pnl_pcts = [t["pnl_pct"] for t in self.trades]
        wins = [p for p in pnl_pcts if p > 0]
        win_rate = (len(wins) / num_trades * 100) if num_trades else 0.0
        avg_trade_pct = float(np.mean(pnl_pcts)) if pnl_pcts else 0.0
        best_trade_pct = float(max(pnl_pcts)) if pnl_pcts else 0.0
        worst_trade_pct = float(min(pnl_pcts)) if pnl_pcts else 0.0

        return {
            "total_return_pct":      round(total_return_pct,      4),
            "annualised_return_pct": round(annualised_return_pct, 4),
            "max_drawdown_pct":      round(max_drawdown_pct,      4),
            "sharpe_ratio":          round(sharpe_ratio,          4),
            "win_rate":              round(win_rate,              4),
            "num_trades":            num_trades,
            "avg_trade_pct":         round(avg_trade_pct,         4),
            "best_trade_pct":        round(best_trade_pct,        4),
            "worst_trade_pct":       round(worst_trade_pct,       4),
            "final_equity":          round(final_equity,          4),
        }

    def save_results(self, results: dict, ticker: str, strategy: str):
        out_dir = os.path.join(os.path.dirname(__file__), "results")
        os.makedirs(out_dir, exist_ok=True)
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        filename = f"{ticker}_{strategy}_{date_str}.json"
        path = os.path.join(out_dir, filename)
        with open(path, "w") as f:
            json.dump(results, f, indent=2, default=str)


def run_backtest(
    df: pd.DataFrame,
    signals: pd.Series,
    ticker: str,
    strategy: str,
) -> dict:
    engine = BacktestEngine()
    results = engine.run(df, signals, ticker=ticker)
    engine.save_results(results, ticker, strategy)
    return results
