import { useEffect, useState } from 'react';
import { useEmergency } from '../hooks/useEmergency';
import { DispatchPanel, CorridorTracker, EventHistory } from '../components/emergency/EmergencyComponents';
import { EmergencyMap } from '../components/map/EmergencyMap';
import { getEmergencyHistory, getActiveEmergencies } from '../api/emergency';
import { useEmergencyStore } from '../store/emergencyStore';
import type { EmergencyEvent } from '../types';
import { Shield, Activity, Radio } from 'lucide-react';

export default function Emergency() {
  const { activeVehicles, corridorMessage } = useEmergency();
  const setActiveVehicles = useEmergencyStore(s => s.setActiveVehicles);
  const [events, setEvents] = useState<EmergencyEvent[]>([]);

  useEffect(() => {
    const load = async () => {
      try {
        const { events: evts } = await getEmergencyHistory();
        setEvents(evts);
        const { active } = await getActiveEmergencies();
        if (Array.isArray(active) && active.length > 0) {
          const validated = active.map((entry) => {
            const v = entry?.vehicle ?? entry;
            return {
            ...v,
            corridor_intersections: Array.isArray(v.corridor_intersections) ? v.corridor_intersections : [],
            alternate_corridor_intersections: Array.isArray(v.alternate_corridor_intersections) ? v.alternate_corridor_intersections : [],
            congestion_hotspots: Array.isArray(v.congestion_hotspots) ? v.congestion_hotspots : [],
            gps_history: Array.isArray(v.gps_history) ? v.gps_history : [],
            current_intersection_idx: v.current_intersection_idx ?? 0,
            lat: typeof v.lat === 'number' ? v.lat : 28.6139,
            lng: typeof v.lng === 'number' ? v.lng : 77.2090
          };
          }).filter(v => v.id);
          setActiveVehicles(validated);
        }
      } catch { /* ignore */ }
    };
    load();
    const interval = setInterval(load, 2000);
    return () => clearInterval(interval);
  }, [setActiveVehicles]);

  return (
    <div className="h-full flex flex-col p-8 gap-8 bg-[#f5f7fa] animate-in fade-in duration-700 overflow-hidden">
      {/* Official Tactical Header */}
      <div className="flex items-center justify-between border-b-2 border-red-600/10 pb-6 shrink-0">
        <div className="flex items-center gap-5">
          <div className="p-4 rounded bg-white border border-red-100 shadow-sm relative">
            <Shield size={32} className="text-red-600" />
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-600 rounded-full animate-ping" />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[10px] font-black text-red-600/60 uppercase tracking-[0.4em]">Tactical Operations Bureau</span>
              <div className="px-1.5 py-0.5 bg-red-600 text-white text-[8px] font-black uppercase rounded">Priority One</div>
            </div>
            <h1 className="text-3xl font-black text-navy uppercase tracking-tight">Ops Control Center</h1>
          </div>
        </div>
        <div className="hidden md:flex items-center gap-4 bg-white px-5 py-3 rounded border border-[#d1d9e2] shadow-sm">
          <Activity size={16} className="text-red-600 animate-pulse" />
          <div className="flex flex-col">
            <span className="text-[9px] font-black text-navy/40 uppercase tracking-widest">Network Secure</span>
            <span className="text-xs font-black text-red-600 uppercase">Emergency Active</span>
          </div>
        </div>
      </div>

      <div className="flex-1 min-h-0 flex gap-8">
        {/* Left Control Sidebar */}
        <div className="w-96 flex flex-col gap-8 overflow-y-auto pr-2 custom_scrollbar">
          <div className="bg-white rounded-lg border-2 border-navy/10 shadow-lg p-5">
            <div className="flex items-center gap-2 mb-4 border-b border-gray-100 pb-3">
               <Radio size={16} className="text-navy" />
               <span className="text-[10px] font-black text-navy uppercase tracking-widest">Rapid Dispatch Terminal</span>
            </div>
            <DispatchPanel activeVehicles={activeVehicles} />
          </div>
          
          {corridorMessage && (
            <div className="rounded-lg bg-red-600 p-5 text-white shadow-xl animate-pulse relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-24 h-24 bg-white/10 -mr-12 -mt-12 rounded-full" />
              <p className="text-[10px] font-black uppercase tracking-[0.3em] text-white/60 mb-1">Active Command</p>
              <p className="text-sm font-black uppercase tracking-widest leading-tight">{corridorMessage}</p>
            </div>
          )}

          <div className="space-y-4">
            <div className="flex items-center justify-between px-2">
               <h2 className="text-[10px] font-black text-navy/40 uppercase tracking-[0.3em]">
                 En-Route Units ({activeVehicles.length})
               </h2>
               <div className="w-1.5 h-1.5 rounded-full bg-navy/20" />
            </div>
            {activeVehicles.length > 0 ? (
              <div className="space-y-4">
                {activeVehicles.map(v => (
                  <div key={v.id} className="bg-white rounded border-2 border-navy/10 p-4 shadow-sm hover:border-navy/30 transition-colors">
                    <CorridorTracker vehicle={v} />
                  </div>
                ))}
              </div>
            ) : (
              <div className="rounded-lg border-2 border-dashed border-navy/10 bg-white/50 p-8 text-center">
                <p className="text-[10px] font-black text-navy/40 uppercase tracking-widest mb-1">Grid Pattern Idle</p>
                <p className="text-[9px] text-navy/30 font-medium uppercase tracking-tighter">Initialize Protocol via Dispatch for GPS Tracking</p>
              </div>
            )}
          </div>

          <div className="space-y-4 mt-auto pt-6 border-t-2 border-navy/5">
            <h2 className="text-[10px] font-black text-navy/40 uppercase tracking-[0.3em] px-2">
              TACTICAL LOG HISTORY
            </h2>
            <div className="bg-white rounded border-2 border-navy/10 p-5 shadow-sm">
              <EventHistory events={events} />
            </div>
          </div>
        </div>

        {/* Right Main Tactical Map */}
        <div className="flex-1 rounded-lg border-4 border-white bg-white overflow-hidden relative shadow-2xl group">
          <EmergencyMap activeVehicles={activeVehicles} />
          
          {/* Map Overlay Accents */}
          <div className="absolute top-6 left-6 p-3 bg-navy/90 border border-white/20 rounded shadow-2xl backdrop-blur-md pointer-events-none">
             <div className="flex flex-col">
                <span className="text-[8px] font-black text-white/50 uppercase tracking-[0.3em]">Sector Focus</span>
                <span className="text-[10px] font-black text-white uppercase tracking-widest">Delhi_NCR_Tactical</span>
             </div>
          </div>
          
          {/* Scanline Effect for Map */}
          <div className="absolute inset-0 pointer-events-none bg-scanlines opacity-[0.02]" />
        </div>
      </div>
    </div>
  );
}
