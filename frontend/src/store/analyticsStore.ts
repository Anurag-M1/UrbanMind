/* Zustand store for analytics dashboard time-series state. */

import { create } from "zustand";

import type { SummaryData, TimeSeriesPoint } from "../types";

interface AnalyticsStoreState {
  flowSeries: TimeSeriesPoint[];
  waitSeries: TimeSeriesPoint[];
  summary: SummaryData | null;
  selectedIntersectionId: string | null;
  setFlowSeries: (points: TimeSeriesPoint[]) => void;
  setWaitSeries: (points: TimeSeriesPoint[]) => void;
  setSummary: (summary: SummaryData) => void;
  setSelectedIntersectionId: (intersectionId: string | null) => void;
}

export const useAnalyticsStore = create<AnalyticsStoreState>((set) => ({
  flowSeries: [],
  waitSeries: [],
  summary: null,
  selectedIntersectionId: null,
  setFlowSeries: (points) => set(() => ({ flowSeries: points })),
  setWaitSeries: (points) => set(() => ({ waitSeries: points })),
  setSummary: (summary) => set(() => ({ summary })),
  setSelectedIntersectionId: (selectedIntersectionId) =>
    set(() => ({ selectedIntersectionId })),
}));
