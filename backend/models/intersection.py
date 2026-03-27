from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime


class IntersectionState(BaseModel):
    id: str
    name: str
    lat: float
    lng: float
    address: str = ""
    ew_green: bool = True
    ew_phase_seconds: float = 0.0
    ew_green_duration: int = 30
    ns_green_duration: int = 25
    cycle_length: int = 59
    density_ew: int = 10
    density_ns: int = 8
    queue_ew_meters: float = 0.0
    queue_ns_meters: float = 0.0
    wait_time_avg: float = 0.0
    wait_time_history: List[float] = Field(default_factory=list)
    throughput_per_hour: int = 0
    override: bool = False
    override_reason: str = ""
    fault: bool = False
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    webster_last_calc: datetime = Field(default_factory=datetime.utcnow)
    total_vehicles_processed: int = 0


class VehicleDetection(BaseModel):
    frame_number: int
    class_name: str
    confidence: float
    bbox: List[float]
    lane: str = ""
    intersection_id: str = ""


class VideoFrame(BaseModel):
    frame_number: int
    timestamp_seconds: float
    detections: List[VehicleDetection] = Field(default_factory=list)
    ew_count: int = 0
    ns_count: int = 0
    annotated_image_b64: str = ""


class VideoAnalysisResult(BaseModel):
    video_id: str
    filename: str = ""
    duration_seconds: float = 0.0
    total_frames: int = 0
    fps: float = 0.0
    frames_processed: int = 0
    intersections_detected: List[str] = Field(default_factory=list)
    vehicle_counts: Dict[str, int] = Field(default_factory=dict)
    lane_density: Dict[str, int] = Field(default_factory=dict)
    recommended_timings: Dict = Field(default_factory=dict)
    detection_frames: List[VideoFrame] = Field(default_factory=list)
    processing_time_seconds: float = 0.0
    status: str = "processing"
    error_message: str = ""
