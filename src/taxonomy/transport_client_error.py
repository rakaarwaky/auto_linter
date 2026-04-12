"""transport_client_error — Transport domain error types."""

from typing import Optional
from pydantic import BaseModel, ConfigDict

from taxonomy.transport_protocol_vo import TransportProtocol, TransportEndpoint


class TransportError(BaseModel):
    """Transport communication failed."""
    model_config = ConfigDict(frozen=True)

    protocol: TransportProtocol
    message: str
    endpoint: Optional[TransportEndpoint] = None
    underlying_error: str = ""

    def __str__(self) -> str:
        ep = f" {self.endpoint}" if self.endpoint else ""
        return f"[{self.protocol.value}]{ep} {self.message}"
