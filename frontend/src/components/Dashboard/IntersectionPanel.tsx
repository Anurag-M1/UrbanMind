/* Right-side detail panel for a selected intersection. */

import { AlertTriangle, ShieldAlert } from "lucide-react";
import { Area, AreaChart, ResponsiveContainer, XAxis, YAxis } from "recharts";

import { DensityBar } from "./DensityBar";
import { SignalTimer } from "./SignalTimer";
import { AlertBadge } from "../shared/AlertBadge";
import { SignalLight } from "../shared/SignalLight";
import type { Alert, IntersectionState } from "../../types";

interface IntersectionPanelProps {
  intersection: IntersectionState | null;
}

export function IntersectionPanel({ intersection }: IntersectionPanelProps) {
  if (intersection === null) {
    return (
      <aside className="rounded-3xl border border-dashed border-um-border bg-um-surface/70 p-6 text-um-muted">
        Select an intersection from the map to inspect live timings, density, and emergency overrides.
      </aside>
    );
  }

  const waitSeries = Array.from({ length: 10 }, (_, index) => ({
    name: `${index}`,
    value: Math.max(0, intersection.wait_time_avg + (index % 2 === 0 ? 2 : -2)),
  }));

  const alerts: Alert[] = [];
  if (intersection.override) {
    alerts.push({
      id: `${intersection.id}-override`,
      kind: "emergency",
      title: "Emergency Corridor Active",
      message: "",
      timestamp: intersection.last_updated,
    });
  }
  if (intersection.fault) {
    alerts.push({
      id: `${intersection.id}-fault`,
      kind: "fault",
      title: "Hardware Fault - Fixed Timer Mode",
      message: "",
      timestamp: intersection.last_updated,
    });
  }

  const ewRemaining = Math.max(0, intersection.ew_green_duration - intersection.ew_phase_seconds);
  const nsRemaining = Math.max(0, intersection.ns_green_duration - intersection.ew_phase_seconds);

  return (
    <aside className="space-y-6 rounded-3xl border border-um-border bg-um-surface/90 p-6">
      <div className="space-y-2">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="font-display text-2xl text-white">{intersection.name}</h3>
            <p className="font-mono text-xs text-um-muted">
              {intersection.lat.toFixed(3)}, {intersection.lng.toFixed(3)}
            </p>
          </div>
          {intersection.fault ? (
            <ShieldAlert className="h-6 w-6 text-um-amber" />
          ) : (
            <AlertTriangle className="h-6 w-6 text-um-cyan" />
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          {alerts.map((alert) => (
            <AlertBadge key={alert.id} alert={alert} />
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-3 rounded-2xl border border-um-border bg-black/20 p-4">
          <SignalLight state={intersection.ew_green ? "green" : "red"} direction="EW" />
          <SignalTimer seconds={ewRemaining} label="E-W Remaining" />
        </div>
        <div className="space-y-3 rounded-2xl border border-um-border bg-black/20 p-4">
          <SignalLight state={intersection.ew_green ? "red" : "green"} direction="NS" />
          <SignalTimer seconds={nsRemaining} label="N-S Remaining" />
        </div>
      </div>

      <div className="space-y-4">
        <DensityBar label="E-W" count={intersection.density_ew} />
        <DensityBar label="N-S" count={intersection.density_ns} />
      </div>

      <div className="grid grid-cols-2 gap-4 text-sm text-um-text">
        <div className="rounded-2xl border border-um-border bg-black/20 p-4">
          Queue E-W: <span className="font-mono text-um-cyan">{intersection.queue_ew.toFixed(1)}m</span>
        </div>
        <div className="rounded-2xl border border-um-border bg-black/20 p-4">
          Queue N-S: <span className="font-mono text-um-cyan">{intersection.queue_ns.toFixed(1)}m</span>
        </div>
      </div>

      <div className="rounded-2xl border border-um-border bg-black/20 p-4">
        <div className="mb-3 text-xs uppercase tracking-[0.22em] text-um-muted">Wait Time Trend</div>
        <div className="h-28">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={waitSeries}>
              <defs>
                <linearGradient id="waitGradient" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="5%" stopColor="var(--um-cyan)" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="var(--um-cyan)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="name" hide />
              <YAxis hide />
              <Area dataKey="value" stroke="var(--um-cyan)" fill="url(#waitGradient)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="rounded-2xl border border-um-border bg-black/20 p-4 font-mono text-sm text-um-text">
        Webster's current calculation: EW: {intersection.ew_green_duration}s | NS: {intersection.ns_green_duration}s | Cycle:{" "}
        {intersection.ew_green_duration + intersection.ns_green_duration + 8}s
      </div>
    </aside>
  );
}
