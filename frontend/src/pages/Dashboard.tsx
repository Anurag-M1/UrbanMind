/* Main operations dashboard page. */

import { ErrorBoundary } from "../components/shared/ErrorBoundary";
import { KPIBar } from "../components/Dashboard/KPIBar";
import { IntersectionPanel } from "../components/Dashboard/IntersectionPanel";
import { CityMap } from "../components/Map/CityMap";
import { useIntersections } from "../hooks/useIntersections";
import { useEmergencyStore } from "../store/emergencyStore";
import { useIntersectionStore } from "../store/intersectionStore";

export function DashboardPage() {
  const { intersections, selectedIntersection, loading, error } = useIntersections();
  const systemStats = useIntersectionStore((state) => state.systemStats);
  const selectIntersection = useIntersectionStore((state) => state.selectIntersection);
  const activeCorridor = useEmergencyStore((state) => state.activeCorridor);

  return (
    <div className="space-y-6">
      <KPIBar intersections={intersections} systemStats={systemStats} />
      <div className="grid grid-cols-[minmax(0,1.45fr)_420px] gap-6">
        <ErrorBoundary title="City map">
          <div className="space-y-3">
            {loading ? <div className="text-um-muted">Loading city map…</div> : null}
            {error ? <div className="text-um-red">{error}</div> : null}
            <CityMap
              intersections={intersections}
              corridorIds={activeCorridor}
              onSelectIntersection={selectIntersection}
            />
          </div>
        </ErrorBoundary>
        <IntersectionPanel intersection={selectedIntersection} />
      </div>
    </div>
  );
}
