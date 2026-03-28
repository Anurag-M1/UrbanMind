import asyncio
import uuid
import logging
import random
from typing import Dict, List, Optional, Any, Callable, Awaitable
from datetime import datetime

from models.emergency import EmergencyVehicle, EmergencyEvent
from utils.haversine import haversine_distance
from config import settings

logger = logging.getLogger("urbanmind.emergency")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GPS TRACKS — Delhi Optimized Tracks
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Track 1: AIIMS -> Lajpat Nagar -> ITO
AMBULANCE_TRACK_DELHI = [
    {"lat": 28.5650, "lng": 77.2080, "speed_kmh": 45, "heading": 30},
    {"lat": 28.5660, "lng": 77.2090, "speed_kmh": 55, "heading": 30},
    {"lat": 28.5672, "lng": 77.2100, "speed_kmh": 40, "heading": 45}, # AIIMS (int_003)
    {"lat": 28.5675, "lng": 77.2200, "speed_kmh": 65, "heading": 90},
    {"lat": 28.5675, "lng": 77.2300, "speed_kmh": 60, "heading": 90},
    {"lat": 28.5675, "lng": 77.2345, "speed_kmh": 45, "heading": 90}, # Lajpat Nagar (int_005)
    {"lat": 28.5800, "lng": 77.2345, "speed_kmh": 55, "heading": 0},
    {"lat": 28.6000, "lng": 77.2348, "speed_kmh": 60, "heading": 0},
    {"lat": 28.6200, "lng": 77.2348, "speed_kmh": 50, "heading": 0},
    {"lat": 28.6273, "lng": 77.2348, "speed_kmh": 35, "heading": 0},  # ITO (int_002)
]

# Track 2: Karol Bagh -> CP -> ITO
FIRE_TRACK_DELHI = [
    {"lat": 28.6443, "lng": 77.1800, "speed_kmh": 50, "heading": 90},
    {"lat": 28.6443, "lng": 77.1901, "speed_kmh": 40, "heading": 90}, # Karol Bagh (int_007)
    {"lat": 28.6400, "lng": 77.2000, "speed_kmh": 60, "heading": 135},
    {"lat": 28.6315, "lng": 77.2167, "speed_kmh": 35, "heading": 135}, # CP (int_001)
    {"lat": 28.6280, "lng": 77.2250, "speed_kmh": 55, "heading": 110},
    {"lat": 28.6273, "lng": 77.2348, "speed_kmh": 40, "heading": 90},  # ITO (int_002)
]

# Track 3: Hauz Khas -> AIIMS -> Lajpat Nagar
POLICE_TRACK_DELHI = [
    {"lat": 28.5400, "lng": 77.2044, "speed_kmh": 60, "heading": 0},
    {"lat": 28.5494, "lng": 77.2044, "speed_kmh": 45, "heading": 0},  # Hauz Khas (int_004)
    {"lat": 28.5550, "lng": 77.2060, "speed_kmh": 65, "heading": 15},
    {"lat": 28.5672, "lng": 77.2100, "speed_kmh": 50, "heading": 15},  # AIIMS (int_003)
    {"lat": 28.5675, "lng": 77.2250, "speed_kmh": 60, "heading": 90},
    {"lat": 28.5675, "lng": 77.2345, "speed_kmh": 45, "heading": 90},  # Lajpat Nagar (int_005)
]

# Intersection GPS coordinates (Delhi Optimized)
INTERSECTION_COORDS = {
    "int_001": (28.6315, 77.2167),
    "int_002": (28.6273, 77.2348),
    "int_003": (28.5672, 77.2100),
    "int_004": (28.5494, 77.2044),
    "int_005": (28.5675, 77.2345),
    "int_006": (28.5485, 77.2513),
    "int_007": (28.6443, 77.1901),
    "int_008": (28.5815, 77.0592),
    "int_009": (28.7299, 77.1264),
}

PRIORITY = {"ambulance": 3, "fire": 2, "police": 1}

TRACKS = {
    "ambulance": AMBULANCE_TRACK_DELHI,
    "fire": FIRE_TRACK_DELHI,
    "police": POLICE_TRACK_DELHI,
}


