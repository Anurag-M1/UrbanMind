from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class LaneDensityModel(BaseModel):
    """Represents density telemetry for one lane."""

    count: int
    queue_length: int
    flow_rate: float
    congestion_level: Literal["LOW", "MED", "HIGH"]


class DeviceHealthModel(BaseModel):
    """Represents device health telemetry."""

    cpu_pct: float
    mem_pct: float
    inference_ms: float


class SignalPhaseModel(BaseModel):
    """Represents one signal phase."""

    direction: str
    green_duration: int


class SignalPlanModel(BaseModel):
    """Represents a signal plan."""

    cycle_length: int
    phases: list[SignalPhaseModel]


class CorridorStatusModel(BaseModel):
    """Represents an emergency corridor state."""

    corridor_id: str | None = None
    active: bool = False
    vehicle_id: str | None = None
    vehicle_type: str | None = None
    route: list[str] = Field(default_factory=list)
    pre_empted_intersections: list[str] = Field(default_factory=list)
    updated_at: str | None = None


class IntersectionStateModel(BaseModel):
    """Represents the latest state for an intersection."""

    intersection_id: str
    timestamp: str
    lane_densities: dict[str, LaneDensityModel]
    current_signal_plan: SignalPlanModel
    emergency_active: bool
    corridor_status: CorridorStatusModel | None = None
    device_health: DeviceHealthModel


class SignalOverrideRequest(BaseModel):
    """Represents a manual override command."""

    phase: str
    duration_seconds: int
    reason: str = Field(min_length=1)


class EmergencyActivateRequest(BaseModel):
    """Represents an emergency activation request."""

    vehicle_id: str
    vehicle_type: Literal["ambulance", "fire", "police"]
    gps_lat: float
    gps_lon: float
    route: list[str]


class EmergencyUpdateRequest(BaseModel):
    """Represents an emergency GPS update."""

    gps_lat: float
    gps_lon: float
