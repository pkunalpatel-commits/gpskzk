from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import select, desc
from .db import init_db, SessionLocal, Candle, TradePrint
from .models import SnapshotIn, CandleIn, TradePrintIn
from .engine import ingest_snapshot, contract_profile, strike_profile
from .providers import dhan as dhan_provider
from .config import DATA_MODE

app = FastAPI(title="NIFTY OI Premium Profile API", version="0.2.0")


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    st = dhan_provider.status()
    return {
        "status": "ok",
        "service": "nifty-oi-profile",
        "data_mode": DATA_MODE,
        "dhan_connected": st.connected,
    }


@app.get("/api/v1/provider/status")
def provider_status():
    return dhan_provider.status().__dict__


@app.get("/api/v1/dhan/expiries")
def dhan_expiries(underlying: str = Query("NIFTY")):
    """Fetch available option expiries from DhanHQ (requires live credentials + Data API)."""
    st = dhan_provider.status()
    if not st.configured or DATA_MODE != "live":
        raise HTTPException(
            503,
            detail={
                "error": "Dhan live mode not active",
                "message": st.message,
                "hint": "Set DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN and DATA_MODE=live in backend .env",
            },
        )
    try:
        expiries = dhan_provider.get_expiry_list(underlying)
        return {"underlying": underlying.upper(), "expiries": expiries, "source": "dhan"}
    except Exception as exc:
        raise HTTPException(502, detail=f"Dhan expiry list failed: {exc}")


@app.get("/api/v1/dhan/optionchain")
def dhan_optionchain(
    underlying: str = Query("NIFTY"),
    expiry: str = Query(""),
    atm_range: int = Query(10, ge=1, le=30),
    ingest: bool = Query(True, description="Ingest OI snapshots into local profile engine"),
):
    """
    Fetch live option chain from DhanHQ Data API (official rate limit: 1 unique req / 3s).
    Optionally ingests CE/PE OI+LTP snapshots into the premium-profile engine.
    """
    st = dhan_provider.status()
    if not st.configured or DATA_MODE != "live":
        raise HTTPException(
            503,
            detail={
                "error": "Dhan live mode not active",
                "message": st.message,
                "hint": "Set DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN and DATA_MODE=live in backend .env. "
                        "Data API subscription required (see dhanhq.co).",
            },
        )
    try:
        result = dhan_provider.fetch_option_chain(underlying, expiry, atm_range)
    except Exception as exc:
        raise HTTPException(502, detail=f"Dhan option chain failed: {exc}")

    ingested = 0
    errors = []
    if ingest:
        now = datetime.now(timezone.utc)
        for c in result.contracts:
            try:
                snap = SnapshotIn(
                    contract_key=c.contract_key,
                    underlying=c.underlying,
                    expiry=c.expiry,
                    strike=c.strike,
                    option_type=c.option_type,
                    timestamp=now,
                    ltp=c.ltp,
                    oi=c.oi,
                    volume=c.volume,
                    bid_price=c.bid_price or None,
                    bid_qty=c.bid_qty or None,
                    ask_price=c.ask_price or None,
                    ask_qty=c.ask_qty or None,
                    source="dhan",
                )
                ingest_snapshot(snap)
                ingested += 1
            except Exception as e:
                errors.append(f"{c.contract_key}: {e}")

    return {
        "underlying": result.underlying,
        "expiry": result.expiry,
        "underlying_ltp": result.underlying_ltp,
        "source": result.source,
        "fetched_at": result.fetched_at,
        "contract_count": len(result.contracts),
        "ingested": ingested,
        "ingest_errors": errors[:10],
        "contracts": [
            {
                "contract_key": c.contract_key,
                "security_id": c.security_id,
                "strike": c.strike,
                "option_type": c.option_type,
                "ltp": c.ltp,
                "oi": c.oi,
                "volume": c.volume,
                "bid": c.bid_price,
                "ask": c.ask_price,
                "iv": c.iv,
            }
            for c in result.contracts
        ],
    }


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
    return {
        "underlying": underlying,
        "expiry": expiry,
        "items": strike_profile(underlying, expiry, bucket_size),
    }


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
        rows = db.scalars(
            select(Candle)
            .where(Candle.contract_key == contract_key, Candle.interval == interval)
            .order_by(desc(Candle.timestamp))
            .limit(min(limit, 2000))
        ).all()
        return {
            "items": [
                {
                    "timestamp": x.timestamp.isoformat(),
                    "open": x.open,
                    "high": x.high,
                    "low": x.low,
                    "close": x.close,
                    "volume": x.volume,
                }
                for x in reversed(rows)
            ]
        }
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
        rows = db.scalars(
            select(TradePrint)
            .where(TradePrint.contract_key == contract_key)
            .order_by(desc(TradePrint.timestamp))
            .limit(min(limit, 2000))
        ).all()
        levels = {}
        for t in rows:
            item = levels.setdefault(t.price, {"buy_volume": 0, "sell_volume": 0, "unknown_volume": 0})
            field = {"BUY": "buy_volume", "SELL": "sell_volume"}.get(t.aggressor, "unknown_volume")
            item[field] += t.quantity
        return {
            "items": [
                {"price": p, **v, "delta": v["buy_volume"] - v["sell_volume"]}
                for p, v in sorted(levels.items())
            ]
        }
    finally:
        db.close()
