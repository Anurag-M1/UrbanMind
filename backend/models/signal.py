"""Models representing signal hardware status, phase state, and controller acknowledgements."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SignalHardwareStatus(BaseModel):
    """Current signal hardware connectivity and health information."""

    intersection_id: str
    connected: bool = False
    protocol: str = Field(default="mqtt")
    firmware_version: Optional[str] = None
    uptime_seconds: int = 0
    last_ack: Optional[datetime] = None
    fault_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SignalPhaseState(BaseModel):
    """Controller-level phase information for a single intersection."""

    intersection_id: str
    ew_green: bool
    phase_remaining_seconds: float = Field(default=0.0, ge=0.0)
    cycle_position_seconds: float = Field(default=0.0, ge=0.0)
    mode: str = Field(default="adaptive")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SignalAck(BaseModel):
    """Acknowledgement payload returned by physical or simulated controllers."""

    intersection_id: str
    status: str = "acknowledged"
    received_at: datetime = Field(default_factory=datetime.utcnow)
