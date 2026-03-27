from pydantic import BaseModel
from typing import Optional


class Vehicle(BaseModel):
    id: str
    type: str  # "car" | "motorcycle" | "auto" | "bus" | "truck" | "ambulance" | "fire" | "police"
    lat: float = 0.0
    lng: float = 0.0
    speed_kmh: float = 0.0
    heading_degrees: float = 0.0
    lane: str = ""
    intersection_id: Optional[str] = None
    is_emergency: bool = False
