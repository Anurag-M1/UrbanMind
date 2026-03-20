/* Intersection data hook bridging API bootstrap and Zustand state. */

import { useEffect, useState } from "react";

import { fetchIntersections } from "../api/urbanmind";
import { useIntersectionStore } from "../store/intersectionStore";

export function useIntersections() {
  const intersections = Array.from(
    useIntersectionStore((state) => state.intersections).values(),
  );
  const updateAllIntersections = useIntersectionStore((state) => state.updateAllIntersections);
  const selectedIntersectionId = useIntersectionStore((state) => state.selectedIntersectionId);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    void (async () => {
      try {
        setLoading(true);
        const items = await fetchIntersections();
        if (!cancelled) {
          updateAllIntersections(items);
          setError(null);
        }
      } catch (cause) {
        if (!cancelled) {
          setError(cause instanceof Error ? cause.message : "Failed to load intersections");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [updateAllIntersections]);

  return {
    intersections,
    loading,
    error,
    selectedIntersectionId,
    selectedIntersection:
      selectedIntersectionId !== null
        ? intersections.find((item) => item.id === selectedIntersectionId) ?? null
        : null,
  };
}
