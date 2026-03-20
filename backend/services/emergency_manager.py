"""Emergency corridor orchestration, vehicle tracking, and conflict handling."""

from __future__ import annotations

import asyncio
import json
import logging
import math
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Iterable, List
from uuid import uuid4

from config import settings
from models.emergency import EmergencyEvent, EmergencyOverride, EmergencyVehicle
from services import state_manager

logger = logging.getLogger("urbanmind.emergency_manager")

EARTH_RADIUS_METERS = 6_371_000
PRIORITY_MAP = {"ambulance": 0, "fire": 1, "police": 2}
SCENARIO_PATH = Path(__file__).resolve().parents[2] / "simulator" / "scenario_emergency.json"


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate the great-circle distance between two coordinate pairs."""

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2
    )
    return 2 * EARTH_RADIUS_METERS * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _project_position(lat: float, lng: float, speed_kmh: float, heading_deg: float, seconds: float = 15.0) -> tuple[float, float]:
    """Project vehicle position several seconds forward using heading and speed."""

    distance_m = speed_kmh * 1000 / 3600 * seconds
    heading = math.radians(heading_deg)
    lat_rad = math.radians(lat)
    lng_rad = math.radians(lng)

    projected_lat = math.asin(
        math.sin(lat_rad) * math.cos(distance_m / EARTH_RADIUS_METERS)
        + math.cos(lat_rad) * math.sin(distance_m / EARTH_RADIUS_METERS) * math.cos(heading)
    )
    projected_lng = lng_rad + math.atan2(
        math.sin(heading) * math.sin(distance_m / EARTH_RADIUS_METERS) * math.cos(lat_rad),
        math.cos(distance_m / EARTH_RADIUS_METERS) - math.sin(lat_rad) * math.sin(projected_lat),
    )
    return math.degrees(projected_lat), math.degrees(projected_lng)


class EmergencyManager:
    """Stateful manager for up to two simultaneous emergency corridors."""

    def __init__(self) -> None:
        self._active_vehicles: dict[str, EmergencyVehicle] = {}
        self._event_log: deque[EmergencyEvent] = deque(maxlen=200)
        self._lock = asyncio.Lock()

    def list_active_vehicles(self) -> list[EmergencyVehicle]:
        """Return active tracked vehicles in registration order."""

        return [vehicle for vehicle in self._active_vehicles.values() if vehicle.active]

    async def register_vehicle(self, vehicle_id: str, vehicle_type: str) -> EmergencyVehicle:
        """Register a vehicle while enforcing the max-two-active-vehicles constraint."""

        async with self._lock:
            if len(self.list_active_vehicles()) >= 2:
                raise ValueError("Maximum of 2 simultaneous emergency vehicles supported")

            vehicle = EmergencyVehicle(
                id=vehicle_id,
                type=vehicle_type,
                lat=0.0,
                lng=0.0,
                speed=0.0,
                heading=0.0,
                active=True,
                corridor_intersections=[],
            )
            self._active_vehicles[vehicle_id] = vehicle
            await self._record_event(
                EmergencyEvent(
                    id=str(uuid4()),
                    vehicle_id=vehicle_id,
                    vehicle_type=vehicle_type,
                    event_type="registered",
                    details="Vehicle registered for live corridor tracking",
                )
            )
            return vehicle

    async def update_gps(self, vehicle_id: str, lat: float, lng: float, speed: float, heading: float) -> EmergencyVehicle:
        """Update a vehicle position and re-run route prediction plus corridor activation."""

        async with self._lock:
            vehicle = self._active_vehicles.get(vehicle_id)
            if vehicle is None or not vehicle.active:
                raise ValueError(f"Emergency vehicle {vehicle_id} is not active")

            vehicle.lat = lat
            vehicle.lng = lng
            vehicle.speed = speed
            vehicle.heading = heading

            route = await self.predict_route(vehicle)
            await self.activate_corridor(vehicle_id, route)
            await self._deactivate_passed_intersections(vehicle)
            return vehicle

    async def predict_route(self, vehicle: EmergencyVehicle) -> list[str]:
        """Return upcoming intersections within corridor distance, ordered by projected arrival."""

        projected_lat, projected_lng = _project_position(vehicle.lat, vehicle.lng, vehicle.speed, vehicle.heading)
        intersections = await state_manager.get_all_intersections()

        scored: list[tuple[float, str]] = []
        for intersection in intersections:
            distance = _haversine(projected_lat, projected_lng, intersection.lat, intersection.lng)
            if distance <= settings.EMERGENCY_CORRIDOR_DISTANCE:
                scored.append((distance, intersection.id))

        scored.sort(key=lambda item: item[0])
        return [intersection_id for _, intersection_id in scored[: settings.EMERGENCY_CORRIDOR_LENGTH]]

    async def activate_corridor(self, vehicle_id: str, intersection_ids: list[str]) -> None:
        """Reserve corridor intersections for the given vehicle and publish override commands."""

        from routers import ws
        from services.signal_controller import publish_emergency_override

        vehicle = self._active_vehicles[vehicle_id]
        prioritized_route = await self.handle_multiple_vehicles(vehicle_id, intersection_ids)
        previous_route = set(vehicle.corridor_intersections)
        vehicle.corridor_intersections = prioritized_route

        for intersection_id in previous_route - set(prioritized_route):
            await self.deactivate_intersection(vehicle_id, intersection_id)

        for intersection_id in prioritized_route:
            await state_manager.set_override(intersection_id, True)
            state = await state_manager.get_intersection(intersection_id)
            if state is None:
                continue

            ew_green = self._determine_green_direction(vehicle, state.lat, state.lng)
            override = EmergencyOverride(
                intersection_id=intersection_id,
                vehicle_id=vehicle.id,
                vehicle_type=vehicle.type,
                ew_green=ew_green,
                priority=PRIORITY_MAP[vehicle.type] + 1,
            )
            await publish_emergency_override(override)

        await self._record_event(
            EmergencyEvent(
                id=str(uuid4()),
                vehicle_id=vehicle.id,
                vehicle_type=vehicle.type,
                event_type="activated",
                corridor_intersections=prioritized_route,
                details=f"Activated corridor across {len(prioritized_route)} intersections",
            )
        )
        await ws.broadcast_emergency_event(vehicle.model_dump(mode="json"), prioritized_route)

    async def deactivate_intersection(self, vehicle_id: str, intersection_id: str) -> None:
        """Release a single intersection back to adaptive control."""

        await state_manager.set_override(intersection_id, False)
        vehicle = self._active_vehicles.get(vehicle_id)
        vehicle_type = vehicle.type if vehicle is not None else "ambulance"
        await self._record_event(
            EmergencyEvent(
                id=str(uuid4()),
                vehicle_id=vehicle_id,
                vehicle_type=vehicle_type,
                event_type="deactivated",
                intersection_id=intersection_id,
                details="Intersection released from emergency override",
            )
        )

    async def deactivate_vehicle(self, vehicle_id: str) -> None:
        """Deactivate a vehicle and release its full corridor."""

        async with self._lock:
            vehicle = self._active_vehicles.get(vehicle_id)
            if vehicle is None:
                raise ValueError(f"Vehicle {vehicle_id} not found")

            for intersection_id in list(vehicle.corridor_intersections):
                await self.deactivate_intersection(vehicle_id, intersection_id)

            vehicle.active = False
            vehicle.corridor_intersections = []
            await self._record_event(
                EmergencyEvent(
                    id=str(uuid4()),
                    vehicle_id=vehicle.id,
                    vehicle_type=vehicle.type,
                    event_type="completed",
                    details="Vehicle corridor manually or automatically cleared",
                )
            )

    async def handle_multiple_vehicles(self, vehicle_id: str, intersection_ids: list[str]) -> list[str]:
        """Resolve conflicts when two emergency vehicles compete for the same route."""

        vehicle = self._active_vehicles[vehicle_id]
        allowed: list[str] = []
        for intersection_id in intersection_ids:
            competing = [
                other
                for other in self.list_active_vehicles()
                if other.id != vehicle_id and intersection_id in other.corridor_intersections
            ]
            if not competing:
                allowed.append(intersection_id)
                continue

            other = competing[0]
            if self._priority_tuple(vehicle) <= self._priority_tuple(other):
                allowed.append(intersection_id)
                await self._record_event(
                    EmergencyEvent(
                        id=str(uuid4()),
                        vehicle_id=vehicle.id,
                        vehicle_type=vehicle.type,
                        event_type="conflict",
                        intersection_id=intersection_id,
                        details=f"Priority granted over {other.id}",
                    )
                )
            else:
                await self._record_event(
                    EmergencyEvent(
                        id=str(uuid4()),
                        vehicle_id=vehicle.id,
                        vehicle_type=vehicle.type,
                        event_type="conflict",
                        intersection_id=intersection_id,
                        details=f"Yielded to higher-priority vehicle {other.id}",
                    )
                )
        return allowed

    async def activate_siren_corridor(self, nearest_intersection: str) -> None:
        """Fallback activation when a strong siren event occurs without GPS context."""

        fallback_id = "siren_fallback"
        if fallback_id not in self._active_vehicles:
            await self.register_vehicle(fallback_id, "ambulance")
        vehicle = self._active_vehicles[fallback_id]
        vehicle.corridor_intersections = [nearest_intersection]
        await self.activate_corridor(fallback_id, [nearest_intersection])

    async def simulate_emergency(self, vehicle_type: str) -> EmergencyVehicle:
        """Run the demo emergency scenario stored in the simulator folder."""

        points = json.loads(SCENARIO_PATH.read_text())
        vehicle_id = f"sim_{uuid4().hex[:8]}"
        vehicle = await self.register_vehicle(vehicle_id, vehicle_type)

        async def _run_track() -> None:
            for point in points:
                try:
                    await self.update_gps(
                        vehicle_id,
                        point["lat"],
                        point["lng"],
                        float(point.get("speed", 60.0)),
                        float(point.get("heading", 0.0)),
                    )
                except Exception as exc:
                    logger.error("Emergency simulation update failed: %s", exc)
                await asyncio.sleep(1)
            await self.deactivate_vehicle(vehicle_id)

        asyncio.create_task(_run_track())
        return vehicle

    def recent_events(self, limit: int = 20) -> list[EmergencyEvent]:
        """Return the newest in-memory emergency events first."""

        return list(reversed(list(self._event_log)[-limit:]))

    def _priority_tuple(self, vehicle: EmergencyVehicle) -> tuple[int, float]:
        """Return a tuple that sorts by vehicle type, then by distance already traveled."""

        return (PRIORITY_MAP[vehicle.type], -vehicle.speed)

    def _determine_green_direction(self, vehicle: EmergencyVehicle, target_lat: float, target_lng: float) -> bool:
        """Choose EW or NS green based on whether longitudinal or latitudinal delta dominates."""

        delta_lng = abs(target_lng - vehicle.lng)
        delta_lat = abs(target_lat - vehicle.lat)
        return delta_lng >= delta_lat

    async def _deactivate_passed_intersections(self, vehicle: EmergencyVehicle) -> None:
        """Release corridor intersections once the vehicle has passed nearby."""

        for intersection_id in list(vehicle.corridor_intersections):
            state = await state_manager.get_intersection(intersection_id)
            if state is None:
                continue
            if _haversine(vehicle.lat, vehicle.lng, state.lat, state.lng) < 75:
                await self.deactivate_intersection(vehicle.id, intersection_id)
                vehicle.corridor_intersections = [
                    current_id for current_id in vehicle.corridor_intersections if current_id != intersection_id
                ]

    async def _record_event(self, event: EmergencyEvent) -> None:
        """Store an emergency event in memory and Redis."""

        self._event_log.append(event)
        await state_manager.record_emergency_event(event)


emergency_manager = EmergencyManager()


async def register_vehicle(vehicle_id: str, vehicle_type: str) -> EmergencyVehicle:
    """Compatibility wrapper for registering emergency vehicles."""

    return await emergency_manager.register_vehicle(vehicle_id, vehicle_type)


async def update_gps(vehicle_id: str, lat: float, lng: float, speed: float, heading: float) -> EmergencyVehicle:
    """Compatibility wrapper for GPS updates."""

    return await emergency_manager.update_gps(vehicle_id, lat, lng, speed, heading)


async def predict_route(vehicle: EmergencyVehicle) -> List[str]:
    """Compatibility wrapper for route prediction."""

    return await emergency_manager.predict_route(vehicle)


async def activate_corridor(vehicle_id: str, intersection_ids: list[str]) -> None:
    """Compatibility wrapper for corridor activation."""

    await emergency_manager.activate_corridor(vehicle_id, intersection_ids)


async def deactivate_intersection(vehicle_id: str, intersection_id: str) -> None:
    """Compatibility wrapper for intersection release."""

    await emergency_manager.deactivate_intersection(vehicle_id, intersection_id)


async def handle_multiple_vehicles() -> Iterable[EmergencyVehicle]:
    """Return currently active vehicles for compatibility with older imports."""

    return emergency_manager.list_active_vehicles()
