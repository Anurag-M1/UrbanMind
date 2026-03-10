import { CircleMarker, MapContainer, TileLayer, Tooltip } from 'react-leaflet'

function congestionColor(level) {
  if (level === 'HIGH') return '#FF6B35'
  if (level === 'MED') return '#FACC15'
  return '#22C55E'
}

function summarizeCongestion(intersection) {
  const values = Object.values(intersection?.lane_densities || {}).map((lane) => lane.congestion_level)
  if (values.includes('HIGH')) return 'HIGH'
  if (values.includes('MED')) return 'MED'
  return 'LOW'
}

export default function IntersectionMap({ intersections, selectedId, onSelect }) {
  const center = [
    Number(import.meta.env.VITE_CITY_CENTER_LAT || 28.6139),
    Number(import.meta.env.VITE_CITY_CENTER_LON || 77.209)
  ]

  return (
    <div className="panel h-[32rem] rounded-3xl border p-3">
      <MapContainer center={center} zoom={13} scrollWheelZoom className="h-full w-full">
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {intersections.map((intersection, index) => {
          const lat = Number(intersection?.location?.lat || center[0] + index * 0.01)
          const lon = Number(intersection?.location?.lon || center[1] + index * 0.01)
          const level = summarizeCongestion(intersection)
          const emergency = intersection.emergency_active
          return (
            <CircleMarker
              key={intersection.intersection_id}
              center={[lat, lon]}
              radius={selectedId === intersection.intersection_id ? 18 : 14}
              pathOptions={{
                color: emergency ? '#FF6B35' : congestionColor(level),
                fillColor: emergency ? '#FF6B35' : congestionColor(level),
                fillOpacity: emergency ? 0.9 : 0.75,
                weight: 2
              }}
              eventHandlers={{ click: () => onSelect(intersection) }}
            >
              <Tooltip direction="top" offset={[0, -8]} opacity={1}>
                <div className="font-body text-sm">
                  <div className="font-semibold">{intersection.intersection_id}</div>
                  <div>{level} congestion</div>
                  <div>{emergency ? 'Emergency corridor' : 'Adaptive timing active'}</div>
                </div>
              </Tooltip>
            </CircleMarker>
          )
        })}
      </MapContainer>
    </div>
  )
}
