/* Top-level KPI strip for live network statistics. */

import { Activity, Clock3, Flame, Network, TimerReset } from "lucide-react";

import { StatCard } from "../shared/StatCard";
import type { IntersectionState, SystemStats } from "../../types";

interface KPIBarProps {
  intersections: IntersectionState[];
  systemStats: SystemStats;
}

export function KPIBar({ intersections, systemStats }: KPIBarProps) {
  const online = intersections.filter((intersection) => !intersection.fault).length;
  const faults = intersections.filter((intersection) => intersection.fault).length;
  const secondsSinceRecalc = systemStats.webster_last_recalc
    ? Math.max(
        0,
        Math.round(
          (Date.now() - new Date(systemStats.webster_last_recalc).getTime()) / 1000,
        ),
      )
    : 0;

  return (
    <section className="grid grid-cols-5 gap-4">
      <StatCard
        label="Total Vehicles Detected"
        value={systemStats.total_vehicles_detected.toFixed(0)}
        helper="Live network count"
        icon={<Activity className="h-5 w-5 text-um-cyan" />}
      />
      <StatCard
        label="Network Avg Wait"
        value={`${systemStats.avg_wait_time_network.toFixed(1)}s`}
        helper="vs 45.0s baseline"
        tone="green"
        icon={<Clock3 className="h-5 w-5 text-um-green" />}
      />
      <StatCard
        label="Webster Recalc Countdown"
        value={`${Math.max(0, 10 - secondsSinceRecalc)}s`}
        helper={`Last at ${secondsSinceRecalc}s ago`}
        tone="purple"
        icon={<TimerReset className="h-5 w-5 text-um-purple" />}
      />
      <StatCard
        label="Active Intersections"
        value={`${online}/9`}
        helper={faults > 0 ? `${faults} faulted signals` : "All signals healthy"}
        tone={faults > 0 ? "amber" : "green"}
        icon={<Network className="h-5 w-5 text-um-amber" />}
      />
      <StatCard
        label="Emissions Saved"
        value={`${systemStats.emissions_saved_pct.toFixed(1)}%`}
        helper="vs stop-and-go baseline"
        tone="cyan"
        icon={<Flame className="h-5 w-5 text-um-cyan" />}
      />
    </section>
  );
}
