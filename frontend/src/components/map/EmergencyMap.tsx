import { useEffect, Fragment } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { EmergencyVehicle } from '../../types';

// Hardcoded coordinates from backend for visual reference
export const INTERSECTION_COORDS: Record<string, [number, number]> = {
  int_001: [28.6315, 77.2167],
  int_002: [28.6273, 77.2348],
  int_003: [28.5672, 77.2100],
  int_004: [28.5494, 77.2044],
  int_005: [28.5675, 77.2345],
  int_006: [28.5485, 77.2513],
  int_007: [28.6443, 77.1901],
  int_008: [28.5815, 77.0592],
  int_009: [28.7299, 77.1264],
};

function MapUpdater({ center }: { center: [number, number] }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, map.getZoom(), { animate: true });
  }, [center, map]);
  return null;
}

// Custom icons
const createCustomIcon = (color: string) => {
  return L.divIcon({
    className: 'custom-icon',
    html: `
      <div style="
        background-color: ${color};
        width: 12px;
        height: 12px;
        border-radius: 50%;
        border: 2px solid white;
        box-shadow: 0 0 10px ${color};
      "></div>
    `,
    iconSize: [12, 12],
    iconAnchor: [6, 6],
  });
};

const ambulanceIcon = createCustomIcon('#ff4444');
const fireIcon = createCustomIcon('#ffaa00');
const policeIcon = createCustomIcon('#00ccff');
const intersectionIcon = createCustomIcon('#44ff44');
const clearedIntersectionIcon = createCustomIcon('#888888');

const getVehicleIcon = (type: string) => {
  switch (type) {
    case 'ambulance': return ambulanceIcon;
    case 'fire': return fireIcon;
    case 'police': return policeIcon;
    default: return ambulanceIcon;
  }
};

interface EmergencyMapProps {
  activeVehicles: EmergencyVehicle[];
}

export function EmergencyMap({ activeVehicles }: EmergencyMapProps) {
  // Delhi center
  const defaultCenter: [number, number] = [28.6139, 77.2090];
  
  // Center map on the first active vehicle if available and has valid coords
  const center: [number, number] = activeVehicles.length > 0 && 
    typeof activeVehicles[0].lat === 'number' && 
    typeof activeVehicles[0].lng === 'number' &&
    !isNaN(activeVehicles[0].lat)
    ? [activeVehicles[0].lat, activeVehicles[0].lng]
    : defaultCenter;

  return (
    <div className="w-full h-full rounded-lg overflow-hidden border border-border">
      <MapContainer 
        center={center} 
        zoom={14} 
        style={{ height: '100%', width: '100%', background: '#0a0a0a' }}
        zoomControl={false}
      >
        <MapUpdater center={center} />
        
        {/* Dark mode tiles - CartoDB Dark Matter */}
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        />

        {/* Draw all intersections as background context */}
        {Object.entries(INTERSECTION_COORDS).map(([id, coords]) => {
          // Check if this intersection is in ANY active vehicle's corridor and not yet cleared
          let isUpcoming = false;
          let isCleared = false;
          let attachedVehicle = null;

          for (const v of activeVehicles) {
            if (!v.corridor_intersections) continue;
            const idx = v.corridor_intersections.indexOf(id);
            if (idx !== -1) {
              attachedVehicle = v;
              if (idx >= v.current_intersection_idx) {
                isUpcoming = true;
              } else {
                isCleared = true;
              }
            }
          }

          let icon = intersectionIcon;
          if (attachedVehicle) {
            if (isUpcoming) icon = createCustomIcon('#ff0055'); // active corridor
            else if (isCleared) icon = clearedIntersectionIcon;
          }

          return (
            <Marker key={id} position={coords} icon={icon}>
              <Popup className="custom-popup">
                <div className="font-mono text-xs text-text">
                  <strong>{id}</strong>
                  {isUpcoming && <div className="text-red mt-1">Awaiting vehicle crossing</div>}
                  {isCleared && <div className="text-muted mt-1">Vehicle cleared</div>}
                </div>
              </Popup>
            </Marker>
          );
        })}

        {/* Draw vehicle tracks and polylines */}
        {activeVehicles.map(v => {
          if (v.lat === undefined || v.lng === undefined) return null;
          const vPos: [number, number] = [v.lat, v.lng];
          const gpsTrail = (v.gps_history || [])
            .filter((point) => typeof point.lat === 'number' && typeof point.lng === 'number')
            .map((point) => [point.lat, point.lng] as [number, number]);
          
          // Draw a line from vehicle to upcoming intersections
          const upcomingPoints = (v.corridor_intersections || [])
            .slice(v.current_intersection_idx || 0)
            .map(id => INTERSECTION_COORDS[id])
            .filter(Boolean);
          const alternatePoints = (v.alternate_corridor_intersections || [])
            .map(id => INTERSECTION_COORDS[id])
            .filter(Boolean);
            
          const routePoints = [vPos, ...upcomingPoints];
          const alternateRoutePoints = [vPos, ...alternatePoints];

          return (
            <Fragment key={v.id}>
              {gpsTrail.length > 1 && (
                <Polyline
                  positions={gpsTrail}
                  color="#00ccff"
                  weight={3}
                  opacity={0.7}
                />
              )}
              {/* Highlight active corridor route */}
              {routePoints.length > 1 && (
                <Polyline 
                  positions={routePoints} 
                  color="#ff4444" 
                  weight={4} 
                  opacity={0.6} 
                  dashArray="5, 10" 
                  className="animate-pulse"
                />
              )}
              {alternateRoutePoints.length > 1 && (
                <Polyline
                  positions={alternateRoutePoints}
                  color="#ffaa00"
                  weight={3}
                  opacity={0.8}
                  dashArray="8, 8"
                />
              )}
              
              <Marker position={vPos} icon={getVehicleIcon(v.type)} zIndexOffset={1000}>
                <Popup className="custom-popup">
                  <div className="font-mono text-xs">
                    <strong className="text-red uppercase">{v.type}</strong>
                    <br />
                    Speed: {Math.round(v.speed_kmh)} km/h
                    <br />
                    ETA: {Math.round(v.eta_seconds)}s
                    <br />
                    Route: {v.route_status || 'Primary Corridor Stable'}
                    {v.reroute_recommendation ? (
                      <>
                        <br />
                        Advisory: {v.reroute_recommendation}
                      </>
                    ) : null}
                  </div>
                </Popup>
              </Marker>
            </Fragment>
          );
        })}
      </MapContainer>
    </div>
  );
}
