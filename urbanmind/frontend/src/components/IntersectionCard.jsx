import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import SignalPhaseDisplay from './SignalPhaseDisplay'

function laneColor(level) {
  if (level === 'HIGH') return 'bg-red-500'
  if (level === 'MED') return 'bg-yellow-400'
  return 'bg-success'
}

export default function IntersectionCard({ intersection }) {
  if (!intersection) {
    return (
      <div className="panel flex h-full items-center justify-center rounded-3xl border p-6 text-center text-muted">
        Click an intersection on the map to inspect live density and signal timing.
      </div>
    )
  }

  const lanes = Object.entries(intersection.lane_densities || {})
  const trendData = lanes.map(([laneId, lane], index) => ({
    minute: `${index + 1}m`,
    wait: lane.queue_length * 6 + lane.count * 2
  }))

  return (
    <div className="panel h-full rounded-3xl border p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-muted">Intersection</p>
          <h2 className="mt-2 font-display text-2xl">{intersection.intersection_id}</h2>
        </div>
        {intersection.emergency_active ? (
          <span className="rounded-full bg-emergency/20 px-3 py-1 text-xs font-semibold text-emergency">
            Emergency corridor active
          </span>
        ) : null}
      </div>

      <div className="mt-6 grid gap-5">
        <div>
          <p className="mb-3 text-xs uppercase tracking-[0.24em] text-muted">Per-lane Density</p>
          <div className="grid gap-3">
            {lanes.map(([laneId, lane]) => (
              <div key={laneId}>
                <div className="mb-2 flex items-center justify-between text-sm">
                  <span>{laneId}</span>
                  <span className="text-muted">
                    {lane.count} vehicles / queue {lane.queue_length}
                  </span>
                </div>
                <div className="h-3 rounded-full bg-white/10">
                  <div
                    className={`h-3 rounded-full ${laneColor(lane.congestion_level)}`}
                    style={{ width: `${Math.min(100, lane.count * 12 + lane.queue_length * 8)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <SignalPhaseDisplay plan={intersection.current_signal_plan} />

        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <div className="mb-4 flex items-center justify-between">
            <p className="text-xs uppercase tracking-[0.24em] text-muted">5-minute Wait Trend</p>
            <span className="text-sm text-muted">
              Cycle {intersection.current_signal_plan?.cycle_length || 0}s
            </span>
          </div>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData}>
                <XAxis dataKey="minute" stroke="#6C8CA1" />
                <YAxis stroke="#6C8CA1" />
                <Tooltip />
                <Line type="monotone" dataKey="wait" stroke="#00C2CB" strokeWidth={3} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  )
}
