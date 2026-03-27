'use client';

import React from 'react';
import { useTrafficStore } from '@/lib/store';
import { GovCard } from '@/components/common/gov-card';

export function IntersectionPanel() {
  const { intersections, selectedIntersection } = useTrafficStore();

  const intersection = intersections.find((i) => i.id === selectedIntersection);

  if (!intersection) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center text-center p-6 bg-gray-50/50 rounded-lg border border-dashed border-gray-300">
        <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 text-navy/20 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <p className="text-navy/40 text-[11px] font-bold uppercase tracking-widest leading-relaxed">
          Select Sector Intersection<br />for Detailed Traffic Data
        </p>
      </div>
    );
  }

  const signalToBg = (signal: string) => (signal === 'green' ? 'bg-green' : signal === 'yellow' ? 'bg-saffron' : 'bg-red-600');

  return (
    <div className="flex h-full min-h-0 w-full flex-col overflow-y-auto pr-1">
      <div className="flex shrink-0 items-end justify-between border-b border-[#d1d9e2] pb-3">
        <div>
          <h2 className="text-lg font-black text-navy uppercase tracking-tight">
            {intersection.name}
          </h2>
          <p className="text-[10px] text-navy/40 font-mono mt-0.5">
            LOC: {Math.round(intersection.lat)}°N / {Math.round(intersection.lng)}°E
          </p>
        </div>
        <div className={`px-2 py-0.5 rounded text-[9px] font-black text-white uppercase tracking-tighter ${intersection.status === 'optimal' ? 'bg-green' : intersection.status === 'congested' ? 'bg-saffron' : 'bg-navy'}`}>
          {intersection.status}
        </div>
      </div>

      <div className="mt-4 space-y-4">
        {/* Signals Section */}
        <div className="grid grid-cols-2 gap-3">
          {/* NS Signal */}
          <GovCard title="N-S SIGNAL" accent={intersection.nsSignal === 'green' ? 'green' : 'navy'} className="p-3">
             <div className="flex items-center justify-between">
                <div className="flex gap-1.5 bg-gray-100 p-1.5 rounded-full border border-gray-200">
                  <div className={`w-3 h-3 rounded-full ${intersection.nsSignal === 'red' ? 'bg-red-600 shadow-[0_0_8px_rgba(220,38,38,0.5)]' : 'bg-gray-300'}`} />
                  <div className={`w-3 h-3 rounded-full ${intersection.nsSignal === 'yellow' ? 'bg-saffron shadow-[0_0_8px_rgba(255,153,51,0.5)]' : 'bg-gray-300'}`} />
                  <div className={`w-3 h-3 rounded-full ${intersection.nsSignal === 'green' ? 'bg-green shadow-[0_0_8px_rgba(19,136,8,0.5)]' : 'bg-gray-300'}`} />
                </div>
                <span className="text-[11px] font-black text-navy uppercase">{intersection.nsSignal}</span>
             </div>
             <div className="mt-3">
                <div className="flex justify-between text-[9px] font-bold text-navy/40 mb-1">
                  <span>PROGRESS</span>
                  <span>{intersection.phaseProgress}%</span>
                </div>
                <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-500 ${signalToBg(intersection.nsSignal)}`}
                    style={{ width: `${intersection.phaseProgress}%` }}
                  />
                </div>
             </div>
          </GovCard>

          {/* EW Signal */}
          <GovCard title="E-W SIGNAL" accent={intersection.ewSignal === 'green' ? 'green' : 'navy'} className="p-3">
             <div className="flex items-center justify-between">
                <div className="flex gap-1.5 bg-gray-100 p-1.5 rounded-full border border-gray-200">
                  <div className={`w-3 h-3 rounded-full ${intersection.ewSignal === 'red' ? 'bg-red-600 shadow-[0_0_8px_rgba(220,38,38,0.5)]' : 'bg-gray-300'}`} />
                  <div className={`w-3 h-3 rounded-full ${intersection.ewSignal === 'yellow' ? 'bg-saffron shadow-[0_0_8px_rgba(255,153,51,0.5)]' : 'bg-gray-300'}`} />
                  <div className={`w-3 h-3 rounded-full ${intersection.ewSignal === 'green' ? 'bg-green shadow-[0_0_8px_rgba(19,136,8,0.5)]' : 'bg-gray-300'}`} />
                </div>
                <span className="text-[11px] font-black text-navy uppercase">{intersection.ewSignal}</span>
             </div>
             <div className="mt-3">
                <div className="flex justify-between text-[9px] font-bold text-navy/40 mb-1">
                  <span>PROGRESS</span>
                  <span>{Math.max(0, 100 - intersection.phaseProgress)}%</span>
                </div>
                <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-500 opacity-60 ${signalToBg(intersection.ewSignal)}`}
                    style={{ width: `${Math.max(0, 100 - intersection.phaseProgress)}%` }}
                  />
                </div>
             </div>
          </GovCard>
        </div>

        {/* Real-time Loading Metrics */}
        <GovCard title="SECTOR METRICS" className="p-0">
          <div className="divide-y divide-gray-100">
            <div className="p-3 flex justify-between items-center bg-gray-50/30">
              <span className="text-[10px] font-bold text-navy/60 uppercase">Queue Length (N-S)</span>
              <span className="text-xs font-black text-navy">{intersection.nsQueueLength} Veh</span>
            </div>
            <div className="p-3 flex justify-between items-center">
              <span className="text-[10px] font-bold text-navy/60 uppercase">Queue Length (E-W)</span>
              <span className="text-xs font-black text-navy">{intersection.ewQueueLength} Veh</span>
            </div>
            <div className="p-3 flex justify-between items-center bg-gray-50/30">
              <span className="text-[10px] font-bold text-navy/60 uppercase">Cycle Occupancy</span>
              <span className="text-xs font-black text-navy">{Math.round((intersection.nsDensity + intersection.ewDensity) / 2)}%</span>
            </div>
          </div>
        </GovCard>

        {/* Lane Density Detail */}
        <div className="space-y-3">
          <p className="text-[10px] font-black text-navy/40 uppercase tracking-widest pl-1">Official Load Factor</p>
          <div className="grid grid-cols-2 gap-3">
             <div className="bg-white p-3 rounded border border-[#d1d9e2]">
                <div className="flex justify-between mb-2">
                   <span className="text-[9px] font-bold text-navy/50 uppercase">N-S Lane</span>
                   <span className="text-[10px] font-black text-navy">{Math.round(intersection.nsDensity)}%</span>
                </div>
                <div className="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
                   <div className="bg-navy h-full transition-all" style={{ width: `${intersection.nsDensity}%` }} />
                </div>
             </div>
             <div className="bg-white p-3 rounded border border-[#d1d9e2]">
                <div className="flex justify-between mb-2">
                   <span className="text-[9px] font-bold text-navy/50 uppercase">E-W Lane</span>
                   <span className="text-[10px] font-black text-navy">{Math.round(intersection.ewDensity)}%</span>
                </div>
                <div className="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
                   <div className="bg-navy h-full transition-all" style={{ width: `${intersection.ewDensity}%` }} />
                </div>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}
