import asyncio
import random
import logging
from typing import Any, Optional, Callable, Awaitable
from datetime import datetime

logger = logging.getLogger("urbanmind.simulator")

# Rush hour multipliers by hour
RUSH_HOUR_PATTERN = {
    0: 0.15, 1: 0.10, 2: 0.08, 3: 0.08, 4: 0.12, 5: 0.25,
    6: 0.45, 7: 0.75, 8: 0.95, 9: 1.00, 10: 0.90, 11: 0.85,
    12: 0.90, 13: 0.85, 14: 0.80, 15: 0.85, 16: 0.95, 17: 1.00,
    18: 1.00, 19: 0.95, 20: 0.85, 21: 0.70, 22: 0.50, 23: 0.30,
}

# Base flows per 10-second window at peak hour (one per intersection)
# Base flows per 10-second window (Delhi Scale: High Density)
EW_BASE = [32, 45, 38, 41, 52, 36, 28, 39, 34]
NS_BASE = [28, 38, 32, 35, 48, 31, 25, 34, 30]


async def simulation_loop(
    state_manager: Any,
    ws_broadcast: Optional[Callable[..., Awaitable[None]]] = None,
    interval: int = 5,
) -> None:
    """
    Traffic density simulator: generates realistic traffic data every `interval` seconds.
    Uses rush-hour patterns with random noise.
    """
    logger.info("Traffic simulator started (interval=%ds)", interval)
    tick_count = 0

    while True:
        try:
            intersections = await state_manager.get_all_intersections()
            if not intersections:
                await asyncio.sleep(interval)
                continue

            hour = datetime.now().hour
            multiplier = RUSH_HOUR_PATTERN.get(hour, 0.5)
            # For demo, always show active traffic
            multiplier = max(multiplier, 0.45)

            updates = []
            total_vehicles = 0

            for i, intersection in enumerate(intersections):
                if intersection.override:
                    updates.append(intersection)
                    continue

                idx = i % len(EW_BASE)
                noise_ew = 0.8 + random.random() * 0.4  # ±20% noise
                noise_ns = 0.8 + random.random() * 0.4

                ew = max(1, int(EW_BASE[idx] * multiplier * noise_ew))
                ns = max(1, int(NS_BASE[idx] * multiplier * noise_ns))

                queue_ew = ew * 5.5  # avg vehicle length 5.5m
                queue_ns = ns * 5.5

                # Wait time depends on density and signal state
                base_wait = 45.0  # fixed timer baseline
                adaptive_factor = 0.55 + random.random() * 0.2  # 55-75% of baseline
                wait_time = base_wait * adaptive_factor * (
                    (ew + ns) / (EW_BASE[idx] + NS_BASE[idx])
                )
                wait_time = max(3.0, min(55.0, wait_time))

                # Toggle signal phase periodically
                phase_elapsed = intersection.ew_phase_seconds + interval
                cycle = intersection.cycle_length or 60
                if phase_elapsed >= (
                    intersection.ew_green_duration
                    if intersection.ew_green
                    else intersection.ns_green_duration
                ):
                    intersection.ew_green = not intersection.ew_green
                    phase_elapsed = 0.0

                intersection.ew_phase_seconds = phase_elapsed
                intersection.density_ew = ew
                intersection.density_ns = ns
                intersection.queue_ew_meters = round(queue_ew, 1)
                intersection.queue_ns_meters = round(queue_ns, 1)
                intersection.wait_time_avg = round(wait_time, 2)
                intersection.last_updated = datetime.utcnow()

                # Increment throughput
                vehicles_this_tick = int((ew + ns) * interval / 10)
                intersection.total_vehicles_processed += vehicles_this_tick
                total_vehicles += vehicles_this_tick

                await state_manager.append_wait_time(intersection.id, wait_time)
                await state_manager.update_density(
                    intersection.id, ew, ns, queue_ew, queue_ns, wait_time
                )
                await state_manager.set_ew_green(
                    intersection.id, intersection.ew_green
                )
                await state_manager.increment_vehicles(
                    intersection.id, vehicles_this_tick
                )

                # Fetch wait history for the state
                history = await state_manager.get_wait_history(intersection.id)
                intersection.wait_time_history = history[:60]

                updates.append(intersection)

            # Update system stats
            await state_manager.update_system_stats(
                total_vehicles_processed=sum(
                    u.total_vehicles_processed for u in updates
                ),
                network_avg_wait=round(
                    sum(u.wait_time_avg for u in updates) / max(1, len(updates)), 2
                ),
                last_tick=datetime.utcnow().isoformat(),
            )

            tick_count += 1

            # Broadcast via WebSocket
            if ws_broadcast:
                await ws_broadcast(
                    {
                        "type": "density_update",
                        "timestamp": datetime.utcnow().isoformat(),
                        "intersections": [u.model_dump(mode="json") for u in updates],
                    }
                )

        except Exception as e:
            logger.error("Simulator error: %s", e)

        await asyncio.sleep(interval)
