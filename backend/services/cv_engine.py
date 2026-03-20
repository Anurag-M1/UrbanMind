"""Helpers for ingesting CV worker updates and exposing intersection camera configs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from models.intersection import DensityUpdate
from services import state_manager


@dataclass
class CameraConfig:
    """Minimal camera configuration the CV worker can consume from the backend."""

    id: str
    rtsp_url: str
    calibration_ppm: float = 10.0
    lanes: dict[str, dict[str, float]] | None = None


async def apply_density_measurement(update: DensityUpdate) -> None:
    """Persist a density measurement and derived analytics samples."""

    await state_manager.apply_density_update(update)


async def list_camera_configs() -> list[dict[str, Any]]:
    """Return generated camera configs for all seeded intersections."""

    intersections = await state_manager.get_all_intersections()
    return [
        CameraConfig(
            id=intersection.id,
            rtsp_url=f"rtsp://camera/{intersection.id}",
            calibration_ppm=10.0,
            lanes={
                "ew_in": {"x1": 0.0, "y1": 0.3, "x2": 0.35, "y2": 0.7},
                "ew_out": {"x1": 0.65, "y1": 0.3, "x2": 1.0, "y2": 0.7},
                "ns_in": {"x1": 0.3, "y1": 0.0, "x2": 0.7, "y2": 0.35},
                "ns_out": {"x1": 0.3, "y1": 0.65, "x2": 0.7, "y2": 1.0},
            },
        ).__dict__
        for intersection in intersections
    ]
