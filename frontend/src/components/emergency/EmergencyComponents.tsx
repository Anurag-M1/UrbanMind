import { useState } from 'react';
import { Ambulance, Flame, Shield, Loader, Radio } from 'lucide-react';
import { simulateEmergency } from '../../api/emergency';
import type { EmergencyVehicle, EmergencyEvent } from '../../types';
import { PulseRing } from '../shared/PulseRing';

interface DispatchPanelProps {
  activeVehicles: EmergencyVehicle[];
  onDispatch?: () => void;
}

export function DispatchPanel({ activeVehicles, onDispatch }: DispatchPanelProps) {
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState('');

  const dispatch = async (type: string) => {
    setLoading(type);
    setError('');
    try {
      await simulateEmergency(type);
      onDispatch?.();
    } catch (err: any) {
      setError(err.message || 'Failed to dispatch');
    }
    setLoading(null);
  };

  const hasActive = (type: string) => activeVehicles.some(v => v.type === type && v.active);
  const hasAny = activeVehicles.length > 0;

  const buttons = [
    { type: 'ambulance', label: 'DISPATCH AMBULANCE', icon: Ambulance, color: 'btn-danger', emoji: '🚑' },
    { type: 'fire', label: 'DISPATCH FIRE ENGINE', icon: Flame, color: 'btn-warning', emoji: '🚒' },
    { type: 'police', label: 'DISPATCH POLICE', icon: Shield, color: 'btn-primary', emoji: '🚔' },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Radio size={16} className={hasAny ? 'text-red' : 'text-green'} />
        <h2 className="font-heading font-semibold text-sm">EMERGENCY DISPATCH CENTER</h2>
      </div>

      <div className={`text-xs flex items-center gap-2 ${hasAny ? 'text-red' : 'text-green'}`}>
        <PulseRing color={hasAny ? 'red' : 'green'} size={8} />
        {hasAny
          ? `CORRIDOR ACTIVE · ${activeVehicles.length} vehicle(s)`
          : 'System Ready · No Active Emergencies'}
      </div>

      <div className="space-y-2">
        {buttons.map(({ type, label, icon: Icon, color, emoji }) => (
          <button
            key={type}
            onClick={() => dispatch(type)}
            disabled={hasActive(type) || loading === type}
            className={`btn ${color} w-full justify-center text-sm ${hasActive(type) ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {loading === type ? (
              <Loader size={16} className="animate-spin" />
            ) : (
              <span>{emoji}</span>
            )}
            {hasActive(type) ? `ACTIVE · In Progress` : label}
          </button>
        ))}
      </div>

      {error && <div className="text-xs text-red">{error}</div>}
    </div>
  );
}

export function CorridorTracker({ vehicle }: { vehicle: EmergencyVehicle }) {
  const intersections = Array.isArray(vehicle.corridor_intersections) ? vehicle.corridor_intersections : [];
  const alternateCorridor = Array.isArray(vehicle.alternate_corridor_intersections) ? vehicle.alternate_corridor_intersections : [];
  const congestionHotspots = Array.isArray(vehicle.congestion_hotspots) ? vehicle.congestion_hotspots : [];
  const gpsHistory = Array.isArray(vehicle.gps_history) ? vehicle.gps_history : [];
  const currentIdx = vehicle.current_intersection_idx || 0;
  const progress = intersections.length > 0
    ? (currentIdx / intersections.length) * 100
    : 0;

  return (
    <div className="card card-emergency">
        <h3 className="font-heading text-sm font-semibold text-red">
          {vehicle.type?.toUpperCase() || 'UNIT'} · {vehicle.id?.slice(0, 12) || '---'}
        </h3>

      <div className="grid grid-cols-2 gap-2 text-xs mb-2 bg-black/20 p-2 rounded border border-white/5">
        <div>
          <span className="text-muted block text-[10px] uppercase">Current Speed</span>
          <span className="font-mono text-cyan text-sm">{Math.round(vehicle.speed_kmh || 0)} km/h</span>
        </div>
        <div>
          <span className="text-muted block text-[10px] uppercase">Total ETA</span>
          <span className="font-mono text-amber text-sm">{Math.round(vehicle.eta_seconds || 0)}s</span>
        </div>
        <div className="col-span-2 mt-1">
          <span className="text-muted block text-[10px] uppercase">Next Crossing</span>
          <span className="font-mono text-text">
            {vehicle.current_intersection_idx !== undefined && vehicle.corridor_intersections && vehicle.current_intersection_idx < vehicle.corridor_intersections.length
              ? `${vehicle.corridor_intersections[vehicle.current_intersection_idx]} in ~${Math.ceil((vehicle.eta_seconds || 0) / ((vehicle.corridor_intersections?.length || 0) - (vehicle.current_intersection_idx || 0) + 1))}s`
              : 'Destination Reached'}
          </span>
        </div>
        <div className="col-span-2 mt-1">
          <span className="text-muted block text-[10px] uppercase">GPS Tracking Status</span>
          <span className={`font-mono text-sm ${vehicle.route_status === 'Reroute Advised' ? 'text-amber' : 'text-green'}`}>
            {vehicle.route_status || 'Primary Corridor Stable'}
          </span>
        </div>
      </div>

      <div className="mb-2">
        <div className="flex justify-between text-xs text-muted mb-1">
          <span>Corridor Progress</span>
          <span>{currentIdx}/{intersections.length} cleared</span>
        </div>
        <div className="progress-bar h-1.5">
          <div className="h-full rounded bg-red transition-all duration-1000" style={{ width: `${Math.round(progress)}%` }} />
        </div>
      </div>

      <div className="flex gap-1 flex-wrap">
        {intersections.map((id, i) => (
          <span
            key={`${id}-${i}`}
            className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
              i < currentIdx
                ? 'bg-green/20 text-green'
                : 'bg-red/20 text-red'
            }`}
          >
            {i < currentIdx ? '✓' : '●'} {id}
          </span>
        ))}
      </div>

      <div className="mt-3 space-y-2 rounded border border-white/10 bg-black/20 p-3">
        <div>
          <span className="text-muted block text-[10px] uppercase">Congestion Hotspots</span>
          <span className="font-mono text-xs text-amber">
            {congestionHotspots.length > 0 ? congestionHotspots.join(' • ') : 'No critical congestion on current corridor'}
          </span>
        </div>
        <div>
          <span className="text-muted block text-[10px] uppercase">Reroute / Alternate Option</span>
          <span className="text-xs leading-5 text-text/90">
            {vehicle.reroute_recommendation || 'Primary route remains the fastest emergency path.'}
          </span>
        </div>
        {alternateCorridor.length > 0 && (
          <div>
            <span className="text-muted block text-[10px] uppercase">Alternate Corridor</span>
            <div className="mt-1 flex flex-wrap gap-1">
              {alternateCorridor.map((id) => (
                <span key={`${vehicle.id}-${id}`} className="rounded bg-amber/15 px-1.5 py-0.5 text-[10px] font-mono text-amber">
                  ALT {id}
                </span>
              ))}
            </div>
          </div>
        )}
        <div>
          <span className="text-muted block text-[10px] uppercase">GPS Points Recorded</span>
          <span className="font-mono text-xs text-cyan">{gpsHistory.length}</span>
        </div>
      </div>
    </div>
  );
}

export function EventHistory({ events }: { events: EmergencyEvent[] }) {
  if (events.length === 0) {
    return <div className="text-xs text-muted text-center py-4">No emergency events yet</div>;
  }

  return (
    <div className="space-y-2 max-h-60 overflow-y-auto">
      {events.map((evt) => (
        <div key={evt.id} className="card text-xs">
          <div className="flex justify-between mb-1">
            <span className="font-heading font-semibold">
              {(evt.vehicle_type || 'unit').toUpperCase()}
            </span>
            <span className="text-muted">
              {new Date(evt.activated_at).toLocaleTimeString()}
            </span>
          </div>
          <div className="flex justify-between text-muted">
            <span>{evt.intersections_cleared} intersections cleared</span>
            <span className="text-green font-mono">~{Math.round(evt.response_time_saved_seconds / 60)} min saved</span>
          </div>
        </div>
      ))}
    </div>
  );
}
