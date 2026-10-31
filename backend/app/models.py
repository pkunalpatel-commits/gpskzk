from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal, Optional

OptionType = Literal["CE", "PE"]

class SnapshotIn(BaseModel):
    contract_key: str = Field(min_length=5)
    underlying: str = "NIFTY"
    expiry: str
    strike: int
    option_type: OptionType
    timestamp: datetime
    ltp: float = Field(ge=0)
    oi: int = Field(ge=0)
    volume: int = Field(default=0, ge=0)
    bid_price: Optional[float] = None
    bid_qty: Optional[int] = None
    ask_price: Optional[float] = None
    ask_qty: Optional[int] = None
    source: str = "manual_or_provider"

class CandleIn(BaseModel):
    contract_key: str
    timestamp: datetime
    interval: str = "1m"
    open: float
    high: float
    low: float
    close: float
    volume: int = 0

class TradePrintIn(BaseModel):
    contract_key: str
    timestamp: datetime
    price: float
    quantity: int
    aggressor: Literal["BUY", "SELL", "UNKNOWN"] = "UNKNOWN"
    source: str = "provider"

class ProfileQuery(BaseModel):
    contract_key: str
    bucket_size: float = Field(default=10.0, gt=0)
