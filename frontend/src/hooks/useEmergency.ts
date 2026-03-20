/* Emergency actions hook for dispatching simulator-driven vehicles. */

import { useEffect, useState } from "react";

import { fetchEmergencyHistory, simulateEmergency } from "../api/urbanmind";
import { useEmergencyStore } from "../store/emergencyStore";

export function useEmergency() {
  const replaceHistory = useEmergencyStore((state) => state.replaceHistory);
  const emergencyHistory = useEmergencyStore((state) => state.emergencyHistory);
  const activeVehicles = useEmergencyStore((state) => state.activeVehicles);
  const activeCorridor = useEmergencyStore((state) => state.activeCorridor);
  const [isDispatching, setIsDispatching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    void (async () => {
      try {
        const history = await fetchEmergencyHistory();
        if (!cancelled) {
          replaceHistory(history);
        }
      } catch (cause) {
        if (!cancelled) {
          setError(cause instanceof Error ? cause.message : "Failed to load emergency history");
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [replaceHistory]);

  const dispatchEmergency = async () => {
    setIsDispatching(true);
    setError(null);
    try {
      await simulateEmergency();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Failed to dispatch emergency");
    } finally {
      setIsDispatching(false);
    }
  };

  return {
    activeVehicles,
    activeCorridor,
    emergencyHistory,
    dispatchEmergency,
    isDispatching,
    error,
  };
}
