from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
from config import DATABASE_URL

Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)


class PriceBar(Base):
    __tablename__ = "price_bars"
    id        = Column(Integer, primary_key=True)
    ticker    = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open      = Column(Float)
    high      = Column(Float)
    low       = Column(Float)
    close     = Column(Float)
    volume    = Column(Float)


class InventoryRecord(Base):
    __tablename__ = "inventory_records"
    id              = Column(Integer, primary_key=True)
    report_date     = Column(DateTime, nullable=False, index=True)
    crude_stocks_mb = Column(Float)   # million barrels
    wow_change_mb   = Column(Float)
    wow_change_pct  = Column(Float)
    signal          = Column(String(20))
    fetched_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Signal(Base):
    __tablename__ = "signals"
    id             = Column(Integer, primary_key=True)
    ticker         = Column(String(20), nullable=False, index=True)
    timestamp      = Column(DateTime, nullable=False, index=True)
    signal_type    = Column(String(30))   # inventory / technical / sentiment / mirofish / ml
    direction      = Column(String(20))   # STRONG_BUY / BUY / HOLD / SELL / STRONG_SELL
    score          = Column(Float)
    metadata_json  = Column(Text)


class TradeRecommendation(Base):
    __tablename__ = "trade_recommendations"
    id              = Column(Integer, primary_key=True)
    ticker          = Column(String(20), nullable=False)
    timestamp       = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    strategy        = Column(String(50))
    direction       = Column(String(20))
    composite_score = Column(Float)
    entry_price     = Column(Float)
    target_price    = Column(Float)
    stop_loss       = Column(Float)
    notes           = Column(Text)


class NewsArticle(Base):
    __tablename__ = "news_articles"
    id           = Column(Integer, primary_key=True)
    published_at = Column(DateTime, index=True)
    source       = Column(String(100))
    title        = Column(Text)
    url          = Column(Text)
    sentiment    = Column(Float)   # -1.0 to 1.0
    fetched_at   = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def init_db():
    Base.metadata.create_all(engine)


def get_session():
    return Session()


if __name__ == "__main__":
    init_db()
    print("Database initialised.")
