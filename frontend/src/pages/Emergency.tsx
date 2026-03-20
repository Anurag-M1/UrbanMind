/* Emergency operations center page. */

import { MapPin } from "lucide-react";

import { CorridorStatus } from "../components/Emergency/CorridorStatus";
import { DispatchButton } from "../components/Emergency/DispatchButton";
import { VehicleTracker } from "../components/Emergency/VehicleTracker";
import { ErrorBoundary } from "../components/shared/ErrorBoundary";
import { CityMap } from "../components/Map/CityMap";
import { useEmergency } from "../hooks/useEmergency";
import { useIntersections } from "../hooks/useIntersections";
import { useIntersectionStore } from "../store/intersectionStore";

export function EmergencyPage() {
  const { intersections } = useIntersections();
  const selectIntersection = useIntersectionStore((state) => state.selectIntersection);
  const {
    activeVehicles,
    activeCorridor,
    emergencyHistory,
    dispatchEmergency,
    isDispatching,
    error,
  } = useEmergency();

  return (
    <div className="grid grid-cols-[320px_minmax(0,1fr)_340px] gap-6">
      <section className="space-y-4">
        <DispatchButton onDispatch={dispatchEmergency} disabled={isDispatching} />
        <div className="rounded-3xl border border-um-border bg-um-surface/90 p-5">
          <div className="mb-3 text-xs uppercase tracking-[0.22em] text-um-muted">
            Dispatch Controls
          </div>
          <div className="text-sm text-um-text">
            Route: Bhilai civic center to Bhilai Nagar Crossing
          </div>
          <div className="mt-2 text-sm text-um-muted">Vehicle type: ambulance</div>
          {error ? <div className="mt-3 text-sm text-um-red">{error}</div> : null}
        </div>
      </section>

      <div className="space-y-6">
        <ErrorBoundary title="Emergency city map">
          <CityMap
            intersections={intersections}
            corridorIds={activeCorridor}
            onSelectIntersection={selectIntersection}
          />
        </ErrorBoundary>
        <CorridorStatus activeVehicles={activeVehicles} activeCorridor={activeCorridor} />
      </div>

      <section className="space-y-4">
        <VehicleTracker activeVehicles={activeVehicles} />
        <div className="rounded-3xl border border-um-border bg-um-surface/90 p-5">
          <div className="mb-3 text-xs uppercase tracking-[0.22em] text-um-muted">Emergency Log</div>
          <div className="space-y-3">
            {emergencyHistory.length === 0 ? (
              <div className="flex items-center gap-3 text-sm text-um-green">
                <MapPin className="h-4 w-4" />
                System Ready
              </div>
            ) : (
              emergencyHistory.slice(0, 20).map((event) => (
                <div key={event.id} className="rounded-2xl border border-um-border bg-black/20 p-3">
                  <div className="font-mono text-xs text-um-muted">{event.timestamp}</div>
                  <div className="mt-1 text-sm text-um-text">
                    {event.event_type.toUpperCase()} · {event.details}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
