"""Pydantic models for signal state, density updates, and API envelopes."""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class TimestampedModel(BaseModel):
    """Common timestamp field shared by API response envelopes."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)


class IntersectionState(BaseModel):
    """Live state for a single intersection in the UrbanMind network."""

    id: str
    name: str
    lat: float
    lng: float
    ew_green: bool
    ew_phase_seconds: float = Field(default=0.0, ge=0.0)
    ew_green_duration: int = Field(default=30, ge=10, le=60)
    ns_green_duration: int = Field(default=25, ge=10, le=60)
    density_ew: int = Field(default=0, ge=0)
    density_ns: int = Field(default=0, ge=0)
    queue_ew: float = Field(default=0.0, ge=0.0)
    queue_ns: float = Field(default=0.0, ge=0.0)
    wait_time_avg: float = Field(default=0.0, ge=0.0)
    override: bool = False
    fault: bool = False
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class IntersectionCreateRequest(BaseModel):
    """Payload used by seed scripts or admin flows to create intersections."""

    id: str
    name: str
    lat: float
    lng: float
    ew_green: bool = True
    ew_phase_seconds: float = Field(default=0.0, ge=0.0)
    ew_green_duration: int = Field(default=30, ge=10, le=60)
    ns_green_duration: int = Field(default=25, ge=10, le=60)
    density_ew: int = Field(default=0, ge=0)
    density_ns: int = Field(default=0, ge=0)
    queue_ew: float = Field(default=0.0, ge=0.0)
    queue_ns: float = Field(default=0.0, ge=0.0)
    wait_time_avg: float = Field(default=0.0, ge=0.0)
    override: bool = False
    fault: bool = False


class SignalCommand(BaseModel):
    """Adaptive or manual signal timing command published to controllers."""

    intersection_id: str
    ew_green_duration: int = Field(ge=10, le=60)
    ns_green_duration: int = Field(ge=10, le=60)
    immediate: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DensityUpdate(BaseModel):
    """Density measurement received from the CV worker or simulator."""

    intersection_id: str
    lane: str = Field(pattern="^(ew|ns)$")
    count: int = Field(ge=0)
    queue_meters: float = Field(ge=0.0)
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ManualSignalCommandRequest(BaseModel):
    """Manual override request from an admin client."""

    ew_green_duration: int = Field(ge=10, le=60)
    ns_green_duration: int = Field(ge=10, le=60)
    immediate: bool = False


class IntersectionStats(BaseModel):
    """Aggregate live network statistics."""

    total_intersections: int = 0
    online_count: int = 0
    faulted_count: int = 0
    overridden_count: int = 0
    network_avg_wait_time: float = 0.0
    total_vehicles_detected: int = 0


class IntersectionResponse(TimestampedModel):
    """Timestamped envelope for a single intersection."""

    data: IntersectionState


class IntersectionListResponse(TimestampedModel):
    """Timestamped envelope for multiple intersections."""

    data: List[IntersectionState]


class DensityUpdateResponse(TimestampedModel):
    """Timestamped envelope for density update acknowledgements."""

    data: DensityUpdate


class SignalCommandResponse(TimestampedModel):
    """Timestamped envelope for signal command acknowledgements."""

    data: SignalCommand


class IntersectionStatsResponse(TimestampedModel):
    """Timestamped envelope for aggregate live statistics."""

    data: IntersectionStats


class OperationStatusResponse(TimestampedModel):
    """Timestamped generic operation response."""

    status: str
    message: str
    resource_id: str | None = None
