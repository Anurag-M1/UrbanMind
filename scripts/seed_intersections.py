"""Seed nine Bhilai/Durg intersections into both the API and Redis directly."""

from __future__ import annotations

import asyncio
import os
import random
from datetime import datetime

import httpx
import redis.asyncio as redis

API_URL = os.getenv("API_URL", "http://localhost:8000")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

INTERSECTIONS = [
    {"id": "int_001", "name": "Sector 1 Chowk", "lat": 21.194, "lng": 81.378},
    {"id": "int_002", "name": "Civic Centre Signal", "lat": 21.198, "lng": 81.382},
    {"id": "int_003", "name": "Nehru Nagar Crossing", "lat": 21.202, "lng": 81.386},
    {"id": "int_004", "name": "Steel Plant Gate #3", "lat": 21.190, "lng": 81.374},
    {"id": "int_005", "name": "Supela Main Junction", "lat": 21.194, "lng": 81.370},
    {"id": "int_006", "name": "Durg Station Road", "lat": 21.186, "lng": 81.279},
    {"id": "int_007", "name": "Smriti Nagar Signal", "lat": 21.207, "lng": 81.389},
    {"id": "int_008", "name": "Risali Chowk", "lat": 21.182, "lng": 81.361},
    {"id": "int_009", "name": "Bhilai Nagar Crossing", "lat": 21.215, "lng": 81.396}
]


async def seed() -> None:
    """Populate backend API and Redis with the required nine intersections."""

    redis_client = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

    async with httpx.AsyncClient(timeout=15.0) as client:
        for _ in range(20):
            try:
                health = await client.get(f"{API_URL}/health")
                if health.status_code == 200:
                    break
            except Exception:
                pass
            await asyncio.sleep(2)

        for index, intersection in enumerate(INTERSECTIONS):
            payload = {
                **intersection,
                "ew_green": index % 2 == 0,
                "ew_phase_seconds": 0.0,
                "ew_green_duration": 30,
                "ns_green_duration": 25,
                "density_ew": random.randint(5, 20),
                "density_ns": random.randint(5, 20),
                "queue_ew": round(random.uniform(18, 60), 1),
                "queue_ns": round(random.uniform(18, 60), 1),
                "wait_time_avg": round(random.uniform(12, 38), 1),
                "override": False,
                "fault": False,
            }

            for _ in range(5):
                try:
                    response = await client.post(f"{API_URL}/api/v1/intersections/", json=payload)
                    response.raise_for_status()
                    break
                except Exception:
                    await asyncio.sleep(1)
            await redis_client.hset(
                f"intersection:{payload['id']}",
                mapping={
                    **{key: str(value) for key, value in payload.items()},
                    "last_updated": datetime.utcnow().isoformat(),
                },
            )
            await redis_client.sadd("intersections:all", payload["id"])

    close_method = getattr(redis_client, "aclose", None)
    if close_method is not None:
        await close_method()
    else:
        await redis_client.close()


if __name__ == "__main__":
    asyncio.run(seed())
