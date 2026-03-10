from __future__ import annotations

from .models import Intersection


class AdaptiveSignalController:
    """Allocates cycle time by phase based on aggregated lane pressure."""

    def plan_cycle(self, intersection: Intersection) -> dict[str, int]:
        phases = intersection.phases()
        lost_time = len(phases) * (intersection.yellow_seconds + intersection.all_red_seconds)
        usable_cycle = max(
            len(phases) * intersection.min_green_seconds,
            intersection.cycle_seconds - lost_time,
        )

        phase_pressure: dict[str, float] = {phase: 0.0 for phase in phases}
        for lane_id, metrics in intersection.lane_metrics.items():
            phase = intersection.lane_phase_map[lane_id]
            phase_pressure[phase] += metrics.pressure_score()

        total_pressure = sum(phase_pressure.values())
        if total_pressure <= 0:
            equal_green = usable_cycle // max(1, len(phases))
            return {
                phase: max(intersection.min_green_seconds, equal_green)
                for phase in phases
            }

        preliminary: dict[str, int] = {}
        for phase, pressure in phase_pressure.items():
            share = pressure / total_pressure
            green_seconds = round(usable_cycle * share)
            bounded_green = max(
                intersection.min_green_seconds,
                min(intersection.max_green_seconds, green_seconds),
            )
            preliminary[phase] = bounded_green

        current_total = sum(preliminary.values())
        delta = usable_cycle - current_total
        if delta != 0:
            ranked_phases = sorted(
                phases,
                key=lambda phase: phase_pressure[phase],
                reverse=delta > 0,
            )
            step = 1 if delta > 0 else -1
            while delta != 0 and ranked_phases:
                adjusted = False
                for phase in ranked_phases:
                    candidate = preliminary[phase] + step
                    if intersection.min_green_seconds <= candidate <= intersection.max_green_seconds:
                        preliminary[phase] = candidate
                        delta -= step
                        adjusted = True
                        if delta == 0:
                            break
                if not adjusted:
                    break

        return preliminary
