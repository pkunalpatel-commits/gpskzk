from sqlalchemy import create_engine, String, Integer, Float, DateTime, Boolean, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from .config import DATABASE_URL

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

class Snapshot(Base):
    __tablename__ = "snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contract_key: Mapped[str] = mapped_column(String(160), index=True)
    underlying: Mapped[str] = mapped_column(String(30))
    expiry: Mapped[str] = mapped_column(String(20))
    strike: Mapped[int] = mapped_column(Integer)
    option_type: Mapped[str] = mapped_column(String(2))
    timestamp: Mapped[object] = mapped_column(DateTime(timezone=True), index=True)
    ltp: Mapped[float] = mapped_column(Float)
    oi: Mapped[int] = mapped_column(Integer)
    volume: Mapped[int] = mapped_column(Integer, default=0)
    source: Mapped[str] = mapped_column(String(40), default="provider")

class OiEvent(Base):
    __tablename__ = "oi_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contract_key: Mapped[str] = mapped_column(String(160), index=True)
    underlying: Mapped[str] = mapped_column(String(30))
    expiry: Mapped[str] = mapped_column(String(20))
    strike: Mapped[int] = mapped_column(Integer)
    option_type: Mapped[str] = mapped_column(String(2))
    timestamp: Mapped[object] = mapped_column(DateTime(timezone=True), index=True)
    ltp_at_event: Mapped[float] = mapped_column(Float)
    premium_bucket: Mapped[float] = mapped_column(Float)
    delta_oi: Mapped[int] = mapped_column(Integer)
    fresh_oi: Mapped[int] = mapped_column(Integer)
    unwinding: Mapped[int] = mapped_column(Integer)

class Candle(Base):
    __tablename__ = "candles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contract_key: Mapped[str] = mapped_column(String(160), index=True)
    timestamp: Mapped[object] = mapped_column(DateTime(timezone=True), index=True)
    interval: Mapped[str] = mapped_column(String(8))
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[int] = mapped_column(Integer, default=0)

class TradePrint(Base):
    __tablename__ = "trade_prints"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contract_key: Mapped[str] = mapped_column(String(160), index=True)
    timestamp: Mapped[object] = mapped_column(DateTime(timezone=True), index=True)
    price: Mapped[float] = mapped_column(Float)
    quantity: Mapped[int] = mapped_column(Integer)
    aggressor: Mapped[str] = mapped_column(String(10))
    source: Mapped[str] = mapped_column(String(40))

def init_db():
    Base.metadata.create_all(bind=engine)