class EmergencyManager:
    def __init__(self) -> None:
        self.active_vehicles: Dict[str, EmergencyVehicle] = {}
        self.priority_queue: List[str] = []
        self.event_history: List[EmergencyEvent] = []
        self.MAX_ACTIVE = 2
        self._tasks: Dict[str, asyncio.Task[None]] = {}

    async def _build_route_guidance(
        self,
        vehicle: EmergencyVehicle,
        state_manager: Any,
    ) -> Dict[str, Any]:
        upcoming_ids = vehicle.corridor_intersections[vehicle.current_intersection_idx:]
        hotspots: List[tuple[float, str]] = []

        for int_id in upcoming_ids:
            state = await state_manager.get_intersection(int_id)
            if not state:
                continue
            load_score = float(state.wait_time_avg) + float(state.density_ew) + float(state.density_ns)
            if state.fault or state.wait_time_avg >= 28 or (state.density_ew + state.density_ns) >= 70:
                hotspots.append((load_score, int_id))

        hotspot_ids = [int_id for _, int_id in sorted(hotspots, reverse=True)]

        if not hotspot_ids:
            return {
                "route_status": "Primary Corridor Stable",
                "reroute_recommendation": "Primary emergency corridor is clear. Maintain current tactical route.",
                "alternate_corridor_intersections": [],
                "congestion_hotspots": [],
            }

        destination_id = vehicle.corridor_intersections[-1] if vehicle.corridor_intersections else None
        destination_coords = INTERSECTION_COORDS.get(destination_id, INTERSECTION_COORDS.get("int_002", (28.6273, 77.2348)))
        candidates: List[tuple[float, str]] = []

        for int_id, (lat, lng) in INTERSECTION_COORDS.items():
            if int_id in vehicle.corridor_intersections:
                continue
            state = await state_manager.get_intersection(int_id)
            if not state:
                continue
            score = (
                float(state.wait_time_avg) * 1.3
                + float(state.density_ew + state.density_ns)
                + (35 if state.fault else 0)
                + haversine_distance(lat, lng, destination_coords[0], destination_coords[1]) / 110
            )
            candidates.append((score, int_id))

        alternates = [int_id for _, int_id in sorted(candidates)[:2]]
        hotspot_label = ", ".join(hotspot_ids[:2]).upper()
        alternate_label = " -> ".join(alternates).upper() if alternates else "NO LOW-CONGESTION ALTERNATE AVAILABLE"

        return {
            "route_status": "Reroute Advised",
            "reroute_recommendation": (
                f"Congestion detected near {hotspot_label}. "
                f"Suggested alternate priority path: {alternate_label}."
            ),
            "alternate_corridor_intersections": alternates,
            "congestion_hotspots": hotspot_ids[:3],
        }

    def _find_corridor_intersections(
        self, track: List[Dict[str, Any]], max_count: int = 5
    ) -> List[str]:
        """Find the N nearest intersections along the GPS track."""
        corridor: List[str] = []
        used = set()
        proximity_threshold = 0.005  # ~500m in degrees

        for waypoint in track:
            lat, lng = waypoint["lat"], waypoint["lng"]
            for int_id, (ilat, ilng) in INTERSECTION_COORDS.items():
                if int_id in used:
                    continue
                dist = haversine_distance(lat, lng, ilat, ilng)
                if dist < proximity_threshold * 111000:  # convert to meters approx
                    corridor.append(int_id)
                    used.add(int_id)
                    if len(corridor) >= max_count:
                        return corridor

        # If not enough found, add nearest ones
        if len(corridor) < 3:
            start_lat = track[0]["lat"]
            start_lng = track[0]["lng"]
            dists = []
            for int_id, (ilat, ilng) in INTERSECTION_COORDS.items():
                if int_id not in used:
                    d = haversine_distance(start_lat, start_lng, ilat, ilng)
                    dists.append((d, int_id))
            dists.sort()
            for _, int_id in dists[:max_count - len(corridor)]:
                corridor.append(int_id)

        return corridor[:max_count]

    async def simulate_emergency(
        self,
        vehicle_type: str,
        state_manager: Any,
        ws_broadcast: Optional[Callable[..., Awaitable[None]]] = None,
        trigger_source: str = "manual",
    ) -> Dict[str, Any]:
        """Start an emergency simulation for the given vehicle type."""
        vehicle_id = f"em_{vehicle_type[:3]}_{uuid.uuid4().hex[:6]}"

        track = TRACKS.get(vehicle_type, AMBULANCE_TRACK_DELHI)
        # Add GPS jitter for realism
        track = [
            {
                **wp,
                "lat": wp["lat"] + random.uniform(-0.00005, 0.00005),
                "lng": wp["lng"] + random.uniform(-0.00005, 0.00005),
            }
            for wp in track
        ]

        corridor = self._find_corridor_intersections(
            track, settings.CORRIDOR_LENGTH
        )

        vehicle = EmergencyVehicle(
            id=vehicle_id,
            type=vehicle_type,
            lat=track[0]["lat"],
            lng=track[0]["lng"],
            speed_kmh=track[0]["speed_kmh"],
            heading_degrees=track[0]["heading"],
            active=True,
            activated_at=datetime.utcnow(),
            corridor_intersections=corridor,
            current_intersection_idx=0,
            eta_seconds=len(track),
        )
        vehicle.gps_history = [{"lat": vehicle.lat, "lng": vehicle.lng}]

        route_guidance = await self._build_route_guidance(vehicle, state_manager)
        vehicle.route_status = route_guidance["route_status"]
        vehicle.reroute_recommendation = route_guidance["reroute_recommendation"]
        vehicle.alternate_corridor_intersections = route_guidance["alternate_corridor_intersections"]
        vehicle.congestion_hotspots = route_guidance["congestion_hotspots"]

        self.active_vehicles[vehicle_id] = vehicle
        self.priority_queue.append(vehicle_id)
        self.priority_queue.sort(
            key=lambda vid: PRIORITY.get(
                self.active_vehicles[vid].type, 0
            ),
            reverse=True,
        )

        # Activate corridor
        await self._activate_corridor(
            vehicle_id,
            corridor,
            state_manager,
            ws_broadcast,
            trigger_source=trigger_source,
        )

        # Start GPS streaming task
        task = asyncio.create_task(
            self._stream_gps(vehicle_id, track, state_manager, ws_broadcast)
        )
        self._tasks[vehicle_id] = task

        logger.info(
            "Emergency activated: %s (%s), corridor: %s",
            vehicle_id, vehicle_type, corridor,
        )

        return {
            "vehicle_id": vehicle_id,
            "vehicle_type": vehicle_type,
            "corridor": corridor,
            "activated_at": vehicle.activated_at.isoformat(),
            "track_points": len(track),
            "trigger_source": trigger_source,
        }

    async def _activate_corridor(
        self,
        vehicle_id: str,
        intersection_ids: List[str],
        state_manager: Any,
        ws_broadcast: Optional[Callable[..., Awaitable[None]]] = None,
        trigger_source: str = "manual",
    ) -> None:
        """Set override on all corridor intersections."""
        vehicle = self.active_vehicles.get(vehicle_id)
        if not vehicle:
            return

        corridor_states = []
        for int_id in intersection_ids:
            await state_manager.set_override(int_id, True, "emergency")
            # Set green in direction of travel
            await state_manager.set_ew_green(int_id, True)
            state = await state_manager.get_intersection(int_id)
            if state:
                corridor_states.append(state.model_dump(mode="json"))

        if ws_broadcast:
            source_prefix = (
                "Siren-verified live detection confirmed for"
                if trigger_source == "vision_auto_siren"
                else
                "Live vision auto-detected"
                if trigger_source == "vision_auto"
                else "Manual dispatch confirmed for"
            )
            await ws_broadcast({
                "type": "emergency_activated",
                "vehicle": vehicle.model_dump(mode="json"),
                "corridor": corridor_states,
                "trigger_source": trigger_source,
                "message": (
                    f"{source_prefix} {vehicle.type.title()}. "
                    f"{len(intersection_ids)} signal green corridor activated. "
                    f"800m pre-emption in effect."
                ),
                "route_status": vehicle.route_status,
                "reroute_recommendation": vehicle.reroute_recommendation,
                "alternate_corridor_intersections": vehicle.alternate_corridor_intersections,
                "congestion_hotspots": vehicle.congestion_hotspots,
            })

    async def _stream_gps(
        self,
        vehicle_id: str,
        track: List[Dict[str, Any]],
        state_manager: Any,
        ws_broadcast: Optional[Callable[..., Awaitable[None]]] = None,
    ) -> None:
        """Stream GPS positions along the track, 1 point per second."""
        vehicle = self.active_vehicles.get(vehicle_id)
        if not vehicle:
            return

        intersections_cleared = 0

        try:
            for i, waypoint in enumerate(track):
                if vehicle_id not in self.active_vehicles:
                    break  # Vehicle was manually deactivated

                vehicle.lat = waypoint["lat"]
                vehicle.lng = waypoint["lng"]
                vehicle.speed_kmh = waypoint["speed_kmh"]
                vehicle.heading_degrees = waypoint["heading"]
                vehicle.eta_seconds = max(0, len(track) - i - 1)
                vehicle.gps_history = [*vehicle.gps_history[-19:], {"lat": vehicle.lat, "lng": vehicle.lng}]

                route_guidance = await self._build_route_guidance(vehicle, state_manager)
                vehicle.route_status = route_guidance["route_status"]
                vehicle.reroute_recommendation = route_guidance["reroute_recommendation"]
                vehicle.alternate_corridor_intersections = route_guidance["alternate_corridor_intersections"]
                vehicle.congestion_hotspots = route_guidance["congestion_hotspots"]

                # Check if near any corridor intersection
                for j, int_id in enumerate(vehicle.corridor_intersections):
                    if j < vehicle.current_intersection_idx:
                        continue
                    int_lat, int_lng = INTERSECTION_COORDS.get(
                        int_id, (0, 0)
                    )
                    dist = haversine_distance(
                        vehicle.lat, vehicle.lng, int_lat, int_lng
                    )
                    if dist < 50:  # within 50 meters
                        vehicle.current_intersection_idx = j + 1
                        intersections_cleared += 1
                        await self._deactivate_intersection(
                            vehicle_id, int_id, state_manager, ws_broadcast
                        )

                if ws_broadcast:
                    await ws_broadcast({
                        "type": "vehicle_position",
                        "vehicle_id": vehicle_id,
                        "lat": vehicle.lat,
                        "lng": vehicle.lng,
                        "speed_kmh": vehicle.speed_kmh,
                        "heading": vehicle.heading_degrees,
                        "eta_seconds": vehicle.eta_seconds,
                        "route_status": vehicle.route_status,
                        "reroute_recommendation": vehicle.reroute_recommendation,
                        "alternate_corridor_intersections": vehicle.alternate_corridor_intersections,
                        "congestion_hotspots": vehicle.congestion_hotspots,
                        "gps_history": vehicle.gps_history,
                        "corridor_progress": (
                            f"{vehicle.current_intersection_idx}/"
                            f"{len(vehicle.corridor_intersections)} "
                            f"intersections cleared"
                        ),
                    })

                await asyncio.sleep(1)

        except asyncio.CancelledError:
            logger.info("GPS stream cancelled for %s", vehicle_id)
        except Exception as e:
            logger.error("GPS stream error for %s: %s", vehicle_id, e)

        # Deactivate remaining corridor intersections
        for int_id in vehicle.corridor_intersections[vehicle.current_intersection_idx:]:
            await self._deactivate_intersection(
                vehicle_id, int_id, state_manager, ws_broadcast
            )
            intersections_cleared += 1

        # Record event
        time_saved = intersections_cleared * 45  # 45s per signal avoided
        event = EmergencyEvent(
            id=f"evt_{uuid.uuid4().hex[:8]}",
            vehicle_id=vehicle_id,
            vehicle_type=vehicle.type,
            activated_at=vehicle.activated_at,
            deactivated_at=datetime.utcnow(),
            intersections_cleared=intersections_cleared,
            response_time_saved_seconds=float(time_saved),
        )
        self.event_history.append(event)
        await state_manager.add_emergency_event(event)

        # Clean up
        self.active_vehicles.pop(vehicle_id, None)
        if vehicle_id in self.priority_queue:
            self.priority_queue.remove(vehicle_id)
        self._tasks.pop(vehicle_id, None)

        if ws_broadcast:
            await ws_broadcast({
                "type": "emergency_deactivated",
                "vehicle_id": vehicle_id,
                "vehicle_type": vehicle.type,
                "intersections_cleared": intersections_cleared,
                "time_saved_seconds": time_saved,
            })

        logger.info(
            "Emergency deactivated: %s, %d intersections cleared, ~%ds saved",
            vehicle_id, intersections_cleared, time_saved,
        )

    async def _deactivate_intersection(
        self,
        vehicle_id: str,
        intersection_id: str,
        state_manager: Any,
        ws_broadcast: Optional[Callable[..., Awaitable[None]]] = None,
    ) -> None:
        """Remove emergency override from a single intersection."""
        await state_manager.set_override(intersection_id, False, "")

        if ws_broadcast:
            await ws_broadcast({
                "type": "corridor_update",
                "vehicle_id": vehicle_id,
                "intersection_id": intersection_id,
                "status": "cleared",
            })

    async def deactivate_vehicle(
        self,
        vehicle_id: str,
        state_manager: Any,
        ws_broadcast: Optional[Callable[..., Awaitable[None]]] = None,
    ) -> bool:
        """Manually deactivate an emergency vehicle."""
        vehicle = self.active_vehicles.get(vehicle_id)
        if not vehicle:
            return False

        # Cancel GPS streaming task
        task = self._tasks.get(vehicle_id)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Deactivate all corridor intersections
        for int_id in vehicle.corridor_intersections:
            await self._deactivate_intersection(
                vehicle_id, int_id, state_manager, ws_broadcast
            )

        self.active_vehicles.pop(vehicle_id, None)
        if vehicle_id in self.priority_queue:
            self.priority_queue.remove(vehicle_id)
        self._tasks.pop(vehicle_id, None)

        return True

    def get_active_vehicles(self) -> List[EmergencyVehicle]:
        return list(self.active_vehicles.values())

    def get_event_history(self, limit: int = 50) -> List[EmergencyEvent]:
        return self.event_history[-limit:]


emergency_manager = EmergencyManager()
