"""Pydantic models for emergency vehicle control, corridor events, and responses."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from models.intersection import TimestampedModel


class EmergencyVehicle(BaseModel):
    """Tracked emergency vehicle and the corridor currently reserved for it."""

    id: str
    type: str = Field(pattern="^(ambulance|fire|police)$")
    lat: float
    lng: float
    speed: float = Field(default=0.0, ge=0.0)
    heading: float = Field(default=0.0, ge=0.0, le=360.0)
    active: bool = True
    corridor_intersections: List[str] = Field(default_factory=list)


class EmergencyRegisterRequest(BaseModel):
    """API payload for registering a new emergency vehicle."""

    vehicle_id: str
    type: str = Field(pattern="^(ambulance|fire|police)$")


class GPSUpdateRequest(BaseModel):
    """GPS update payload sent by the emergency tracker or simulator."""

    vehicle_id: str
    lat: float
    lng: float
    speed: float = Field(default=0.0, ge=0.0)
    heading: float = Field(default=0.0, ge=0.0, le=360.0)


class EmergencyOverride(BaseModel):
    """Emergency override message delivered to a signal controller."""

    intersection_id: str
    vehicle_id: str
    vehicle_type: str = Field(pattern="^(ambulance|fire|police)$")
    ew_green: bool
    priority: int = Field(ge=1, le=3)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EmergencyEvent(BaseModel):
    """Event emitted for emergency corridor activation, conflict, or release."""

    id: str
    vehicle_id: str
    vehicle_type: str = Field(pattern="^(ambulance|fire|police)$")
    event_type: str
    intersection_id: Optional[str] = None
    corridor_intersections: List[str] = Field(default_factory=list)
    duration_seconds: Optional[float] = None
    details: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EmergencySimulateRequest(BaseModel):
    """Input for starting the built-in emergency demonstration flow."""

    vehicle_type: str = Field(default="ambulance", pattern="^(ambulance|fire|police)$")
    route_name: str = Field(default="city_centre_demo")


class EmergencyVehicleResponse(TimestampedModel):
    """Timestamped envelope for a single emergency vehicle."""

    data: EmergencyVehicle


class EmergencyVehicleListResponse(TimestampedModel):
    """Timestamped envelope for active emergency vehicles."""

    data: List[EmergencyVehicle]


class EmergencyEventListResponse(TimestampedModel):
    """Timestamped envelope for emergency analytics or logs."""

    data: List[EmergencyEvent]


class EmergencyStatus(BaseModel):
    """Summary of live emergency corridor status."""

    active_vehicles: List[EmergencyVehicle] = Field(default_factory=list)
    active_corridor: List[str] = Field(default_factory=list)
    total_preempted: int = 0
    conflicts: int = 0


class EmergencyStatusResponse(TimestampedModel):
    """Timestamped envelope for emergency corridor summary state."""

    data: EmergencyStatus
