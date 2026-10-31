# NIFTY OI Premium Profile — Full Source Project

A multi-part starter implementation for an Android options analytics app with a Python backend.
It is designed around the agreed workflow:

- NIFTY 50, selected expiry, ATM ± 10 strikes
- Separate CE and PE strike profiles
- Individual contract premium-wise OI profile (example: NIFTY 25350 PE)
- Current OI by live premium bucket
- Cumulative intraday OI additions, unwinding and net OI change
- Candlestick OHLCV screen
- Order-flow/footprint data model and screen
- SQLite event/snapshot persistence
- Docker-ready backend and GitHub Actions Android build

## Important status / data truth

DhanHQ **Data API** integration is implemented for option-chain + expiry list (official v2 endpoints / `dhanhq` SDK).

- Credentials stay **only** on the backend (`DHAN_CLIENT_ID`, `DHAN_ACCESS_TOKEN`, `DATA_MODE=live`).
- Android never embeds tokens; it calls your backend.
- Live mode requires an active Dhan **Data API** subscription and a valid access token.
- Option-chain rate limit: **1 unique request / 3 seconds** (Dhan rule).
- WebSocket live tick feed is not yet wired; REST option-chain ingest is ready.

See `docs/DHAN_INTEGRATION.md` for setup steps. Do not commit credentials or put them in the APK.

## Repository structure

- `android/` — Kotlin + Jetpack Compose Android app
- `backend/` — FastAPI service, SQLite, OI profile engine, tests
- `docs/` — architecture, data model, Dhan integration checklist
- `.github/workflows/` — Android and backend CI

## Quick start: backend

Requires Python 3.11+.

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: `http://localhost:8000/docs`

The backend starts in `demo` mode and serves clearly labelled sample data only. The OI profile engine and persistence endpoints are functional for submitted snapshots.

## Quick start: Android

Open `android/` in Android Studio (Ladybug or newer), install JDK 17 and Android SDK 35, then run the `app` configuration.

For an Android emulator, backend URL `http://10.0.2.2:8000` is used by default. For a physical phone, set the backend URL to your PC's LAN IP, e.g. `http://192.168.1.20:8000`, and configure a trusted network/firewall. Production should use HTTPS.

## Build APK with GitHub Actions

1. Push this repository to GitHub.
2. Open **Actions**.
3. Run **Build Android APK** or push to `main`.
4. Download artifact `nifty-oi-profile-debug-apk`.
5. Extract `app-debug.apk`.

The debug APK is for testing. A release APK must be signed with your own keystore; keep signing secrets in GitHub Actions secrets, never in source.

## OI event accounting

For each stable contract key (`underlying|expiry|strike|CE/PE`):

1. Save opening OI baseline and each valid timestamped snapshot.
2. Compare the latest valid OI with the prior valid OI.
3. Calculate delta OI.
4. Attribute that delta event to the LTP premium bucket at that event time.
5. Never move a historical OI event when LTP later migrates.
6. Recalculate current OI distribution using each contract's latest LTP.
7. Keep current OI, cumulative additions, cumulative unwinding and net change as separate profiles.

A change in OI does not identify whether the initiating party was a buyer or seller. Footprint requires trade prints plus a defensible aggressor-side classification. Market depth alone is not a complete trade footprint.

## Tests

```bash
cd backend
pytest -q
```

## Before live trading use

- Confirm Dhan data API subscription and current access rights.
- Implement/verify Dhan auth and refresh lifecycle on server only.
- Verify instrument master security IDs and expiry mapping.
- Verify packet parsing against current official packet docs.
- Implement reconnect, heartbeat, stale-data and rate-limit handling.
- Compare calculated OI with Dhan option-chain/market data during market hours.
- Validate timestamp timezone (`Asia/Kolkata`) and market-session reset.
- Do not use this app for automated orders; no order placement is implemented.
