"""Webster signal optimization logic and periodic recalculation loop."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from config import settings
from models.intersection import SignalCommand
from services import state_manager

logger = logging.getLogger("urbanmind.webster")

SATURATION_FLOW_RATE = 1800.0
LOST_TIME_PER_PHASE = 4.0
PHASE_COUNT = 2
MIN_GREEN = 10
MAX_GREEN = 60

_last_recalculation = datetime.utcnow()


def get_last_recalculation_timestamp() -> str:
    """Return the most recent optimizer timestamp as ISO-8601 text."""

    return _last_recalculation.isoformat()


def calculate_optimal_timings(density_ew: int, density_ns: int) -> dict[str, int]:
    """Calculate Webster timings using 10-second counts converted to hourly flow."""

    if density_ew < 0 or density_ns < 0:
        raise ValueError("Density inputs must be non-negative")

    lost_time = LOST_TIME_PER_PHASE * PHASE_COUNT
    flow_ew = float(density_ew * 6 * 60)
    flow_ns = float(density_ns * 6 * 60)

    y_ew = flow_ew / SATURATION_FLOW_RATE if SATURATION_FLOW_RATE else 0.0
    y_ns = flow_ns / SATURATION_FLOW_RATE if SATURATION_FLOW_RATE else 0.0
    total_y = y_ew + y_ns

    if total_y <= 0:
        cycle_length = int(lost_time + 2 * settings.SIGNAL_CYCLE_DEFAULT_EW)
        return {
            "ew_green": settings.SIGNAL_CYCLE_DEFAULT_EW,
            "ns_green": settings.SIGNAL_CYCLE_DEFAULT_NS,
            "cycle_length": cycle_length,
        }

    if total_y >= 1:
        total_y = 0.95

    denominator = 1 - total_y
    if denominator <= 0:
        denominator = 0.05

    cycle_length = (1.5 * lost_time + 5) / denominator
    effective_green = max(cycle_length - lost_time, MIN_GREEN * 2)

    ew_green = effective_green * (y_ew / total_y)
    ns_green = effective_green * (y_ns / total_y)

    ew_green_clamped = max(MIN_GREEN, min(MAX_GREEN, int(round(ew_green))))
    ns_green_clamped = max(MIN_GREEN, min(MAX_GREEN, int(round(ns_green))))
    cycle_value = max(int(round(cycle_length)), ew_green_clamped + ns_green_clamped + int(lost_time))

    return {
        "ew_green": ew_green_clamped,
        "ns_green": ns_green_clamped,
        "cycle_length": cycle_value,
    }


async def webster_optimizer_loop() -> None:
    """Run Webster recalculation for all non-overridden, non-faulted intersections."""

    from services.signal_controller import publish_signal_command
    from routers import ws

    global _last_recalculation

    while True:
        try:
            intersections = await state_manager.get_all_intersections()
            for state in intersections:
                if state.override or state.fault:
                    continue

                timings = calculate_optimal_timings(state.density_ew, state.density_ns)
                changed = (
                    state.ew_green_duration != timings["ew_green"]
                    or state.ns_green_duration != timings["ns_green"]
                )
                state.ew_green_duration = timings["ew_green"]
                state.ns_green_duration = timings["ns_green"]
                state.last_updated = datetime.utcnow()
                await state_manager.set_intersection(state)

                if changed:
                    command = SignalCommand(
                        intersection_id=state.id,
                        ew_green_duration=timings["ew_green"],
                        ns_green_duration=timings["ns_green"],
                        immediate=False,
                    )
                    await publish_signal_command(command)
                    logger.info(
                        "Webster recalculation %s at %s -> EW=%ss NS=%ss cycle=%ss",
                        state.id,
                        state.last_updated.isoformat(),
                        timings["ew_green"],
                        timings["ns_green"],
                        timings["cycle_length"],
                    )

            _last_recalculation = datetime.utcnow()
            ws.set_last_webster_recalc(_last_recalculation.isoformat())
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("Webster optimizer loop failed: %s", exc, exc_info=True)
        await asyncio.sleep(settings.WEBSTER_RECALC_INTERVAL)
