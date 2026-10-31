from fastapi import FastAPI, HTTPException
from sqlalchemy import select, desc
from .db import init_db, SessionLocal, Candle, TradePrint
from .models import SnapshotIn, CandleIn, TradePrintIn
from .engine import ingest_snapshot, contract_profile, strike_profile
from .providers.dhan import status as dhan_status

app = FastAPI(title="NIFTY OI Premium Profile API", version="0.1.0")

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok", "service": "nifty-oi-profile"}

@app.get("/api/v1/provider/status")
def provider_status():
    return dhan_status().__dict__

@app.post("/api/v1/snapshots")
def add_snapshot(s: SnapshotIn):
    try:
        return ingest_snapshot(s)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/api/v1/profile/contract")
def get_contract_profile(contract_key: str, bucket_size: float = 10.0):
    if bucket_size <= 0:
        raise HTTPException(400, "bucket_size must be positive")
    return contract_profile(contract_key, bucket_size)

@app.get("/api/v1/profile/strikes")
def get_strike_profile(underlying: str = "NIFTY", expiry: str = "", bucket_size: float = 10.0):
    if not expiry:
        raise HTTPException(400, "expiry is required")
    return {"underlying": underlying, "expiry": expiry,
            "items": strike_profile(underlying, expiry, bucket_size)}

@app.post("/api/v1/candles")
def add_candle(c: CandleIn):
    db = SessionLocal()
    try:
        db.add(Candle(**c.model_dump()))
        db.commit()
        return {"stored": True}
    finally:
        db.close()

@app.get("/api/v1/candles")
def get_candles(contract_key: str, interval: str = "1m", limit: int = 500):
    db = SessionLocal()
    try:
        rows = db.scalars(select(Candle).where(
            Candle.contract_key == contract_key, Candle.interval == interval
        ).order_by(desc(Candle.timestamp)).limit(min(limit, 2000))).all()
        return {"items": [{
            "timestamp": x.timestamp.isoformat(), "open": x.open, "high": x.high,
            "low": x.low, "close": x.close, "volume": x.volume
        } for x in reversed(rows)]}
    finally:
        db.close()

@app.post("/api/v1/trades")
def add_trade(t: TradePrintIn):
    db = SessionLocal()
    try:
        db.add(TradePrint(**t.model_dump()))
        db.commit()
        return {"stored": True}
    finally:
        db.close()

@app.get("/api/v1/orderflow")
def get_orderflow(contract_key: str, limit: int = 500):
    db = SessionLocal()
    try:
        rows = db.scalars(select(TradePrint).where(
            TradePrint.contract_key == contract_key
        ).order_by(desc(TradePrint.timestamp)).limit(min(limit, 2000))).all()
        levels = {}
        for t in rows:
            item = levels.setdefault(t.price, {"buy_volume": 0, "sell_volume": 0, "unknown_volume": 0})
            field = {"BUY": "buy_volume", "SELL": "sell_volume"}.get(t.aggressor, "unknown_volume")
            item[field] += t.quantity
        return {"items": [{"price": p, **v, "delta": v["buy_volume"] - v["sell_volume"]}
                          for p, v in sorted(levels.items())]}
    finally:
        db.close()
