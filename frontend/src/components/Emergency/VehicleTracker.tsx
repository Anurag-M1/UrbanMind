/* Emergency vehicle list with live speed and route details. */

import type { EmergencyVehicle } from "../../types";

interface VehicleTrackerProps {
  activeVehicles: EmergencyVehicle[];
}

export function VehicleTracker({ activeVehicles }: VehicleTrackerProps) {
  if (activeVehicles.length === 0) {
    return (
      <div className="rounded-3xl border border-um-border bg-um-surface/90 p-5 text-um-muted">
        System Ready
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {activeVehicles.map((vehicle) => (
        <article key={vehicle.id} className="rounded-3xl border border-um-border bg-um-surface/90 p-4">
          <div className="font-display text-lg text-white">{vehicle.type.toUpperCase()}</div>
          <div className="mt-2 font-mono text-sm text-um-cyan">{vehicle.speed.toFixed(1)} km/h</div>
          <div className="mt-2 text-sm text-um-text">
            ETA to next intersection: {Math.max(4, 18 - vehicle.corridor_intersections.length)}s
          </div>
        </article>
      ))}
    </div>
  );
}
