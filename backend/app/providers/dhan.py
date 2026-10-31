\"\"\"Dhan provider adapter boundary.

Do not guess packet layouts or silently label placeholder data as live.
Complete this adapter against the current official DhanHQ docs and test
against a subscribed account before setting DATA_MODE=live.
\"\"\"
from dataclasses import dataclass
from ..config import DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN

@dataclass
class ProviderStatus:
    provider: str
    configured: bool
    mode: str
    message: str

def status() -> ProviderStatus:
    configured = bool(DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN)
    return ProviderStatus(
        provider="DhanHQ",
        configured=configured,
        mode="adapter_pending",
        message=("Credentials detected; live adapter still requires verified implementation."
                 if configured else "Dhan credentials are not configured on backend.")
    )

class DhanProvider:
    def __init__(self):
        self.client_id = DHAN_CLIENT_ID
        self.access_token = DHAN_ACCESS_TOKEN

    def connect(self):
        raise NotImplementedError(
            "Implement current DhanHQ auth/WebSocket protocol from official docs. "
            "This starter intentionally does not fabricate live data."
        )

    def subscribe(self, security_ids: list[str]):
        raise NotImplementedError("Implement documented Dhan subscription packet and limits.")

    def parse_market_packet(self, packet: bytes):
        raise NotImplementedError("Implement and test current Dhan binary packet schema.")
