from __future__ import annotations

import json
import logging
import os
from collections import defaultdict, deque
from typing import Any

try:
    from redis import Redis
except ImportError:  # pragma: no cover - optional dependency
    Redis = None


LOGGER = logging.getLogger(__name__)


class RedisStateStore:
    """Provides state and history access backed by Redis with in-memory fallback."""

    def __init__(self, url: str | None = None) -> None:
        """Initializes the state store.

        Args:
            url: Optional Redis URL.

        Returns:
            None.
        """

        self.url = url or os.getenv("REDIS_URL", "redis://127.0.0.1:6379")
        self.client = self._connect()
        self.memory_state: dict[str, dict[str, Any]] = {}
        self.memory_history: dict[str, deque[dict[str, Any]]] = defaultdict(lambda: deque(maxlen=1800))

    def _connect(self) -> Redis | None:
        """Creates a Redis client if the dependency and server are available.

        Args:
            None.

        Returns:
            Redis client or None.
        """

        if Redis is None:
            LOGGER.warning("redis dependency missing; using in-memory state store")
            return None
        try:
            client = Redis.from_url(self.url, decode_responses=True)
            client.ping()
            return client
        except Exception as exc:  # pragma: no cover - depends on infra
            LOGGER.warning("redis unavailable (%s); using in-memory state store", exc)
            return None

    def get_intersection_state(self, intersection_id: str) -> dict[str, Any] | None:
        """Fetches the latest state for one intersection.

        Args:
            intersection_id: Intersection identifier.

        Returns:
            Latest state dictionary or None.
        """

        if self.client is not None:
            payload = self.client.get(f"intersection:{intersection_id}:state")
            return None if payload is None else json.loads(payload)
        return self.memory_state.get(intersection_id)

    def set_intersection_state(self, intersection_id: str, state: dict[str, Any]) -> None:
        """Stores the latest state with a 30-second TTL.

        Args:
            intersection_id: Intersection identifier.
            state: State payload.

        Returns:
            None.
        """

        if self.client is not None:
            self.client.setex(f"intersection:{intersection_id}:state", 30, json.dumps(state))
            self.client.sadd("intersections:known", intersection_id)
            return
        self.memory_state[intersection_id] = state

    def get_all_intersection_states(self) -> list[dict[str, Any]]:
        """Fetches all known intersection states.

        Args:
            None.

        Returns:
            List of state dictionaries.
        """

        if self.client is not None:
            intersection_ids = sorted(self.client.smembers("intersections:known"))
            return [
                state
                for intersection_id in intersection_ids
                if (state := self.get_intersection_state(intersection_id)) is not None
            ]
        return [self.memory_state[key] for key in sorted(self.memory_state)]

    def append_history(self, intersection_id: str, state: dict[str, Any]) -> None:
        """Appends a state entry to rolling history storage.

        Args:
            intersection_id: Intersection identifier.
            state: State payload.

        Returns:
            None.
        """

        if self.client is not None:
            key = f"intersection:{intersection_id}:history"
            self.client.lpush(key, json.dumps(state))
            self.client.ltrim(key, 0, 1799)
            return
        self.memory_history[intersection_id].appendleft(state)

    def get_history(self, intersection_id: str, minutes: int) -> list[dict[str, Any]]:
        """Returns state history for the requested time window.

        Args:
            intersection_id: Intersection identifier.
            minutes: Number of minutes to return.

        Returns:
            List of historical state entries.
        """

        limit = max(1, min(1800, minutes * 30))
        if self.client is not None:
            key = f"intersection:{intersection_id}:history"
            return [json.loads(item) for item in self.client.lrange(key, 0, limit - 1)]
        return list(self.memory_history[intersection_id])[:limit]
