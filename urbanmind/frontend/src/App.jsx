import { useMemo, useState } from 'react'
import EmergencyPanel from './components/EmergencyPanel'
import IntersectionCard from './components/IntersectionCard'
import IntersectionMap from './components/IntersectionMap'
import StatsBar from './components/StatsBar'
import { useWebSocket } from './hooks/useWebSocket'

export default function App() {
  const { intersections, emergencies, connected, lastUpdated } = useWebSocket()
  const [selectedIntersection, setSelectedIntersection] = useState(null)

  const enrichedIntersections = useMemo(
    () =>
      intersections.map((intersection, index) => ({
        ...intersection,
        location: intersection.location || {
          lat: Number(import.meta.env.VITE_CITY_CENTER_LAT || 28.6139) + index * 0.01,
          lon: Number(import.meta.env.VITE_CITY_CENTER_LON || 77.209) + index * 0.01
        }
      })),
    [intersections]
  )

  const selected =
    enrichedIntersections.find((intersection) => intersection.intersection_id === selectedIntersection?.intersection_id) ||
    enrichedIntersections[0] ||
    null

  return (
    <div className="flex min-h-screen flex-col px-4 py-4 text-ink lg:px-6">
      <div className="mx-auto flex w-full max-w-[1700px] flex-1 flex-col gap-4">
        <StatsBar
          intersections={enrichedIntersections}
          emergencies={emergencies}
          connected={connected}
          lastUpdated={lastUpdated}
        />

        <div className="grid gap-4 xl:grid-cols-[20rem_minmax(0,1fr)_24rem]">
          <aside className="panel rounded-3xl border p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-muted">Network</p>
                <h2 className="mt-2 font-display text-2xl">Intersections</h2>
              </div>
              <span
                className={`rounded-full px-3 py-1 text-xs font-semibold ${
                  connected ? 'bg-success/20 text-success' : 'bg-emergency/20 text-emergency'
                }`}
              >
                {connected ? 'Live' : 'Retrying'}
              </span>
            </div>
            <div className="mt-6 space-y-3">
              {enrichedIntersections.map((intersection) => (
                <button
                  key={intersection.intersection_id}
                  className={`w-full rounded-2xl border px-4 py-3 text-left transition ${
                    selected?.intersection_id === intersection.intersection_id
                      ? 'border-accent bg-accent/10'
                      : 'border-white/10 bg-white/5 hover:bg-white/10'
                  }`}
                  onClick={() => setSelectedIntersection(intersection)}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold">{intersection.intersection_id}</span>
                    <span className="text-xs text-muted">
                      {intersection.current_signal_plan?.cycle_length || 0}s cycle
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </aside>

          <main className="grid gap-4">
            <IntersectionMap
              intersections={enrichedIntersections}
              selectedId={selected?.intersection_id}
              onSelect={setSelectedIntersection}
            />
            <IntersectionCard intersection={selected} />
          </main>

          <aside>
            <EmergencyPanel emergencies={emergencies} />
          </aside>
        </div>

        <footer className="panel rounded-3xl border px-4 py-3 text-center text-sm text-muted">
          Designed and Developed By Anurag Singh
        </footer>
      </div>
    </div>
  )
}
