# DhanHQ integration checklist

This project intentionally isolates Dhan-specific calls in `backend/app/providers/dhan.py`.

Before enabling live mode:

1. Read current official DhanHQ API documentation and confirm the correct API version.
2. Confirm the account has the required market-data entitlement.
3. Configure `DHAN_CLIENT_ID` and `DHAN_ACCESS_TOKEN` in the backend environment only.
4. Implement the currently documented authentication mechanism.
5. Download and parse the official instrument master; persist exchange segment, security ID, underlying, expiry, strike, option type and lot size.
6. Implement the currently documented option-chain endpoint and respect its current per-client/per-endpoint rate limits.
7. Implement WebSocket connection, authorization, subscription packet, binary packet decoding, heartbeat and reconnect according to the current packet specification.
8. Confirm whether live feed provides the trade prints and bid/ask fields needed for a real footprint. If aggressor-side trade classification is not supplied, label inferred classification as estimated.
9. Validate OI values, units and update frequency against the official option-chain response.
10. Add contract-level subscription limits and batching.

Never put the Dhan access token in Android resources, BuildConfig, source control, logs or API responses. Use HTTPS and an authenticated backend in production.

The adapter currently reports `configured=false` and does not fabricate live data. A developer must complete and test the version-sensitive Dhan packet/auth implementation before setting live status.
