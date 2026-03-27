import asyncio
import logging
from typing import Dict, Any, Optional, Callable, Awaitable
from datetime import datetime

logger = logging.getLogger("urbanmind.webster")

SATURATION_FLOW = 1600  # veh/hour/lane (Increased for high-density Delhi clusters)
LOST_TIME_PER_PHASE = 6  # seconds (High Delhi clearance intervals)


def calculate(density_ew: int, density_ns: int) -> Dict[str, Any]:
    """
    Webster's formula for optimal signal cycle length.
    density_ew/ns are vehicle counts per 10-second window.
    """
    flow_ew = density_ew * 360  # convert 10s count to hourly flow
    flow_ns = density_ns * 360

    y_ew = flow_ew / SATURATION_FLOW if SATURATION_FLOW > 0 else 0
    y_ns = flow_ns / SATURATION_FLOW if SATURATION_FLOW > 0 else 0
    Y = y_ew + y_ns

    L = 2 * LOST_TIME_PER_PHASE  # total lost time (2 phases)

    # Guard: oversaturated or zero flow
    if Y >= 0.9 or Y == 0:
        return {
            "ew_green": 40,
            "ns_green": 35,
            "cycle_length": 79,
            "y_ew": round(y_ew, 3),
            "y_ns": round(y_ns, 3),
            "Y": round(Y, 3),
            "flow_ew_per_hour": flow_ew,
            "flow_ns_per_hour": flow_ns,
        }

    # Webster's optimal cycle length (Delhi Adjusted)
    C = (1.5 * L + 5) / (1 - Y)
    C = max(60, min(180, round(C)))

    # Effective green time
    G = C - L

    # Split proportionally by flow ratio
    ew_green = max(10, min(60, round(G * (y_ew / Y)))) if Y > 0 else 25
    ns_green = max(10, min(60, G - ew_green))

    return {
        "ew_green": ew_green,
        "ns_green": ns_green,
        "cycle_length": ew_green + ns_green + L,
        "y_ew": round(y_ew, 3),
        "y_ns": round(y_ns, 3),
        "Y": round(Y, 3),
        "flow_ew_per_hour": flow_ew,
        "flow_ns_per_hour": flow_ns,
    }


async def optimization_loop(
    state_manager: Any,
    mqtt_client: Any,
    ws_broadcast: Optional[Callable[..., Awaitable[None]]] = None,
    interval: int = 10,
) -> None:
    """
    Runs forever: every `interval` seconds, recalculate optimal signal timings
    for all non-overridden intersections using Webster's formula.
    """
    logger.info("Webster optimization loop started (interval=%ds)", interval)
    recalc_count = 0

    while True:
        try:
            intersections = await state_manager.get_all_intersections()
            updated_count = 0

            for intersection in intersections:
                if intersection.override or intersection.fault:
                    continue

                timings = calculate(intersection.density_ew, intersection.density_ns)

                intersection.ew_green_duration = timings["ew_green"]
                intersection.ns_green_duration = timings["ns_green"]
                intersection.cycle_length = timings["cycle_length"]
                intersection.webster_last_calc = datetime.utcnow()

                await state_manager.set_intersection(intersection)

                # Publish to MQTT
                if mqtt_client and mqtt_client.connected:
                    mqtt_client.publish(
                        f"urbanmind/intersection/{intersection.id}/command",
                        {
                            "ew_green": timings["ew_green"],
                            "ns_green": timings["ns_green"],
                            "cycle_length": timings["cycle_length"],
                        },
                    )

                updated_count += 1

            recalc_count += 1
            await state_manager.increment_stat("webster_recalculations", 1)

            if ws_broadcast:
                await ws_broadcast(
                    {
                        "type": "webster_recalc",
                        "timestamp": datetime.utcnow().isoformat(),
                        "intersections_updated": updated_count,
                        "recalc_number": recalc_count,
                    }
                )

            logger.debug(
                "Webster recalculated %d intersections (cycle #%d)",
                updated_count,
                recalc_count,
            )

        except Exception as e:
            logger.error("Webster optimization error: %s", e)

        await asyncio.sleep(interval)
