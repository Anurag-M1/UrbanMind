import logging
import random
from typing import Optional
from datetime import datetime

from fastapi import APIRouter

from services.state_manager import state_manager
from services.emergency_manager import emergency_manager

logger = logging.getLogger("urbanmind.router.analytics")
router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

BASELINE_WAIT = 45.0  # Fixed timer baseline in seconds


@router.get("/wait-times")
async def get_wait_times(intersection_id: str = "all", window: int = 60):
    """Get wait time data for intersections."""
    intersections = await state_manager.get_all_intersections()
    results = []

    for intersection in intersections:
        if intersection_id != "all" and intersection.id != intersection_id:
            continue
        history = await state_manager.get_wait_history(intersection.id)
        results.append({
            "intersection_id": intersection.id,
            "intersection_name": intersection.name,
            "avg_wait": intersection.wait_time_avg,
            "history": history[:window],
        })

    return {"wait_times": results}


@router.get("/density-heatmap")
async def get_density_heatmap():
    """Get density data formatted for heatmap visualization."""
    intersections = await state_manager.get_all_intersections()
    max_density = max(
        (i.density_ew + i.density_ns for i in intersections), default=1
    )
    max_density = max(max_density, 1)

    return {
        "heatmap": [
            {
                "intersection_id": i.id,
                "name": i.name,
                "lat": i.lat,
                "lng": i.lng,
                "intensity": round(
                    (i.density_ew + i.density_ns) / max_density, 3
                ),
                "density_ew": i.density_ew,
                "density_ns": i.density_ns,
            }
            for i in intersections
        ]
    }


@router.get("/summary")
async def get_analytics_summary():
    """Get comprehensive analytics summary."""
    intersections = await state_manager.get_all_intersections()

    if not intersections:
        return {
            "network_avg_wait_seconds": 0,
            "baseline_wait_seconds": BASELINE_WAIT,
            "wait_reduction_pct": 0,
            "total_vehicles_processed": 0,
            "total_emergency_events": 0,
            "emissions_saved_pct": 0,
        }

    avg_wait = sum(i.wait_time_avg for i in intersections) / len(intersections)
    wait_reduction = max(0, ((BASELINE_WAIT - avg_wait) / BASELINE_WAIT) * 100)
    total_vehicles = sum(i.total_vehicles_processed for i in intersections)

    # Find best and worst intersections
    sorted_by_wait = sorted(intersections, key=lambda x: x.wait_time_avg)
    best = sorted_by_wait[0]
    worst = sorted_by_wait[-1]
    peak_density = max(intersections, key=lambda x: x.density_ew + x.density_ns)

    events = emergency_manager.get_event_history()
    stats = await state_manager.get_system_stats()
    
    # Use the synced total from system stats if available
    total_vehicles_synced = int(
        stats.get(
            "vision_total_vehicles_detected",
            stats.get("total_vehicles_processed", stats.get("total_vehicles", total_vehicles))
        )
    )

    return {
        "network_avg_wait_seconds": int(round(avg_wait)),
        "baseline_wait_seconds": int(round(BASELINE_WAIT)),
        "wait_reduction_pct": int(round(wait_reduction)),
        "total_vehicles_processed": total_vehicles_synced,
        "total_emergency_events": len(events),
        "emissions_saved_pct": int(round(wait_reduction * 0.7)),  # proportional estimate
        "best_intersection": {
            "id": best.id,
            "name": best.name,
            "avg_wait": best.wait_time_avg,
        },
        "worst_intersection": {
            "id": worst.id,
            "name": worst.name,
            "avg_wait": worst.wait_time_avg,
        },
        "peak_density_intersection": {
            "id": peak_density.id,
            "name": peak_density.name,
            "density": peak_density.density_ew + peak_density.density_ns,
        },
        "webster_recalculations_today": int(
            stats.get("webster_recalculations", 0)
        ),
        "uptime_hours": int(round(
            float(stats.get("uptime_seconds", 0)) / 3600
        )),
    }


@router.get("/flow-series")
async def get_flow_series():
    """Get hourly vehicle flow for charting."""
    # Generate realistic hour-by-hour flow based on rush hour patterns
    from services.simulator import RUSH_HOUR_PATTERN

    hour_data = []
    for hour in range(24):
        mult = RUSH_HOUR_PATTERN.get(hour, 0.5)
        base_ew = int(420 * mult * (0.9 + random.random() * 0.2))
        base_ns = int(350 * mult * (0.9 + random.random() * 0.2))
        hour_data.append({
            "hour": hour,
            "ew_flow": base_ew,
            "ns_flow": base_ns,
            "total": base_ew + base_ns,
        })

    return {"flow_series": hour_data}
