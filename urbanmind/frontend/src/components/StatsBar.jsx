export default function StatsBar({ intersections, emergencies, lastUpdated, connected }) {
  const online = intersections.filter((intersection) => intersection?.timestamp).length
  const waitTimes = intersections.map((intersection) => {
    const totalQueue = Object.values(intersection.lane_densities || {}).reduce((sum, lane) => sum + lane.queue_length, 0)
    const cycle = intersection.current_signal_plan?.cycle_length || 60
    return totalQueue * 4 + cycle / 2
  })
  const averageWait = waitTimes.length
    ? (waitTimes.reduce((sum, value) => sum + value, 0) / waitTimes.length).toFixed(1)
    : '0.0'

  const items = [
    { label: 'Intersections Online', value: `${online}/${intersections.length || online}` },
    { label: 'Average Wait', value: `${averageWait}s` },
    { label: 'Active Corridors', value: emergencies.length },
    { label: 'Telemetry', value: connected ? 'Connected' : 'Reconnecting' }
  ]

  return (
    <div className="panel grid gap-4 rounded-3xl border px-6 py-4 lg:grid-cols-4">
      {items.map((item) => (
        <div key={item.label}>
          <p className="text-xs uppercase tracking-[0.24em] text-muted">{item.label}</p>
          <p className="mt-2 font-display text-2xl text-ink">{item.value}</p>
        </div>
      ))}
      <div className="lg:col-span-4 border-t border-white/10 pt-3 text-xs text-muted">
        Last updated {lastUpdated ? lastUpdated.toLocaleTimeString() : 'waiting for data'}
      </div>
    </div>
  )
}
