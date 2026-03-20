/* Emergency corridor summary card. */

import type { EmergencyVehicle } from "../../types";

interface CorridorStatusProps {
  activeVehicles: EmergencyVehicle[];
  activeCorridor: string[];
}

export function CorridorStatus({ activeVehicles, activeCorridor }: CorridorStatusProps) {
  return (
    <section className="rounded-3xl border border-um-border bg-um-surface/90 p-5">
      <div className="text-xs uppercase tracking-[0.22em] text-um-muted">Corridor Status</div>
      <div className="mt-3 font-display text-2xl text-white">
        Pre-empted {activeCorridor.length} signals · 800m · {activeVehicles.length} vehicles active
      </div>
    </section>
  );
}
