import { deactivateEmergency } from '../api/client'

export default function EmergencyPanel({ emergencies, onRefresh }) {
  const handleDeactivate = async (vehicleId) => {
    const confirmed = window.confirm(`Deactivate corridor for ${vehicleId}?`)
    if (!confirmed) {
      return
    }
    await deactivateEmergency(vehicleId)
    if (onRefresh) {
      onRefresh()
    }
  }

  return (
    <div className="panel h-full rounded-3xl border p-5">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-muted">Emergency Grid</p>
          <h2 className="mt-2 font-display text-2xl">Active Corridors</h2>
        </div>
        <span className="rounded-full bg-emergency/20 px-3 py-1 text-xs font-semibold text-emergency">
          {emergencies.length}
        </span>
      </div>

      <div className="mt-6 space-y-4">
        {emergencies.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-white/10 p-4 text-sm text-muted">
            No active emergency vehicles.
          </div>
        ) : null}
        {emergencies.map((emergency) => (
          <div key={emergency.vehicle_id} className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-muted">{emergency.vehicle_type}</p>
                <h3 className="mt-1 font-display text-lg">{emergency.vehicle_id}</h3>
              </div>
              <button
                className="rounded-full border border-emergency/60 px-3 py-1 text-sm text-emergency transition hover:bg-emergency/10"
                onClick={() => handleDeactivate(emergency.vehicle_id)}
              >
                Deactivate
              </button>
            </div>
            <div className="mt-4 space-y-2 text-sm">
              {emergency.route.map((intersectionId) => {
                const passed = !emergency.pre_empted_intersections.includes(intersectionId)
                return (
                  <div key={intersectionId} className="flex items-center justify-between rounded-xl bg-shell/60 px-3 py-2">
                    <span>{intersectionId}</span>
                    <span className={passed ? 'text-success' : 'text-emergency'}>
                      {passed ? 'passed' : 'pre-empted'}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
