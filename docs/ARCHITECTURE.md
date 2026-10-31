# Architecture

## Components

1. Android client: Compose UI, Retrofit REST client, local settings.
2. FastAPI backend: API facade, provider adapter, OI aggregation engine.
3. Dhan provider adapter: server-side auth, instrument master, market feed and option-chain integration.
4. SQLite: raw snapshots, OI delta events, profile metadata.
5. CI: Android APK build and Python test workflow.

## Data flow

Dhan feed -> provider adapter -> normalized contract snapshots -> OI engine -> SQLite -> REST API -> Android charts.

## Profiles

- Strike profile: current OI / fresh additions / unwinding / net change grouped by strike, CE/PE separately.
- Contract premium profile: a single contract's OI delta events grouped by the premium bucket at event time.
- Current premium distribution: current OI allocated using the latest LTP bucket.
- Heatmap: strike x premium bucket.
- OHLC: timestamped option candles.
- Footprint: price-level bid/ask trade volume only when trade prints and aggressor classification are available.

## Time and session

Use exchange-local `Asia/Kolkata`. Session baseline must be created on the first valid snapshot at or after market open, not by assuming the first received packet is exactly 09:15. Keep previous valid OI for delta calculation and opening baseline for cumulative intraday calculation.
