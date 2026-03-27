from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class EmergencyVehicle(BaseModel):
    id: str
    type: str  # "ambulance" | "fire" | "police"
    lat: float = 0.0
    lng: float = 0.0
    speed_kmh: float = 0.0
    heading_degrees: float = 0.0
    active: bool = True
    activated_at: datetime = Field(default_factory=datetime.utcnow)
    corridor_intersections: List[str] = Field(default_factory=list)
    current_intersection_idx: int = 0
    eta_seconds: float = 0.0


class EmergencyEvent(BaseModel):
    id: str
    vehicle_id: str
    vehicle_type: str
    activated_at: datetime = Field(default_factory=datetime.utcnow)
    deactivated_at: Optional[datetime] = None
    intersections_cleared: int = 0
    response_time_saved_seconds: float = 0.0
