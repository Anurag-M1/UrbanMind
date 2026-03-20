"""Failsafe helpers for reverting signal plans to fixed-timer operation."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from config import settings
from services import state_manager

logger = logging.getLogger("urbanmind.failsafe")

_active_failsafe: set[str] = set()
_reconnect_tasks: dict[str, asyncio.Task[None]] = {}


async def initialize_failsafe_schedules() -> None:
    """Persist default fixed-timer schedules for all known intersections."""

    intersections = await state_manager.get_all_intersections()
    for state in intersections:
        await state_manager.set_fixed_timer_schedule(
            state.id,
            settings.FAILSAFE_FIXED_TIMER_EW,
            settings.FAILSAFE_FIXED_TIMER_NS,
        )
    logger.info("Initialized failsafe schedules for %d intersections", len(intersections))


async def activate_failsafe(intersection_id: str) -> None:
    """Set an intersection to fixed-timer mode and notify the dashboard."""

    from routers import ws

    if intersection_id in _active_failsafe:
        return

    state = await state_manager.get_intersection(intersection_id)
    if state is None:
        logger.warning("Cannot activate failsafe for unknown intersection %s", intersection_id)
        return

    _active_failsafe.add(intersection_id)
    state.fault = True
    state.override = False
    state.ew_green_duration = settings.FAILSAFE_FIXED_TIMER_EW
    state.ns_green_duration = settings.FAILSAFE_FIXED_TIMER_NS
    state.last_updated = datetime.utcnow()
    await state_manager.set_intersection(state)
    await ws.broadcast_fault_event(intersection_id, "Hardware fault detected. Fixed timer mode active.")

    if intersection_id not in _reconnect_tasks or _reconnect_tasks[intersection_id].done():
        _reconnect_tasks[intersection_id] = asyncio.create_task(_retry_reconnect(intersection_id))

    logger.warning("Failsafe activated for %s", intersection_id)


async def clear_failsafe(intersection_id: str) -> None:
    """Clear fault state and cancel any active reconnect loop."""

    if intersection_id in _active_failsafe:
        _active_failsafe.remove(intersection_id)

    task = _reconnect_tasks.pop(intersection_id, None)
    if task is not None:
        task.cancel()

    await state_manager.set_fault(intersection_id, False)
    logger.info("Failsafe cleared for %s", intersection_id)


async def is_failsafe_active(intersection_id: str) -> bool:
    """Return whether fixed-timer mode is active for an intersection."""

    return intersection_id in _active_failsafe


async def _retry_reconnect(intersection_id: str) -> None:
    """Attempt to restore signal hardware connectivity every 30 seconds."""

    from services.signal_controller import signal_adapter

    try:
        while intersection_id in _active_failsafe:
            await asyncio.sleep(30)
            status = await signal_adapter.read_status(intersection_id)
            if status is not None and status.connected:
                await clear_failsafe(intersection_id)
                break
    except asyncio.CancelledError:
        return
