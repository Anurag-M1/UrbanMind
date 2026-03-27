import redis.asyncio as aioredis
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from models.intersection import IntersectionState
from models.emergency import EmergencyVehicle, EmergencyEvent
from config import settings

logger = logging.getLogger("urbanmind.state")


class StateManager:
    def __init__(self) -> None:
        self.redis: Optional[aioredis.Redis] = None
        self._start_time: datetime = datetime.utcnow()

    async def connect(self) -> None:
        self.redis = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            retry_on_timeout=True,
        )
        try:
            await self.redis.ping()
            logger.info("Connected to Redis at %s", settings.REDIS_URL)
        except Exception as e:
            logger.error("Redis connection failed: %s", e)
            raise

    async def disconnect(self) -> None:
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis")

    async def is_connected(self) -> bool:
        if not self.redis:
            return False
        try:
            await self.redis.ping()
            return True
        except Exception:
            return False

    # ─── Intersection Operations ──────────────────────────────────────

    async def get_intersection(self, int_id: str) -> Optional[IntersectionState]:
        if not self.redis:
            return None
        data = await self.redis.hgetall(f"int:{int_id}")
        if not data:
            return None
        return self._deserialize_intersection(data)

    async def set_intersection(self, state: IntersectionState) -> None:
        if not self.redis:
            return
        data = self._serialize_intersection(state)
        await self.redis.hset(f"int:{state.id}", mapping=data)
        await self.redis.sadd("ints:all", state.id)

    async def get_all_intersections(self) -> List[IntersectionState]:
        if not self.redis:
            return []
        ids = await self.redis.smembers("ints:all")
        results: List[IntersectionState] = []
        for int_id in sorted(ids):
            state = await self.get_intersection(int_id)
            if state:
                results.append(state)
        return results

    async def bulk_update_intersections(self, states: List[IntersectionState]) -> None:
        if not self.redis:
            return
        pipe = self.redis.pipeline()
        for state in states:
            data = self._serialize_intersection(state)
            pipe.hset(f"int:{state.id}", mapping=data)
            pipe.sadd("ints:all", state.id)
        await pipe.execute()

    async def update_density(
        self,
        int_id: str,
        ew: int,
        ns: int,
        queue_ew: float,
        queue_ns: float,
        wait_time: float,
    ) -> None:
        if not self.redis:
            return
        now = datetime.utcnow().isoformat()
        await self.redis.hset(
            f"int:{int_id}",
            mapping={
                "density_ew": str(ew),
                "density_ns": str(ns),
                "queue_ew_meters": str(round(queue_ew, 1)),
                "queue_ns_meters": str(round(queue_ns, 1)),
                "wait_time_avg": str(round(wait_time, 2)),
                "last_updated": now,
            },
        )

    async def append_wait_time(self, int_id: str, wait_seconds: float) -> None:
        if not self.redis:
            return
        key = f"int:{int_id}:wait_history"
        await self.redis.lpush(key, str(round(wait_seconds, 2)))
        await self.redis.ltrim(key, 0, 59)

    async def get_wait_history(self, int_id: str) -> List[float]:
        if not self.redis:
            return []
        key = f"int:{int_id}:wait_history"
        values = await self.redis.lrange(key, 0, 59)
        return [float(v) for v in values]

    async def increment_vehicles(self, int_id: str, count: int) -> None:
        if not self.redis:
            return
        await self.redis.hincrby(f"int:{int_id}", "total_vehicles_processed", count)

    # ─── Override & Fault ─────────────────────────────────────────────

    async def set_override(self, int_id: str, active: bool, reason: str = "") -> None:
        if not self.redis:
            return
        await self.redis.hset(
            f"int:{int_id}",
            mapping={
                "override": "1" if active else "0",
                "override_reason": reason,
            },
        )

    async def set_fault(self, int_id: str, fault: bool) -> None:
        if not self.redis:
            return
        await self.redis.hset(f"int:{int_id}", "fault", "1" if fault else "0")

    async def set_ew_green(self, int_id: str, ew_green: bool) -> None:
        if not self.redis:
            return
        await self.redis.hset(f"int:{int_id}", "ew_green", "1" if ew_green else "0")

    # ─── Emergency Events ─────────────────────────────────────────────

    async def add_emergency_event(self, event: EmergencyEvent) -> None:
        if not self.redis:
            return
        await self.redis.lpush("emergency:events", event.model_dump_json())
        await self.redis.ltrim("emergency:events", 0, 99)

    async def get_emergency_events(self, limit: int = 50) -> List[EmergencyEvent]:
        if not self.redis:
            return []
        raw = await self.redis.lrange("emergency:events", 0, limit - 1)
        return [EmergencyEvent.model_validate_json(r) for r in raw]

    # ─── System Stats ─────────────────────────────────────────────────

    async def get_system_stats(self) -> Dict[str, Any]:
        if not self.redis:
            return {}
        stats = await self.redis.hgetall("system:stats")
        return stats

    async def update_system_stats(self, **kwargs: Any) -> None:
        if not self.redis:
            return
        mapping = {k: str(v) for k, v in kwargs.items()}
        if mapping:
            await self.redis.hset("system:stats", mapping=mapping)

    async def increment_stat(self, key: str, amount: int = 1) -> None:
        if not self.redis:
            return
        await self.redis.hincrby("system:stats", key, amount)

    # ─── Reset ────────────────────────────────────────────────────────

    async def reset_all(self) -> None:
        if not self.redis:
            return
        ids = await self.redis.smembers("ints:all")
        pipe = self.redis.pipeline()
        for int_id in ids:
            pipe.delete(f"int:{int_id}")
            pipe.delete(f"int:{int_id}:wait_history")
        pipe.delete("ints:all")
        pipe.delete("emergency:events")
        pipe.delete("system:stats")
        await pipe.execute()
        logger.info("Reset all state in Redis")

    # ─── Serialization Helpers ────────────────────────────────────────

    def _serialize_intersection(self, state: IntersectionState) -> Dict[str, str]:
        return {
            "id": state.id,
            "name": state.name,
            "lat": str(state.lat),
            "lng": str(state.lng),
            "address": state.address,
            "ew_green": "1" if state.ew_green else "0",
            "ew_phase_seconds": str(state.ew_phase_seconds),
            "ew_green_duration": str(state.ew_green_duration),
            "ns_green_duration": str(state.ns_green_duration),
            "cycle_length": str(state.cycle_length),
            "density_ew": str(state.density_ew),
            "density_ns": str(state.density_ns),
            "queue_ew_meters": str(state.queue_ew_meters),
            "queue_ns_meters": str(state.queue_ns_meters),
            "wait_time_avg": str(state.wait_time_avg),
            "throughput_per_hour": str(state.throughput_per_hour),
            "override": "1" if state.override else "0",
            "override_reason": state.override_reason,
            "fault": "1" if state.fault else "0",
            "last_updated": state.last_updated.isoformat(),
            "webster_last_calc": state.webster_last_calc.isoformat(),
            "total_vehicles_processed": str(state.total_vehicles_processed),
        }

    def _deserialize_intersection(self, data: Dict[str, str]) -> IntersectionState:
        wait_history: List[float] = []
        return IntersectionState(
            id=data.get("id", ""),
            name=data.get("name", ""),
            lat=float(data.get("lat", 0)),
            lng=float(data.get("lng", 0)),
            address=data.get("address", ""),
            ew_green=data.get("ew_green") == "1",
            ew_phase_seconds=float(data.get("ew_phase_seconds", 0)),
            ew_green_duration=int(float(data.get("ew_green_duration", 30))),
            ns_green_duration=int(float(data.get("ns_green_duration", 25))),
            cycle_length=int(float(data.get("cycle_length", 59))),
            density_ew=int(float(data.get("density_ew", 0))),
            density_ns=int(float(data.get("density_ns", 0))),
            queue_ew_meters=float(data.get("queue_ew_meters", 0)),
            queue_ns_meters=float(data.get("queue_ns_meters", 0)),
            wait_time_avg=float(data.get("wait_time_avg", 0)),
            wait_time_history=wait_history,
            throughput_per_hour=int(float(data.get("throughput_per_hour", 0))),
            override=data.get("override") == "1",
            override_reason=data.get("override_reason", ""),
            fault=data.get("fault") == "1",
            last_updated=datetime.fromisoformat(
                data.get("last_updated", datetime.utcnow().isoformat())
            ),
            webster_last_calc=datetime.fromisoformat(
                data.get("webster_last_calc", datetime.utcnow().isoformat())
            ),
            total_vehicles_processed=int(
                float(data.get("total_vehicles_processed", 0))
            ),
        )


state_manager = StateManager()
