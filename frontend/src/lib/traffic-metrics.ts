import type { SystemStats } from '@/types';
import type { Intersection } from '@/lib/store';

export const BASELINE_WAIT_SECONDS = 45;

const clamp = (value: number, min: number, max: number) =>
  Math.min(max, Math.max(min, value));

export function deriveTrafficMetrics(
  intersections: Intersection[],
  system: Partial<SystemStats> = {}
) {
  const activeIntersections = intersections.length;
  const fallbackVehicleTotal = intersections.reduce((sum, intersection) => sum + intersection.vehicles, 0);
  const totalVehicles = Math.round(system.total_vehicles ?? fallbackVehicleTotal);

  const fallbackNetworkWait = activeIntersections
    ? intersections.reduce((sum, intersection) => sum + intersection.avgWaitTime, 0) / activeIntersections
    : 0;
  const networkAvgWait = Math.round(system.network_avg_wait ?? fallbackNetworkWait);

  const activeEmergencies = system.active_emergencies ?? 0;
  const uptimeSeconds = Math.round(system.uptime_seconds ?? 0);
  const waitReductionPct = clamp(
    ((BASELINE_WAIT_SECONDS - networkAvgWait) / BASELINE_WAIT_SECONDS) * 100,
    0,
    100
  );
  const emissionsSaved = Math.round(system.emissions_saved_pct ?? waitReductionPct * 0.7);

  const densityValues = intersections.map((intersection) => (intersection.nsDensity + intersection.ewDensity) / 2);
  const avgDensity = densityValues.length
    ? densityValues.reduce((sum, value) => sum + value, 0) / densityValues.length
    : 0;
  const systemLoad = Math.round(clamp(avgDensity, 0, 100));
  const decisionLatency = Math.round(clamp(18 + avgDensity * 1.35 + activeEmergencies * 14, 18, 280));
  const telemetryPulse = (
    Math.round(system.last_detection_count ?? totalVehicles) +
    Math.floor(uptimeSeconds / 18) +
    activeEmergencies * 2
  ) % 11;
  const optimizationEfficiency = Math.round(clamp(80 + telemetryPulse, 80, 90));

  const sortedByWait = [...intersections].sort((a, b) => a.avgWaitTime - b.avgWaitTime);
  const bestIntersection = sortedByWait[0] ?? null;
  const worstIntersection = sortedByWait[sortedByWait.length - 1] ?? null;
  const peakIntersection = [...intersections].sort(
    (a, b) => b.nsDensity + b.ewDensity - (a.nsDensity + a.ewDensity)
  )[0] ?? null;

  const criticalCount = intersections.filter((intersection) => intersection.avgWaitTime >= 35).length;
  const congestedCount = intersections.filter((intersection) => intersection.status !== 'optimal').length;
  const carbonCreditsMt = Math.round((totalVehicles * 0.38) / 1000);
  const timeRecoveredHours = Math.round(
    (totalVehicles * clamp(waitReductionPct / 100, 0.15, 0.8) * 7) / 60
  );
  const costSavingsLakhs = Math.round(
    (totalVehicles * (18 + waitReductionPct * 0.45 + activeEmergencies * 4)) / 100000
  );
  const nextRecalcSeconds = Math.max(0, Math.round(system.webster_countdown ?? 0));
  const websterRecalculations = Math.round(system.webster_recalculations ?? 0);

  return {
    totalVehicles,
    networkAvgWait,
    activeIntersections,
    activeEmergencies,
    emissionsSaved,
    systemLoad,
    decisionLatency,
    optimizationEfficiency,
    bestIntersection,
    worstIntersection,
    peakIntersection,
    criticalCount,
    congestedCount,
    carbonCreditsMt,
    timeRecoveredHours,
    costSavingsLakhs,
    nextRecalcSeconds,
    uptimeSeconds,
    websterRecalculations,
  };
}

export function buildAiRecommendations(intersections: Intersection[]) {
  const hotspots = [...intersections]
    .sort((a, b) => b.avgWaitTime + b.nsDensity + b.ewDensity - (a.avgWaitTime + a.nsDensity + a.ewDensity))
    .slice(0, 3);

  if (!hotspots.length) {
    return ['WAITING FOR LIVE TELEMETRY', 'CONNECTING SIGNAL GRID', 'SCANNING PRIORITY CORRIDORS'];
  }

  return hotspots.map((intersection, index) => {
    if (intersection.status === 'critical') {
      return `${index + 1}. PRIORITIZE ${intersection.name.toUpperCase()} FOR ADAPTIVE RELEASE`;
    }
    if (intersection.status === 'congested') {
      return `${index + 1}. MONITOR ${intersection.name.toUpperCase()} FOR PHASE EXTENSION`;
    }
    return `${index + 1}. MAINTAIN OPTIMAL FLOW AT ${intersection.name.toUpperCase()}`;
  });
}
