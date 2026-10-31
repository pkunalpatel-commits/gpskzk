from collections import defaultdict
from datetime import datetime
from sqlalchemy import select, desc
from .db import SessionLocal, Snapshot, OiEvent

def bucket_for(ltp: float, bucket_size: float) -> float:
    return (ltp // bucket_size) * bucket_size

def ingest_snapshot(s):
    \"\"\"Persist snapshot and create an OI event against prior valid snapshot.
    Historical events stay attributed to the premium at event time.
    \"\"\"
    db = SessionLocal()
    try:
        previous = db.scalar(
            select(Snapshot).where(Snapshot.contract_key == s.contract_key)
            .order_by(desc(Snapshot.timestamp)).limit(1)
        )
        row = Snapshot(
            contract_key=s.contract_key, underlying=s.underlying, expiry=s.expiry,
            strike=s.strike, option_type=s.option_type, timestamp=s.timestamp,
            ltp=s.ltp, oi=s.oi, volume=s.volume, source=s.source
        )
        db.add(row)
        db.flush()
        if previous is not None:
            delta = s.oi - previous.oi
            # Avoid treating unchanged OI as a generation event.
            if delta != 0:
                size = 10.0
                db.add(OiEvent(
                    contract_key=s.contract_key, underlying=s.underlying,
                    expiry=s.expiry, strike=s.strike, option_type=s.option_type,
                    timestamp=s.timestamp, ltp_at_event=s.ltp,
                    premium_bucket=bucket_for(s.ltp, size), delta_oi=delta,
                    fresh_oi=max(delta, 0), unwinding=max(-delta, 0)
                ))
        db.commit()
        return {"stored": True, "delta_oi": None if previous is None else s.oi - previous.oi}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def contract_profile(contract_key: str, bucket_size: float = 10.0):
    db = SessionLocal()
    try:
        events = db.scalars(select(OiEvent).where(OiEvent.contract_key == contract_key)).all()
        latest = db.scalar(select(Snapshot).where(Snapshot.contract_key == contract_key)
                           .order_by(desc(Snapshot.timestamp)).limit(1))
        previous = db.scalar(select(Snapshot).where(Snapshot.contract_key == contract_key)
                             .order_by(desc(Snapshot.timestamp)).offset(1).limit(1))
        profile = defaultdict(lambda: {"fresh_oi": 0, "unwinding": 0, "net_oi": 0})
        for e in events:
            b = bucket_for(e.ltp_at_event, bucket_size)
            profile[b]["fresh_oi"] += e.fresh_oi
            profile[b]["unwinding"] += e.unwinding
            profile[b]["net_oi"] += e.delta_oi
        return {
            "contract_key": contract_key,
            "latest": None if latest is None else {
                "timestamp": latest.timestamp.isoformat(), "ltp": latest.ltp, "oi": latest.oi,
                "volume": latest.volume, "strike": latest.strike, "option_type": latest.option_type,
                "expiry": latest.expiry
            },
            "previous_snapshot": None if previous is None else {
                "timestamp": previous.timestamp.isoformat(), "oi": previous.oi
            },
            "bucket_size": bucket_size,
            "profile": [{"premium_from": b, "premium_to": b + bucket_size, **v}
                        for b, v in sorted(profile.items())]
        }
    finally:
        db.close()

def strike_profile(underlying: str, expiry: str, bucket_size: float = 10.0):
    db = SessionLocal()
    try:
        latest_rows = db.execute(
            select(Snapshot).where(Snapshot.underlying == underlying, Snapshot.expiry == expiry)
            .order_by(Snapshot.timestamp)
        ).scalars().all()
        latest = {}
        for row in latest_rows:
            latest[row.contract_key] = row
        base = {}
        # Opening baseline approximated by first stored snapshot per contract.
        rows = db.scalars(select(Snapshot).where(
            Snapshot.underlying == underlying, Snapshot.expiry == expiry
        ).order_by(Snapshot.timestamp)).all()
        for row in rows:
            base.setdefault(row.contract_key, row.oi)
        result = []
        for key, row in latest.items():
            delta = row.oi - base.get(key, row.oi)
            result.append({
                "strike": row.strike, "option_type": row.option_type,
                "current_oi": row.oi, "net_oi": delta,
                "fresh_oi": max(delta, 0), "unwinding": max(-delta, 0),
                "ltp": row.ltp, "premium_bucket": bucket_for(row.ltp, bucket_size)
            })
        return sorted(result, key=lambda x: (x["strike"], x["option_type"]))
    finally:
        db.close()
