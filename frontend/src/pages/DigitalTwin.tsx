'use client';

import React, { lazy, Suspense, useMemo } from 'react';
import { Activity, MapPinned, Shield, Siren } from 'lucide-react';
import { GovCard } from '@/components/common/gov-card';
import { useTrafficStore } from '@/lib/store';
import { deriveTrafficMetrics } from '@/lib/traffic-metrics';

const City3D = lazy(() => import('@/components/City3D/City3D'));

export default function DigitalTwin() {
  const {
    intersections,
    selectedIntersection,
    totalVehicles,
    networkAvgWait,
    activeEmergencies,
    emissionsSaved,
    uptimeSeconds,
    websterRecalculations,
  } = useTrafficStore();
  const setSelectedIntersection = useTrafficStore((state) => state.setSelectedIntersection);

  const metrics = useMemo(
    () =>
      deriveTrafficMetrics(intersections, {
        total_vehicles: totalVehicles,
        network_avg_wait: networkAvgWait,
        active_emergencies: activeEmergencies,
        emissions_saved_pct: emissionsSaved,
        uptime_seconds: uptimeSeconds,
        webster_recalculations: websterRecalculations,
      }),
    [intersections, totalVehicles, networkAvgWait, activeEmergencies, emissionsSaved, uptimeSeconds, websterRecalculations]
  );

  const hotspots = useMemo(
    () =>
      [...intersections]
        .sort((a, b) => b.avgWaitTime + b.nsDensity + b.ewDensity - (a.avgWaitTime + a.nsDensity + a.ewDensity))
        .slice(0, 5),
    [intersections]
  );

  const selectedDetails = intersections.find((intersection) => intersection.id === selectedIntersection) ?? hotspots[0];

  return (
    <div className="flex min-h-full w-full flex-col overflow-y-auto bg-[#f5f7fa] p-4 animate-in fade-in duration-700 sm:p-6 lg:p-8">
      <div className="mb-6 flex flex-col gap-4 border-b-2 border-navy/10 pb-6 lg:mb-8 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="mb-2 flex items-center gap-2">
            <div className="h-6 w-1.5 bg-saffron" />
            <div className="h-6 w-1.5 border border-gray-200 bg-white" />
            <div className="h-6 w-1.5 bg-green" />
            <h3 className="ml-2 text-[10px] font-black uppercase tracking-[0.3em] text-navy/40">Spatial Intelligence Module</h3>
          </div>
          <h1 className="text-3xl font-black uppercase tracking-tight text-navy sm:text-4xl">3D City Digital Twin</h1>
          <p className="mt-1 font-medium text-navy/50">Metropolitan spatial simulation with synchronized live traffic telemetry.</p>
        </div>
        <div className="flex items-center gap-3 rounded border border-[#d1d9e2] bg-white p-4 shadow-sm">
          <div className="h-2 w-2 rounded-full bg-green animate-pulse" />
          <span className="text-[10px] font-black uppercase tracking-widest text-navy">Simulation Synchronized</span>
        </div>
      </div>

      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 2xl:grid-cols-4">
        <GovCard accent="navy" className="p-4">
          <p className="text-[10px] font-black uppercase tracking-widest text-navy/40">Tracked Vehicles</p>
          <p className="mt-2 text-3xl font-black text-navy">{metrics.totalVehicles.toLocaleString('en-IN')}</p>
        </GovCard>
        <GovCard accent="white" className="p-4">
          <p className="text-[10px] font-black uppercase tracking-widest text-navy/40">Network Wait</p>
          <p className="mt-2 text-3xl font-black text-navy">{Math.round(metrics.networkAvgWait)}s</p>
        </GovCard>
        <GovCard accent="saffron" className="p-4">
          <p className="text-[10px] font-black uppercase tracking-widest text-navy/40">Hotspot Sectors</p>
          <p className="mt-2 text-3xl font-black text-navy">{metrics.congestedCount}</p>
        </GovCard>
        <GovCard accent="green" className="p-4">
          <p className="text-[10px] font-black uppercase tracking-widest text-navy/40">Live Emergencies</p>
          <p className="mt-2 text-3xl font-black text-navy">{metrics.activeEmergencies}</p>
        </GovCard>
      </div>

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-6 2xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="group relative min-h-[360px] overflow-hidden rounded-lg border-2 border-navy/10 bg-white shadow-xl sm:min-h-[440px] lg:min-h-[560px]">
          <Suspense
            fallback={
              <div className="flex h-full w-full flex-col items-center justify-center bg-[#f8f9fa]">
                <div className="mb-4 rounded-full bg-navy/5 p-4">
                  <Shield size={48} className="animate-pulse text-navy" />
                </div>
                <span className="text-[10px] font-black uppercase tracking-[0.4em] text-navy/40 animate-pulse">
                  Initializing Spatial Model
                </span>
              </div>
            }
          >
            <City3D intersections={intersections} onIntersectionSelect={setSelectedIntersection} />
          </Suspense>

          <div className="pointer-events-none absolute bottom-4 left-4 rounded border border-white/20 bg-navy/90 p-4 shadow-2xl backdrop-blur-md sm:bottom-6 sm:left-6">
            <p className="mb-1 text-[9px] font-black uppercase tracking-widest text-white/50">Rendering Protocol</p>
            <p className="text-xs font-bold uppercase tracking-tight text-white">high-fidelity photogrammetry</p>
          </div>

          <div className="pointer-events-none absolute left-0 top-0 h-12 w-12 border-l-2 border-t-2 border-navy/20" />
          <div className="pointer-events-none absolute bottom-0 right-0 h-12 w-12 border-b-2 border-r-2 border-navy/20" />
        </div>

        <div className="grid min-h-0 gap-6 xl:grid-cols-2 2xl:grid-cols-1">
          <GovCard title="LIVE HOTSPOT PRIORITY" className="flex min-h-0 flex-col p-4">
            <div className="space-y-3 overflow-y-auto pr-1 2xl:max-h-[340px]">
              {hotspots.map((intersection) => (
                <button
                  key={intersection.id}
                  type="button"
                  onClick={() => setSelectedIntersection(intersection.id)}
                  className="w-full rounded border border-[#d1d9e2] p-3 text-left transition hover:border-navy/30 hover:bg-[#f8f9fa]"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <p className="truncate text-[11px] font-black uppercase tracking-tight text-navy">{intersection.name}</p>
                      <p className="mt-1 text-[10px] font-medium uppercase tracking-wider text-navy/40">
                        {Math.round(intersection.avgWaitTime)}s avg wait • {Math.round(intersection.nsDensity + intersection.ewDensity)} density
                      </p>
                    </div>
                    <MapPinned size={16} className="shrink-0 text-navy/50" />
                  </div>
                </button>
              ))}
            </div>
          </GovCard>

          {selectedDetails && (
            <GovCard title="SELECTED INTERSECTION" className="flex min-h-0 flex-col p-4">
              <div className="space-y-4 overflow-y-auto pr-1">
                <div>
                  <p className="text-lg font-black text-navy">{selectedDetails.name}</p>
                  <p className="text-[10px] font-mono uppercase tracking-wide text-navy/40">
                    {Math.round(selectedDetails.lat)} / {Math.round(selectedDetails.lng)}
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded bg-[#f8f9fa] p-3">
                    <div className="mb-1 flex items-center gap-2 text-navy/50">
                      <Activity size={14} />
                      <span className="text-[9px] font-black uppercase tracking-widest">Wait</span>
                    </div>
                    <p className="text-xl font-black text-navy">{Math.round(selectedDetails.avgWaitTime)}s</p>
                  </div>
                  <div className="rounded bg-[#f8f9fa] p-3">
                    <div className="mb-1 flex items-center gap-2 text-navy/50">
                      <Siren size={14} />
                      <span className="text-[9px] font-black uppercase tracking-widest">Status</span>
                    </div>
                    <p className="text-xl font-black uppercase text-navy">{selectedDetails.status}</p>
                  </div>
                </div>
                <div className="space-y-3">
                  <div>
                    <div className="mb-1 flex items-center justify-between text-[10px] font-bold uppercase tracking-wide text-navy/50">
                      <span>N-S Density</span>
                      <span>{Math.round(selectedDetails.nsDensity)}%</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-gray-100">
                      <div className="h-full bg-navy" style={{ width: `${Math.min(100, selectedDetails.nsDensity)}%` }} />
                    </div>
                  </div>
                  <div>
                    <div className="mb-1 flex items-center justify-between text-[10px] font-bold uppercase tracking-wide text-navy/50">
                      <span>E-W Density</span>
                      <span>{Math.round(selectedDetails.ewDensity)}%</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-gray-100">
                      <div className="h-full bg-saffron" style={{ width: `${Math.min(100, selectedDetails.ewDensity)}%` }} />
                    </div>
                  </div>
                </div>
              </div>
            </GovCard>
          )}
        </div>
      </div>
    </div>
  );
}
