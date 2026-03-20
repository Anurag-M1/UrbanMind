"""Traffic and emergency simulator for UrbanMind demos and development."""

from __future__ import annotations

import asyncio
import json
import logging
import math
import os
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import httpx

logger = logging.getLogger("urbanmind.simulator")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

BASE_URL = os.getenv("API_URL", "http://api:8000")
SIMULATOR_DIR = Path(__file__).resolve().parent
SCENARIO_RUSH = SIMULATOR_DIR / "scenario_rush_hour.json"
SCENARIO_EMERGENCY = SIMULATOR_DIR / "scenario_emergency.json"


class RushHourPattern:
    """Hourly multiplier table used to emulate Indian city traffic demand."""

    hour_multiplier = {
        6: 0.3,
        7: 0.6,
        8: 0.9,
        9: 1.0,
        10: 0.7,
        11: 0.6,
        12: 0.55,
        13: 0.5,
        14: 0.4,
        15: 0.55,
        16: 0.7,
        17: 0.85,
        18: 1.0,
        19: 0.8,
        20: 0.55,
    }
    base_ew_flow = 15
    base_ns_flow = 12

    @classmethod
    def multiplier_for_hour(cls, hour: int) -> float:
        return cls.hour_multiplier.get(hour, 0.35)


@dataclass
class IntersectionSimulator:
    """Live traffic generator for a single intersection."""

    intersection_id: str
    grid_x: int
    grid_y: int

    def sample_counts(self, now: datetime) -> tuple[int, int]:
        """Generate realistic E-W and N-S vehicle counts for a 10-second sample."""

        multiplier = RushHourPattern.multiplier_for_hour(now.hour)
        directional_bias = 1.0 + ((self.grid_x - self.grid_y) * 0.08)
        noise_ew = random.uniform(0.8, 1.2)
        noise_ns = random.uniform(0.8, 1.2)

        ew = max(1, int(RushHourPattern.base_ew_flow * multiplier * directional_bias * noise_ew))
        ns = max(1, int(RushHourPattern.base_ns_flow * multiplier * (2 - directional_bias) * noise_ns))
        return ew, ns

    def sample_queue(self, count: int) -> float:
        """Estimate queue length in meters from count."""

        return round(count * random.uniform(3.6, 5.4), 1)


class EmergencySimulator:
    """Playback of a prerecorded emergency GPS route."""

    def __init__(self, scenario_path: Path) -> None:
        self.scenario_path = scenario_path

    async def trigger(self, client: httpx.AsyncClient) -> None:
        """Register and stream the prerecorded ambulance route."""

        points = json.loads(self.scenario_path.read_text())
        vehicle_id = f"sim-ambulance-{int(datetime.utcnow().timestamp())}"

        await client.post(
            f"{BASE_URL}/api/v1/emergency/register",
            json={"vehicle_id": vehicle_id, "type": "ambulance"},
        )

        for point in points:
            await client.post(
                f"{BASE_URL}/api/v1/emergency/gps-update",
                json={
                    "vehicle_id": vehicle_id,
                    "lat": point["lat"],
                    "lng": point["lng"],
                    "speed": point.get("speed", 60),
                    "heading": point.get("heading", 0),
                },
            )
            await asyncio.sleep(1)


async def post_density(client: httpx.AsyncClient, intersection_id: str, lane: str, count: int, queue: float) -> None:
    """Send a simulated density update to the backend."""

    await client.post(
        f"{BASE_URL}/api/v1/signals/density",
        json={
            "intersection_id": intersection_id,
            "lane": lane,
            "count": count,
            "queue_meters": queue,
            "confidence": 0.92,
        },
    )


async def bootstrap_intersections(client: httpx.AsyncClient) -> list[str]:
    """Fetch the currently registered intersections from the backend."""

    response = await client.get(f"{BASE_URL}/api/v1/signals/intersections")
    payload = response.json()
    return [item["id"] for item in payload["data"]]


async def run_density_simulator() -> None:
    """Run the 3x3 network density simulation every 5 seconds."""

    async with httpx.AsyncClient(timeout=15.0) as client:
        intersection_ids = await bootstrap_intersections(client)
        simulators = [
            IntersectionSimulator(intersection_id=intersection_id, grid_x=index % 3, grid_y=index // 3)
            for index, intersection_id in enumerate(intersection_ids[:9])
        ]

        while True:
            now = datetime.utcnow()
            for simulator in simulators:
                ew_count, ns_count = simulator.sample_counts(now)
                await post_density(client, simulator.intersection_id, "ew", ew_count, simulator.sample_queue(ew_count))
                await post_density(client, simulator.intersection_id, "ns", ns_count, simulator.sample_queue(ns_count))
            await asyncio.sleep(5)


async def main() -> None:
    """Start both density and emergency simulation tasks."""

    emergency_simulator = EmergencySimulator(SCENARIO_EMERGENCY)

    async with httpx.AsyncClient(timeout=15.0) as client:
        rush_hour_task = asyncio.create_task(run_density_simulator())

        scenario = json.loads(SCENARIO_RUSH.read_text())
        if scenario.get("trigger_emergency_demo", True):
            await asyncio.sleep(5)
            await emergency_simulator.trigger(client)

        await rush_hour_task


if __name__ == "__main__":
    asyncio.run(main())
