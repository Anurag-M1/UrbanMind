"""Analytics API exposing wait times, flow series, emergency events, and summaries."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from services import state_manager
from services.emergency_manager import emergency_manager

router = APIRouter(prefix="/analytics", tags=["analytics"])


class TimeSeriesPoint(BaseModel):
    """Single analytics point for charts."""

    timestamp: str
    value: float
    intersection_id: str | None = None


class TimeSeriesResponse(BaseModel):
    """Timestamped analytics series response."""

    data: list[TimeSeriesPoint]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SummaryData(BaseModel):
    """Aggregate analytics summary for a selected range."""

    peak_hour_identified: str
    best_intersection: str
    worst_intersection: str
    total_emergency_events: int
    cumulative_emissions_saved: float


class SummaryResponse(BaseModel):
    """Timestamped analytics summary response."""

    data: SummaryData
    timestamp: datetime = Field(default_factory=datetime.utcnow)


@router.get("/wait-times", response_model=TimeSeriesResponse)
async def wait_times(
    _from: str | None = Query(default=None, alias="from"),
    _to: str | None = Query(default=None, alias="to"),
    intersection_id: str | None = None,
) -> TimeSeriesResponse:
    """Return wait time points as chart-ready series."""

    points = [TimeSeriesPoint(**item) for item in await state_manager.get_wait_time_series(intersection_id)]
    return TimeSeriesResponse(data=points)


@router.get("/flow", response_model=TimeSeriesResponse)
async def flow(
    _from: str | None = Query(default=None, alias="from"),
    _to: str | None = Query(default=None, alias="to"),
    intersection_id: str | None = None,
) -> TimeSeriesResponse:
    """Return flow points as chart-ready series."""

    points = [TimeSeriesPoint(**item) for item in await state_manager.get_flow_series(intersection_id)]
    return TimeSeriesResponse(data=points)


@router.get("/emergency-events", response_model=TimeSeriesResponse)
async def emergency_events(
    _from: str | None = Query(default=None, alias="from"),
    _to: str | None = Query(default=None, alias="to"),
) -> TimeSeriesResponse:
    """Return emergency event counts as time-series data."""

    events = await state_manager.get_emergency_events(100)
    points = [
        TimeSeriesPoint(timestamp=event.timestamp.isoformat(), value=1.0, intersection_id=event.intersection_id)
        for event in events
    ]
    return TimeSeriesResponse(data=points)


@router.get("/summary", response_model=SummaryResponse)
async def summary() -> SummaryResponse:
    """Return high-level analytics summary cards."""

    intersections = await state_manager.get_all_intersections()
    if intersections:
        best = min(intersections, key=lambda item: item.wait_time_avg)
        worst = max(intersections, key=lambda item: item.wait_time_avg)
    else:
        best = worst = None

    avg_wait = await state_manager.get_network_average_wait()
    baseline = 45.0
    emissions_saved = max(0.0, ((baseline - avg_wait) / baseline) * 100) if baseline else 0.0

    return SummaryResponse(
        data=SummaryData(
            peak_hour_identified="08:30",
            best_intersection=best.name if best is not None else "N/A",
            worst_intersection=worst.name if worst is not None else "N/A",
            total_emergency_events=len(emergency_manager.recent_events(100)),
            cumulative_emissions_saved=round(emissions_saved, 2),
        )
    )
