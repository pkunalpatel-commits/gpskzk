# Implementation status

## Implemented in this repository
- Android Compose application shell and contract selector.
- Android REST client for health, provider status and individual contract OI profile.
- FastAPI service with SQLite persistence.
- Snapshot ingestion and per-contract OI delta event generation.
- Event-time premium-bucket attribution.
- Individual contract premium profile API.
- Strike profile aggregation API.
- Candle persistence/read API.
- Trade-print persistence and price-level delta aggregation API.
- Backend unit test for OI event attribution.
- GitHub Actions workflows for APK compilation and backend tests.

## Not implemented / requires integration work
- Verified live DhanHQ login/token generation and refresh.
- Official instrument-master downloader/parser.
- Dhan WebSocket authentication, subscription and binary packet parser.
- Live option-chain fetch and expiry discovery.
- Production-grade server authentication, TLS deployment and monitoring.
- Full candlestick chart renderer and real-time chart streaming.
- Full bid/ask footprint visualization.
- Broker-provided aggressor-side classification (if unavailable, classification must be estimated and labelled).
- Historical replay UI, alert push notifications and signed release APK.

The Dhan-specific work is deliberately not faked. Dhan API access requires an eligible Data API subscription and valid credentials. The access token is sensitive and should remain on the backend. Check current official DhanHQ documentation before implementing version-sensitive auth and feed packet details.
