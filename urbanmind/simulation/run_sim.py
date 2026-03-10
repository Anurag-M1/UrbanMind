from __future__ import annotations

import argparse
import json
import queue
import sys
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from simulation.sim_intersection import SimulatedIntersection

try:
    from rich.live import Live
    from rich.table import Table
except ImportError:  # pragma: no cover - optional dependency
    Live = None
    Table = None


def _post_state(url: str, state: dict[str, Any]) -> None:
    """Posts one simulated state payload to the backend API.

    Args:
        url: Backend ingest URL.
        state: State payload.

    Returns:
        None.
    """

    target_url = (
        url
        if url.endswith("/state")
        else f"{url.rstrip('/')}/{state['intersection_id']}/state"
    )
    data = json.dumps(state).encode("utf-8")
    request = urllib.request.Request(target_url, data=data, method="POST")
    request.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(request, timeout=5):
        return


def _render_table(states: dict[str, dict[str, Any]]) -> Any:
    """Renders the current simulation state table.

    Args:
        states: Latest per-intersection state.

    Returns:
        Rich table or plain-text string.
    """

    if Table is None:
        return "\n".join(
            f"{intersection_id} wait={state['benchmark']['actual_wait_seconds']} emergency={state['emergency_active']}"
            for intersection_id, state in sorted(states.items())
        )
    table = Table(title="UrbanMind Simulation")
    table.add_column("Intersection")
    table.add_column("Cycle")
    table.add_column("Avg Wait")
    table.add_column("Emergency")
    table.add_column("Top Congestion")
    for intersection_id, state in sorted(states.items()):
        top_level = max(
            (lane["congestion_level"] for lane in state["lane_densities"].values()),
            default="LOW",
            key=lambda value: {"LOW": 0, "MED": 1, "HIGH": 2}[value],
        )
        table.add_row(
            intersection_id,
            str(state["current_signal_plan"]["cycle_length"]),
            str(state["benchmark"]["actual_wait_seconds"]),
            "YES" if state["emergency_active"] else "NO",
            top_level,
        )
    return table


def _worker(
    simulator: SimulatedIntersection,
    duration: int,
    tick_delay: float,
    inject_emergency: int | None,
    route: list[str],
    outbound: "queue.Queue[tuple[str, dict[str, Any]]]",
    backend_url: str | None,
) -> None:
    """Runs one intersection simulation worker.

    Args:
        simulator: Intersection simulator.
        duration: Total simulated seconds.
        tick_delay: Real-time delay per simulated second.
        inject_emergency: Optional emergency injection time.
        route: Route affected by emergency pre-emption.
        outbound: Queue used to publish latest state.
        backend_url: Optional backend URL for state posting.

    Returns:
        None.
    """

    for second in range(duration):
        emergency_active = inject_emergency is not None and second >= inject_emergency and second < inject_emergency + 90 and simulator.intersection_id in route
        state = simulator.step(second, emergency_active=emergency_active)
        outbound.put((simulator.intersection_id, state))
        if backend_url:
            try:
                _post_state(backend_url, state)
            except Exception:
                pass
        time.sleep(tick_delay)


def main() -> None:
    """Runs N simulated intersections in parallel.

    Args:
        None.

    Returns:
        None.
    """

    parser = argparse.ArgumentParser(description="Run UrbanMind traffic simulation")
    parser.add_argument("--intersections", type=int, default=3)
    parser.add_argument("--duration", type=int, default=300)
    parser.add_argument("--inject-emergency", type=int, default=None)
    parser.add_argument("--backend-url", type=str, default=None)
    parser.add_argument("--tick-delay", type=float, default=0.05)
    args = parser.parse_args()

    states: dict[str, dict[str, Any]] = {}
    outbound: "queue.Queue[tuple[str, dict[str, Any]]]" = queue.Queue()
    route = [f"sim_{index + 1:03d}" for index in range(args.intersections)]
    threads = [
        threading.Thread(
            target=_worker,
            args=(
                SimulatedIntersection(route[index]),
                args.duration,
                args.tick_delay,
                args.inject_emergency,
                route,
                outbound,
                args.backend_url,
            ),
            daemon=True,
        )
        for index in range(args.intersections)
    ]
    for thread in threads:
        thread.start()

    if Live is None:
        while any(thread.is_alive() for thread in threads) or not outbound.empty():
            while not outbound.empty():
                intersection_id, state = outbound.get()
                states[intersection_id] = state
            print(_render_table(states))
            time.sleep(max(args.tick_delay, 0.1))
    else:
        with Live(_render_table(states), refresh_per_second=10) as live:
            while any(thread.is_alive() for thread in threads) or not outbound.empty():
                while not outbound.empty():
                    intersection_id, state = outbound.get()
                    states[intersection_id] = state
                live.update(_render_table(states))
                time.sleep(max(args.tick_delay, 0.1))
    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
