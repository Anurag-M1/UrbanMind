/* Wait time chart with fixed-timer baseline comparison. */

import { Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { TimeSeriesPoint } from "../../types";

interface WaitTimeChartProps {
  data: TimeSeriesPoint[];
}

export function WaitTimeChart({ data }: WaitTimeChartProps) {
  return (
    <div className="h-72 rounded-3xl border border-um-border bg-um-surface/90 p-4">
      <div className="mb-4 text-xs uppercase tracking-[0.22em] text-um-muted">Average Wait Time</div>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <XAxis dataKey="timestamp" tick={false} stroke="var(--um-muted)" />
          <YAxis stroke="var(--um-muted)" />
          <Tooltip />
          <ReferenceLine y={45} stroke="var(--um-amber)" strokeDasharray="6 6" />
          <Line type="monotone" dataKey="value" stroke="var(--um-green)" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
