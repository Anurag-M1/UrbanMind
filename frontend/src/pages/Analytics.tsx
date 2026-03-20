/* Analytics dashboard page. */

import { useEffect, useState } from "react";

import {
  fetchAnalyticsSummary,
  fetchFlowSeries,
  fetchWaitTimeSeries,
} from "../api/urbanmind";
import { FlowChart } from "../components/Analytics/FlowChart";
import { HeatmapLegend } from "../components/Analytics/HeatmapLegend";
import { WaitTimeChart } from "../components/Analytics/WaitTimeChart";
import { ErrorBoundary } from "../components/shared/ErrorBoundary";
import { StatCard } from "../components/shared/StatCard";
import { useAnalyticsStore } from "../store/analyticsStore";
import { useIntersections } from "../hooks/useIntersections";

export function AnalyticsPage() {
  const { intersections } = useIntersections();
  const {
    flowSeries,
    waitSeries,
    summary,
    selectedIntersectionId,
    setFlowSeries,
    setWaitSeries,
    setSummary,
    setSelectedIntersectionId,
  } = useAnalyticsStore();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    void (async () => {
      setLoading(true);
      const [flow, wait, nextSummary] = await Promise.all([
        fetchFlowSeries(selectedIntersectionId ?? undefined),
        fetchWaitTimeSeries(selectedIntersectionId ?? undefined),
        fetchAnalyticsSummary(),
      ]);
      if (!cancelled) {
        setFlowSeries(flow);
        setWaitSeries(wait);
        setSummary(nextSummary);
        setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [selectedIntersectionId, setFlowSeries, setSummary, setWaitSeries]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4 rounded-3xl border border-um-border bg-um-surface/90 p-5">
        <div>
          <div className="text-xs uppercase tracking-[0.22em] text-um-muted">Analytics Range</div>
          <div className="mt-2 flex gap-2">
            {["today", "last 7 days", "last 30 days", "custom"].map((label) => (
              <button
                key={label}
                type="button"
                className="rounded-full border border-um-border px-3 py-1 text-sm text-um-text"
              >
                {label}
              </button>
            ))}
          </div>
        </div>
        <select
          value={selectedIntersectionId ?? "all"}
          onChange={(event) =>
            setSelectedIntersectionId(event.target.value === "all" ? null : event.target.value)
          }
          className="rounded-2xl border border-um-border bg-black/20 px-4 py-3 text-sm text-um-text"
        >
          <option value="all">All intersections</option>
          {intersections.map((intersection) => (
            <option key={intersection.id} value={intersection.id}>
              {intersection.name}
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <StatCard label="Peak Hour" value={summary?.peak_hour_identified ?? "--"} tone="purple" />
        <StatCard label="Best Intersection" value={summary?.best_intersection ?? "--"} tone="green" />
        <StatCard label="Worst Intersection" value={summary?.worst_intersection ?? "--"} tone="amber" />
        <StatCard
          label="Emergency Events"
          value={`${summary?.total_emergency_events ?? 0}`}
          tone="red"
          helper={`${summary?.cumulative_emissions_saved.toFixed(1) ?? "0.0"}% emissions saved`}
        />
      </div>

      {loading ? <div className="text-um-muted">Loading analytics…</div> : null}
      <div className="grid grid-cols-2 gap-6">
        <ErrorBoundary title="Flow analytics">
          <FlowChart data={flowSeries} />
        </ErrorBoundary>
        <ErrorBoundary title="Wait time analytics">
          <WaitTimeChart data={waitSeries} />
        </ErrorBoundary>
      </div>
      <HeatmapLegend />
    </div>
  );
}
