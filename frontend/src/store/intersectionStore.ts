/* Zustand store for live intersection and dashboard state. */

import { create } from "zustand";

import type { Alert, IntersectionState, SystemStats } from "../types";

interface IntersectionStoreState {
  intersections: Map<string, IntersectionState>;
  systemStats: SystemStats;
  alerts: Alert[];
  selectedIntersectionId: string | null;
  updateIntersection: (state: IntersectionState) => void;
  updateAllIntersections: (states: IntersectionState[]) => void;
  updateSystemStats: (stats: SystemStats) => void;
  addAlert: (alert: Alert) => void;
  clearAlert: (id: string) => void;
  selectIntersection: (id: string | null) => void;
}

const defaultStats: SystemStats = {
  total_vehicles_detected: 0,
  avg_wait_time_network: 0,
  webster_last_recalc: "",
  emissions_saved_pct: 0,
};

export const useIntersectionStore = create<IntersectionStoreState>((set) => ({
  intersections: new Map<string, IntersectionState>(),
  systemStats: defaultStats,
  alerts: [],
  selectedIntersectionId: null,
  updateIntersection: (state) =>
    set((current) => {
      const next = new Map(current.intersections);
      next.set(state.id, state);
      return { intersections: next };
    }),
  updateAllIntersections: (states) =>
    set(() => ({
      intersections: new Map(states.map((state) => [state.id, state])),
    })),
  updateSystemStats: (stats) => set(() => ({ systemStats: stats })),
  addAlert: (alert) =>
    set((current) => ({
      alerts: [alert, ...current.alerts].slice(0, 12),
    })),
  clearAlert: (id) =>
    set((current) => ({
      alerts: current.alerts.filter((alert) => alert.id !== id),
    })),
  selectIntersection: (id) => set(() => ({ selectedIntersectionId: id })),
}));
