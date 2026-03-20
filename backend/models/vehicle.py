"""Models describing vehicle detections and aggregate classification analytics."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class VehicleDetection(BaseModel):
    """Single CV detection result attributed to a lane and intersection."""

    class_id: int
    class_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox_x1: float
    bbox_y1: float
    bbox_x2: float
    bbox_y2: float
    lane: Optional[str] = Field(default=None, pattern="^(ew|ns)$")
    intersection_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class VehicleCount(BaseModel):
    """Aggregated vehicle counts per intersection direction."""

    intersection_id: str
    direction: str = Field(pattern="^(ew|ns)$")
    total: int = 0
    cars: int = 0
    motorcycles: int = 0
    buses: int = 0
    trucks: int = 0
    auto_rickshaws: int = 0
    bicycles: int = 0
    others: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class VehicleTypeDistribution(BaseModel):
    """Whole-network distribution of vehicle classes for analytics views."""

    cars: int = 0
    motorcycles: int = 0
    buses: int = 0
    trucks: int = 0
    auto_rickshaws: int = 0
    bicycles: int = 0
    others: int = 0
    total: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
