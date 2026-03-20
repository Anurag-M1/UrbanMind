/* Flow chart for hourly traffic volume. */

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { TimeSeriesPoint } from "../../types";

interface FlowChartProps {
  data: TimeSeriesPoint[];
}

export function FlowChart({ data }: FlowChartProps) {
  return (
    <div className="h-72 rounded-3xl border border-um-border bg-um-surface/90 p-4">
      <div className="mb-4 text-xs uppercase tracking-[0.22em] text-um-muted">Hourly Vehicle Flow</div>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <CartesianGrid stroke="rgba(74,104,120,0.25)" />
          <XAxis dataKey="timestamp" tick={false} stroke="var(--um-muted)" />
          <YAxis stroke="var(--um-muted)" />
          <Tooltip />
          <Area dataKey="value" stroke="var(--um-cyan)" fill="rgba(0, 217, 255, 0.14)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
