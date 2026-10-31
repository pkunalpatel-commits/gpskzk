from datetime import datetime, timezone, timedelta
from app.models import SnapshotIn
from app.db import init_db, engine, Base, SessionLocal
from app.engine import ingest_snapshot, contract_profile

def setup_function():
    Base.metadata.drop_all(bind=engine)
    init_db()

def test_snapshot_delta_and_premium_attribution():
    t = datetime.now(timezone.utc)
    first = SnapshotIn(contract_key="NIFTY|2026-11-05|25350|PE", expiry="2026-11-05",
        strike=25350, option_type="PE", timestamp=t, ltp=64.5, oi=100000)
    second = SnapshotIn(contract_key="NIFTY|2026-11-05|25350|PE", expiry="2026-11-05",
        strike=25350, option_type="PE", timestamp=t+timedelta(minutes=1), ltp=74.5, oi=112000)
    assert ingest_snapshot(first)["delta_oi"] is None
    assert ingest_snapshot(second)["delta_oi"] == 12000
    result = contract_profile("NIFTY|2026-11-05|25350|PE", 10)
    assert result["profile"][0]["premium_from"] == 70.0
    assert result["profile"][0]["net_oi"] == 12000
