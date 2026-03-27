"""
Seed script - Delhi Optimized.
Seeding core Delhi intersections with high-density traffic configuration.
"""
import asyncio
import random
from datetime import datetime
from typing import Any

INTERSECTIONS = [
    {"id": "int_001", "name": "Connaught Place (CP) Outer Circle", "lat": 28.6315, "lng": 77.2167, "address": "New Delhi, Delhi 110001"},
    {"id": "int_002", "name": "ITO Junction (Vikas Marg)", "lat": 28.6273, "lng": 77.2348, "address": "ITO, New Delhi, Delhi 110002"},
    {"id": "int_003", "name": "AIIMS Crossing (Ring Road)", "lat": 28.5672, "lng": 77.2100, "address": "Ansari Nagar, New Delhi, Delhi 110029"},
    {"id": "int_004", "name": "Hauz Khas Junction (August Kranti)", "lat": 28.5494, "lng": 77.2044, "address": "Hauz Khas, New Delhi, Delhi 110016"},
    {"id": "int_005", "name": "Lajpat Nagar (Moolchand Crossing)", "lat": 28.5675, "lng": 77.2345, "address": "Lajpat Nagar, New Delhi, Delhi 110024"},
    {"id": "int_006", "name": "Nehru Place Main Intersection", "lat": 28.5485, "lng": 77.2513, "address": "Nehru Place, New Delhi, Delhi 110019"},
    {"id": "int_007", "name": "Karol Bagh (Pusa Road)", "lat": 28.6443, "lng": 77.1901, "address": "Karol Bagh, New Delhi, Delhi 110005"},
    {"id": "int_008", "name": "Dwarka Sector 10 Chowk", "lat": 28.5815, "lng": 77.0592, "address": "Dwarka, New Delhi, Delhi 110075"},
    {"id": "int_009", "name": "Rohini Sector 15 Crossing", "lat": 28.7299, "lng": 77.1264, "address": "Rohini, New Delhi, Delhi 110085"},
]


async def seed_intersections(state_manager: Any) -> None:
    """Seed Delhi intersections into Redis."""
    from models.intersection import IntersectionState

    for i, data in enumerate(INTERSECTIONS):
        # Delhi specific initial densities (High Baseline)
        state = IntersectionState(
            id=data["id"],
            name=data["name"],
            lat=data["lat"],
            lng=data["lng"],
            address=data["address"],
            ew_green=(i % 2 == 0),
            ew_phase_seconds=0.0,
            ew_green_duration=random.randint(45, 55), # Delhi needs longer cycles
            ns_green_duration=random.randint(35, 45),
            cycle_length=0,
            density_ew=random.randint(25, 45),
            density_ns=random.randint(20, 35),
            queue_ew_meters=0.0,
            queue_ns_meters=0.0,
            wait_time_avg=0.0,
            throughput_per_hour=0,
            override=False,
            override_reason="",
            fault=False,
            last_updated=datetime.utcnow(),
            webster_last_calc=datetime.utcnow(),
            total_vehicles_processed=0,
        )
        state.cycle_length = state.ew_green_duration + state.ns_green_duration + 8
        await state_manager.set_intersection(state)

    print(f"✓ Seeded {len(INTERSECTIONS)} Delhi intersections")


async def main() -> None:
    """Standalone seed runner."""
    import sys
    import os
    # Add project root to path
    sys.path.insert(0, os.getcwd())
    from services.state_manager import StateManager

    sm = StateManager()
    await sm.connect()
    await seed_intersections(sm)
    await sm.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
