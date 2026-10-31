# DhanHQ Data API integration

Implemented against official DhanHQ v2 documentation:
- https://docs.dhanhq.co/
- https://dhanhq.co/docs/v2/option-chain/
- Python SDK: `pip install dhanhq`

## What is wired

| Feature | Endpoint / module | Status |
|---------|-------------------|--------|
| Auth (client-id + access-token) | env only | ✅ |
| Provider status | `GET /api/v1/provider/status` | ✅ |
| Expiry list | `GET /api/v1/dhan/expiries` | ✅ |
| Option chain (OI, LTP, IV, bid/ask) | `GET /api/v1/dhan/optionchain` | ✅ |
| Ingest into OI premium engine | `ingest=true` on optionchain | ✅ |
| Credentials in APK | — | ❌ never |

## Setup (backend only)

1. Open **web.dhan.co** → Profile → **Access DhanHQ APIs**
2. Generate **Access Token** (24h) or use API-key flow + TOTP
3. Confirm **Data APIs** subscription is active (required for option chain / live quotes)
4. In `backend/.env`:

```env
DATA_MODE=live
DHAN_CLIENT_ID=your_client_id
DHAN_ACCESS_TOKEN=your_access_token
```

5. Install and run:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

6. Test:

```bash
curl http://localhost:8000/api/v1/provider/status
curl "http://localhost:8000/api/v1/dhan/expiries?underlying=NIFTY"
curl "http://localhost:8000/api/v1/dhan/optionchain?underlying=NIFTY&atm_range=10&ingest=true"
```

## Official identifiers

| Underlying | Security ID | Segment |
|------------|-------------|---------|
| NIFTY      | 13          | IDX_I   |
| BANKNIFTY  | 25          | IDX_I   |
| FINNIFTY   | 27          | IDX_I   |

## Rate limits (Dhan)

- Option Chain: **1 unique request / 3 seconds**
- Market Quote: 1 req/sec (up to 1000 instruments)
- Data APIs daily cap: see current Dhan docs

Respect these limits; do not poll option chain faster than every 3s.

## Security rules (must follow)

- Credentials live **only** in backend environment variables
- Never put `DHAN_ACCESS_TOKEN` in Android `BuildConfig`, resources, or source
- Android talks only to **your backend** over HTTP/HTTPS
- Do not log full tokens
- Access tokens expire (typically 24h); renew via Dhan Web or RenewToken API

## Android

The app shows provider status from `/api/v1/provider/status`.
When `mode=live` and `connected=true`, the UI labels data as live.
When credentials are missing, it clearly shows **DEMO / NOT CONNECTED**.

## Not yet implemented (next steps)

- Live Market Feed WebSocket (`wss://api-feed.dhan.co`) for tick-level OI/LTP
- Binary packet decode for Full / Quote / OI packets
- Background poller (every ≥3s) during market hours
- Instrument master CSV download + security_id cache
- Token auto-renewal with TOTP

These require continuous connection handling and must still keep all secrets on the server.
