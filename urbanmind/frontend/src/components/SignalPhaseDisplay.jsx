export default function SignalPhaseDisplay({ plan }) {
  const currentPhase = plan?.phases?.[0]

  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-muted">Current Phase</p>
          <p className="mt-2 font-display text-xl text-ink">
            {currentPhase?.direction || 'No active phase'}
          </p>
        </div>
        <div className="rounded-full bg-accent/15 px-4 py-2 text-sm font-semibold text-accent">
          {currentPhase?.green_duration || 0}s green
        </div>
      </div>
      <div className="mt-4 grid gap-2">
        {(plan?.phases || []).map((phase) => (
          <div
            key={phase.direction}
            className="flex items-center justify-between rounded-xl bg-shell/70 px-3 py-2 text-sm"
          >
            <span className="capitalize">{phase.direction}</span>
            <span className="text-muted">{phase.green_duration}s</span>
          </div>
        ))}
      </div>
    </div>
  )
}
