"""
DhanHQ Data API provider — implemented against official DhanHQ v2 docs.

References:
  - https://docs.dhanhq.co/
  - https://dhanhq.co/docs/v2/option-chain/
  - https://pypi.org/project/dhanhq/
  - NIFTY index security_id = 13, segment = IDX_I

Credentials (DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN) must live only in backend env.
Never embed them in the APK or commit them to git.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from ..config import DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN, DATA_MODE

logger = logging.getLogger(__name__)

# Official Dhan index security IDs
NIFTY_SECURITY_ID = 13
BANKNIFTY_SECURITY_ID = 25
FINNIFTY_SECURITY_ID = 27
UNDERLYING_MAP = {
    "NIFTY": NIFTY_SECURITY_ID,
    "BANKNIFTY": BANKNIFTY_SECURITY_ID,
    "FINNIFTY": FINNIFTY_SECURITY_ID,
}
UNDERLYING_SEGMENT = "IDX_I"


@dataclass
class ProviderStatus:
    provider: str
    configured: bool
    mode: str
    message: str
    connected: bool = False
    last_error: str = ""


@dataclass
class OptionContract:
    """Normalized contract from Dhan option chain."""
    security_id: str
    underlying: str
    expiry: str
    strike: int
    option_type: str  # CE | PE
    ltp: float
    oi: int
    volume: int
    bid_price: float = 0.0
    bid_qty: int = 0
    ask_price: float = 0.0
    ask_qty: int = 0
    iv: float = 0.0
    delta: float = 0.0
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0

    @property
    def contract_key(self) -> str:
        return f"{self.underlying}|{self.expiry}|{self.strike}|{self.option_type}"


@dataclass
class OptionChainResult:
    underlying: str
    expiry: str
    underlying_ltp: float
    contracts: list = field(default_factory=list)
    source: str = "dhan"
    fetched_at: str = ""
    raw_keys: list = field(default_factory=list)


def status() -> ProviderStatus:
    configured = bool(DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN)
    if not configured:
        return ProviderStatus(
            provider="DhanHQ",
            configured=False,
            mode="demo",
            message="Dhan credentials not set. Set DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN in backend .env",
            connected=False,
        )
    if DATA_MODE != "live":
        return ProviderStatus(
            provider="DhanHQ",
            configured=True,
            mode="demo",
            message="Credentials present but DATA_MODE is not 'live'. Set DATA_MODE=live to use Dhan Data API.",
            connected=False,
        )
    try:
        client = _get_client()
        if hasattr(client, "get_fund_limits"):
            client.get_fund_limits()
        elif hasattr(client, "get_profile"):
            client.get_profile()
        return ProviderStatus(
            provider="DhanHQ",
            configured=True,
            mode="live",
            message="Connected to DhanHQ Data API",
            connected=True,
        )
    except Exception as exc:
        return ProviderStatus(
            provider="DhanHQ",
            configured=True,
            mode="error",
            message="Credentials present but Dhan API call failed. Check token validity and Data API subscription (₹499/mo).",
            connected=False,
            last_error=str(exc)[:300],
        )


_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    if not (DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN):
        raise RuntimeError("DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN are required for live mode")
    try:
        from dhanhq import DhanContext, dhanhq
    except ImportError as e:
        raise RuntimeError("dhanhq package not installed. Run: pip install dhanhq") from e
    ctx = DhanContext(DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN)
    _client = dhanhq(ctx)
    return _client


def get_expiry_list(underlying: str = "NIFTY") -> list:
    sec_id = UNDERLYING_MAP.get(underlying.upper())
    if sec_id is None:
        raise ValueError(f"Unsupported underlying: {underlying}. Use one of {list(UNDERLYING_MAP)}")
    client = _get_client()
    if hasattr(client, "expiry_list"):
        resp = client.expiry_list(
            under_security_id=sec_id,
            under_exchange_segment=UNDERLYING_SEGMENT,
        )
    else:
        import httpx
        r = httpx.post(
            "https://api.dhan.co/v2/optionchain/expirylist",
            headers={
                "access-token": DHAN_ACCESS_TOKEN,
                "client-id": DHAN_CLIENT_ID,
                "Content-Type": "application/json",
            },
            json={
                "UnderlyingScrip": sec_id,
                "UnderlyingSeg": UNDERLYING_SEGMENT,
            },
            timeout=30.0,
        )
        r.raise_for_status()
        resp = r.json()

    data = resp.get("data", resp) if isinstance(resp, dict) else resp
    if isinstance(data, dict):
        expiries = data.get("data") or data.get("expiryList") or data.get("ExpiryList") or []
    else:
        expiries = data or []
    if isinstance(expiries, dict):
        expiries = list(expiries.values()) if expiries else []
    return [str(e) for e in expiries]


def fetch_option_chain(underlying: str = "NIFTY", expiry: str = "", atm_range: int = 10) -> OptionChainResult:
    """
    Fetch option chain from Dhan. Rate limit: 1 unique request / 3 seconds.
    NIFTY UnderlyingScrip=13, UnderlyingSeg=IDX_I
    """
    sec_id = UNDERLYING_MAP.get(underlying.upper())
    if sec_id is None:
        raise ValueError(f"Unsupported underlying: {underlying}")
    if not expiry:
        expiries = get_expiry_list(underlying)
        if not expiries:
            raise RuntimeError("No expiries returned from Dhan")
        expiry = expiries[0]

    client = _get_client()
    if hasattr(client, "option_chain"):
        resp = client.option_chain(
            under_security_id=sec_id,
            under_exchange_segment=UNDERLYING_SEGMENT,
            expiry=expiry,
        )
    else:
        import httpx
        r = httpx.post(
            "https://api.dhan.co/v2/optionchain",
            headers={
                "access-token": DHAN_ACCESS_TOKEN,
                "client-id": DHAN_CLIENT_ID,
                "Content-Type": "application/json",
            },
            json={
                "UnderlyingScrip": sec_id,
                "UnderlyingSeg": UNDERLYING_SEGMENT,
                "Expiry": expiry,
            },
            timeout=45.0,
        )
        r.raise_for_status()
        resp = r.json()

    return _parse_option_chain_response(resp, underlying.upper(), expiry, atm_range)


def _parse_option_chain_response(resp: Any, underlying: str, expiry: str, atm_range: int) -> OptionChainResult:
    data = resp.get("data", resp) if isinstance(resp, dict) else {}
    if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
        data = data["data"]

    underlying_ltp = float(
        data.get("last_price")
        or data.get("lastPrice")
        or data.get("underlyingValue")
        or data.get("UnderlyingValue")
        or 0
    )

    oc = data.get("oc") or data.get("optionChain") or data.get("OC") or {}
    contracts = []
    raw_keys = []

    strike_map = {}
    for strike_key, sides in oc.items():
        try:
            strike = int(float(str(strike_key).replace(",", "")))
        except (TypeError, ValueError):
            continue
        strike_map[strike] = sides if isinstance(sides, dict) else {}

    if not strike_map:
        chain_list = data.get("chain") or data.get("strikes") or []
        for item in chain_list:
            if not isinstance(item, dict):
                continue
            try:
                strike = int(float(item.get("strike") or item.get("strikePrice") or 0))
            except (TypeError, ValueError):
                continue
            strike_map[strike] = item

    strikes_sorted = sorted(strike_map.keys())
    if underlying_ltp > 0 and strikes_sorted:
        atm = min(strikes_sorted, key=lambda s: abs(s - underlying_ltp))
        atm_idx = strikes_sorted.index(atm)
        lo = max(0, atm_idx - atm_range)
        hi = min(len(strikes_sorted), atm_idx + atm_range + 1)
        selected = strikes_sorted[lo:hi]
    else:
        selected = strikes_sorted

    for strike in selected:
        sides = strike_map[strike]
        for side_key, opt_type in (("ce", "CE"), ("pe", "PE"), ("CE", "CE"), ("PE", "PE")):
            side = sides.get(side_key) if isinstance(sides, dict) else None
            if not side or not isinstance(side, dict):
                continue
            raw_keys.append(f"{strike}:{opt_type}")
            greeks = side.get("greeks") or {}
            contracts.append(
                OptionContract(
                    security_id=str(
                        side.get("security_id")
                        or side.get("securityId")
                        or side.get("SecurityId")
                        or ""
                    ),
                    underlying=underlying,
                    expiry=expiry,
                    strike=strike,
                    option_type=opt_type,
                    ltp=float(side.get("last_price") or side.get("lastPrice") or side.get("LTP") or 0),
                    oi=int(side.get("oi") or side.get("OI") or side.get("open_interest") or 0),
                    volume=int(side.get("volume") or side.get("Volume") or 0),
                    bid_price=float(side.get("top_bid_price") or side.get("bid") or side.get("best_bid_price") or 0),
                    bid_qty=int(side.get("top_bid_quantity") or side.get("bid_qty") or 0),
                    ask_price=float(side.get("top_ask_price") or side.get("ask") or side.get("best_ask_price") or 0),
                    ask_qty=int(side.get("top_ask_quantity") or side.get("ask_qty") or 0),
                    iv=float(side.get("implied_volatility") or side.get("iv") or side.get("IV") or 0),
                    delta=float(greeks.get("delta", side.get("delta", 0)) or 0),
                    gamma=float(greeks.get("gamma", side.get("gamma", 0)) or 0),
                    theta=float(greeks.get("theta", side.get("theta", 0)) or 0),
                    vega=float(greeks.get("vega", side.get("vega", 0)) or 0),
                )
            )

    return OptionChainResult(
        underlying=underlying,
        expiry=expiry,
        underlying_ltp=underlying_ltp,
        contracts=contracts,
        source="dhan",
        fetched_at=datetime.now(timezone.utc).isoformat(),
        raw_keys=raw_keys,
    )


class DhanProvider:
    def __init__(self):
        self.client_id = DHAN_CLIENT_ID
        self.access_token = DHAN_ACCESS_TOKEN

    def is_live_ready(self) -> bool:
        return bool(self.client_id and self.access_token and DATA_MODE == "live")

    def status(self) -> ProviderStatus:
        return status()

    def expiry_list(self, underlying: str = "NIFTY") -> list:
        return get_expiry_list(underlying)

    def option_chain(self, underlying: str = "NIFTY", expiry: str = "", atm_range: int = 10) -> OptionChainResult:
        return fetch_option_chain(underlying, expiry, atm_range)
