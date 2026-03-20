"""Async Redis-backed state and analytics storage for UrbanMind."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Sequence

import redis.asyncio as redis

from config import settings
from models.emergency import EmergencyEvent
from models.intersection import DensityUpdate, IntersectionState

logger = logging.getLogger("urbanmind.state_manager")

INTERSECTIONS_SET_KEY = "intersections:all"
WAIT_TIMES_KEY_PREFIX = "wait_times:"
FLOW_KEY_PREFIX = "flow:"
EMERGENCY_EVENTS_KEY = "emergency:events"
SYSTEM_STATS_KEY = "system:stats"
FIXED_SCHEDULE_KEY_PREFIX = "failsafe:"

_redis: redis.Redis | None = None


@dataclass(frozen=True)
class FlowSample:
    """Stored flow sample for analytics rollups."""

    timestamp: str
    value: float


async def get_redis() -> redis.Redis:
    """Return the shared async Redis client, creating it on first use."""

    global _redis
    if _redis is None:
        _redis = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis


async def connect_redis() -> bool:
    """Open and validate the Redis connection."""

    try:
        client = await get_redis()
        await client.ping()
        logger.info("Redis connected: %s", settings.REDIS_URL)
        return True
    except Exception as exc:
        logger.error("Redis connection failed: %s", exc)
        return False


async def ping_redis() -> bool:
    """Check whether Redis is reachable."""

    try:
        client = await get_redis()
        return bool(await client.ping())
    except Exception as exc:
        logger.error("Redis ping failed: %s", exc)
        return False


async def close_redis() -> None:
    """Close the shared Redis client."""

    global _redis
    if _redis is None:
        return
    await _redis.aclose()
    _redis = None
    logger.info("Redis client closed")


def _intersection_key(intersection_id: str) -> str:
    return f"intersection:{intersection_id}"


def _wait_time_key(intersection_id: str) -> str:
    return f"{WAIT_TIMES_KEY_PREFIX}{intersection_id}"


def _flow_key(intersection_id: str) -> str:
    return f"{FLOW_KEY_PREFIX}{intersection_id}"


def _serialize_mapping(data: dict[str, Any]) -> dict[str, str]:
    """Serialize a Python mapping for Redis hash storage."""

    serialized: dict[str, str] = {}
    for key, value in data.items():
        if isinstance(value, datetime):
            serialized[key] = value.isoformat()
        elif isinstance(value, (dict, list)):
            serialized[key] = json.dumps(value)
        else:
            serialized[key] = str(value)
    return serialized


def _parse_bool(value: str | None) -> bool:
    return value is not None and value.lower() == "true"


def _deserialize_intersection(payload: dict[str, str]) -> IntersectionState:
    """Convert a Redis hash payload back into an IntersectionState."""

    return IntersectionState(
        id=payload["id"],
        name=payload["name"],
        lat=float(payload["lat"]),
        lng=float(payload["lng"]),
        ew_green=_parse_bool(payload.get("ew_green")),
        ew_phase_seconds=float(payload.get("ew_phase_seconds", "0")),
        ew_green_duration=int(payload.get("ew_green_duration", settings.SIGNAL_CYCLE_DEFAULT_EW)),
        ns_green_duration=int(payload.get("ns_green_duration", settings.SIGNAL_CYCLE_DEFAULT_NS)),
        density_ew=int(payload.get("density_ew", "0")),
        density_ns=int(payload.get("density_ns", "0")),
        queue_ew=float(payload.get("queue_ew", "0")),
        queue_ns=float(payload.get("queue_ns", "0")),
        wait_time_avg=float(payload.get("wait_time_avg", "0")),
        override=_parse_bool(payload.get("override")),
        fault=_parse_bool(payload.get("fault")),
        last_updated=datetime.fromisoformat(payload["last_updated"]),
    )


async def get_intersection(intersection_id: str) -> IntersectionState | None:
    """Fetch one intersection from Redis, or None when absent or on error."""

    try:
        client = await get_redis()
        payload = await client.hgetall(_intersection_key(intersection_id))
        if not payload:
            return None
        return _deserialize_intersection(payload)
    except Exception as exc:
        logger.error("Failed to fetch intersection %s: %s", intersection_id, exc)
        return None


async def set_intersection(state: IntersectionState) -> None:
    """Persist an intersection state and register its ID in the global set."""

    try:
        client = await get_redis()
        mapping = _serialize_mapping(state.model_dump())
        await client.hset(_intersection_key(state.id), mapping=mapping)
        await client.sadd(INTERSECTIONS_SET_KEY, state.id)
    except Exception as exc:
        logger.error("Failed to store intersection %s: %s", state.id, exc)
        raise


async def get_all_intersections() -> List[IntersectionState]:
    """Return all known intersections sorted by ID."""

    try:
        client = await get_redis()
        intersection_ids = sorted(await client.smembers(INTERSECTIONS_SET_KEY))
        results: list[IntersectionState] = []
        for intersection_id in intersection_ids:
            state = await get_intersection(intersection_id)
            if state is not None:
                results.append(state)
        return results
    except Exception as exc:
        logger.error("Failed to fetch all intersections: %s", exc)
        return []


async def delete_intersection(intersection_id: str) -> bool:
    """Remove an intersection and its membership entry."""

    try:
        client = await get_redis()
        deleted = await client.delete(_intersection_key(intersection_id))
        await client.srem(INTERSECTIONS_SET_KEY, intersection_id)
        return deleted > 0
    except Exception as exc:
        logger.error("Failed to delete intersection %s: %s", intersection_id, exc)
        return False


async def update_density(intersection_id: str, lane: str, count: int, queue: float) -> None:
    """Update density and queue information for a single lane."""

    try:
        state = await get_intersection(intersection_id)
        if state is None:
            logger.warning("Density update skipped for unknown intersection %s", intersection_id)
            return

        if lane == "ew":
            state.density_ew = count
            state.queue_ew = queue
        else:
            state.density_ns = count
            state.queue_ns = queue

        state.wait_time_avg = await get_avg_wait_time(intersection_id)
        state.last_updated = datetime.utcnow()
        await set_intersection(state)
    except Exception as exc:
        logger.error("Failed to update density for %s: %s", intersection_id, exc)


async def apply_density_update(update: DensityUpdate) -> None:
    """Persist a density update and store associated analytics samples."""

    await update_density(update.intersection_id, update.lane, update.count, update.queue_meters)
    state = await get_intersection(update.intersection_id)
    if state is None:
        return
    await record_flow_sample(update.intersection_id, state.density_ew + state.density_ns)
    await record_wait_time(update.intersection_id, max(state.queue_ew, state.queue_ns) * 1.8)


async def set_override(intersection_id: str, active: bool) -> None:
    """Enable or disable emergency override mode."""

    try:
        state = await get_intersection(intersection_id)
        if state is None:
            return
        state.override = active
        state.last_updated = datetime.utcnow()
        await set_intersection(state)
    except Exception as exc:
        logger.error("Failed to set override for %s: %s", intersection_id, exc)


async def set_fault(intersection_id: str, fault: bool) -> None:
    """Set or clear fault state for an intersection."""

    try:
        state = await get_intersection(intersection_id)
        if state is None:
            return
        state.fault = fault
        state.last_updated = datetime.utcnow()
        await set_intersection(state)
    except Exception as exc:
        logger.error("Failed to set fault for %s: %s", intersection_id, exc)


async def record_wait_time(intersection_id: str, wait_seconds: float) -> None:
    """Append a wait-time sample while keeping only the latest 1000 entries."""

    try:
        client = await get_redis()
        key = _wait_time_key(intersection_id)
        sample = json.dumps({"timestamp": datetime.utcnow().isoformat(), "value": wait_seconds})
        await client.lpush(key, sample)
        await client.ltrim(key, 0, 999)
        state = await get_intersection(intersection_id)
        if state is not None:
            state.wait_time_avg = await get_avg_wait_time(intersection_id)
            state.last_updated = datetime.utcnow()
            await set_intersection(state)
    except Exception as exc:
        logger.error("Failed to record wait time for %s: %s", intersection_id, exc)


async def get_avg_wait_time(intersection_id: str) -> float:
    """Calculate average wait time from the retained samples."""

    try:
        client = await get_redis()
        raw_samples = await client.lrange(_wait_time_key(intersection_id), 0, -1)
        if not raw_samples:
            return 0.0
        values = [float(json.loads(item)["value"]) for item in raw_samples]
        return round(sum(values) / len(values), 2)
    except Exception as exc:
        logger.error("Failed to compute average wait time for %s: %s", intersection_id, exc)
        return 0.0


async def get_wait_time_series(intersection_id: str | None = None, limit: int = 500) -> List[dict[str, float | str]]:
    """Fetch wait time points for one or all intersections."""

    try:
        if intersection_id is not None:
            target_ids: Sequence[str] = [intersection_id]
        else:
            target_ids = [state.id for state in await get_all_intersections()]

        client = await get_redis()
        results: list[dict[str, float | str]] = []
        for target_id in target_ids:
            for raw in await client.lrange(_wait_time_key(target_id), 0, limit - 1):
                sample = json.loads(raw)
                results.append(
                    {
                        "timestamp": sample["timestamp"],
                        "value": float(sample["value"]),
                        "intersection_id": target_id,
                    }
                )
        results.sort(key=lambda item: str(item["timestamp"]))
        return results
    except Exception as exc:
        logger.error("Failed to fetch wait time series: %s", exc)
        return []


async def record_flow_sample(intersection_id: str, total_flow: int) -> None:
    """Append a flow sample for analytics, keeping the latest 5000 items."""

    try:
        client = await get_redis()
        sample = json.dumps({"timestamp": datetime.utcnow().isoformat(), "value": total_flow})
        await client.lpush(_flow_key(intersection_id), sample)
        await client.ltrim(_flow_key(intersection_id), 0, 4999)
    except Exception as exc:
        logger.error("Failed to record flow sample for %s: %s", intersection_id, exc)


async def get_flow_series(intersection_id: str | None = None, limit: int = 500) -> List[dict[str, float | str]]:
    """Fetch flow samples for one or all intersections."""

    try:
        if intersection_id is not None:
            target_ids: Sequence[str] = [intersection_id]
        else:
            target_ids = [state.id for state in await get_all_intersections()]

        client = await get_redis()
        results: list[dict[str, float | str]] = []
        for target_id in target_ids:
            for raw in await client.lrange(_flow_key(target_id), 0, limit - 1):
                sample = json.loads(raw)
                results.append(
                    {
                        "timestamp": sample["timestamp"],
                        "value": float(sample["value"]),
                        "intersection_id": target_id,
                    }
                )
        results.sort(key=lambda item: str(item["timestamp"]))
        return results
    except Exception as exc:
        logger.error("Failed to fetch flow series: %s", exc)
        return []


async def record_emergency_event(event: EmergencyEvent) -> None:
    """Append an emergency event for analytics and incident history."""

    try:
        client = await get_redis()
        await client.lpush(EMERGENCY_EVENTS_KEY, event.model_dump_json())
        await client.ltrim(EMERGENCY_EVENTS_KEY, 0, 999)
    except Exception as exc:
        logger.error("Failed to record emergency event %s: %s", event.id, exc)


async def get_emergency_events(limit: int = 100) -> List[EmergencyEvent]:
    """Return recent emergency events from Redis."""

    try:
        client = await get_redis()
        events: list[EmergencyEvent] = []
        for raw in await client.lrange(EMERGENCY_EVENTS_KEY, 0, limit - 1):
            events.append(EmergencyEvent.model_validate_json(raw))
        return events
    except Exception as exc:
        logger.error("Failed to fetch emergency events: %s", exc)
        return []


async def set_fixed_timer_schedule(intersection_id: str, ew_green: int, ns_green: int) -> None:
    """Persist a fixed timer schedule used by failsafe mode."""

    try:
        client = await get_redis()
        await client.hset(
            f"{FIXED_SCHEDULE_KEY_PREFIX}{intersection_id}",
            mapping=_serialize_mapping(
                {
                    "intersection_id": intersection_id,
                    "ew_green_duration": ew_green,
                    "ns_green_duration": ns_green,
                    "timestamp": datetime.utcnow(),
                }
            ),
        )
    except Exception as exc:
        logger.error("Failed to store fixed schedule for %s: %s", intersection_id, exc)


async def get_fixed_timer_schedule(intersection_id: str) -> dict[str, str] | None:
    """Fetch a persisted fixed timer schedule."""

    try:
        client = await get_redis()
        payload = await client.hgetall(f"{FIXED_SCHEDULE_KEY_PREFIX}{intersection_id}")
        return payload or None
    except Exception as exc:
        logger.error("Failed to fetch fixed schedule for %s: %s", intersection_id, exc)
        return None


async def get_network_average_wait() -> float:
    """Calculate the average wait across the full network."""

    intersections = await get_all_intersections()
    if not intersections:
        return 0.0
    values = [await get_avg_wait_time(state.id) for state in intersections]
    return round(sum(values) / len(values), 2) if values else 0.0


async def get_total_detected_vehicles() -> int:
    """Return the current live vehicle count across all intersections."""

    intersections = await get_all_intersections()
    return sum(state.density_ew + state.density_ns for state in intersections)
