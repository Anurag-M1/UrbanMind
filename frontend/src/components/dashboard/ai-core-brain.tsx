'use client';

import React, { useMemo } from 'react';
import { useTrafficStore } from '@/lib/store';
import { AnimatedCounter } from '@/components/common/animated-counter';
import { buildAiRecommendations } from '@/lib/traffic-metrics';

export function AICoreBrain() {
  const { systemLoad, decisionLatency, optimizationEfficiency, intersections } = useTrafficStore();
  const recommendations = useMemo(() => buildAiRecommendations(intersections), [intersections]);

  return (
    <div className="flex h-full min-h-0 w-full flex-col overflow-y-auto p-4 pr-3">
      {/* Official Status Indicator */}
      <div className="mb-4 flex shrink-0 items-center justify-between rounded border border-[#d1d9e2] bg-[#f8f9fa] p-2">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green animate-pulse" />
          <span className="text-[10px] font-bold text-navy uppercase tracking-widest">Neural Core Status: NOMINAL</span>
        </div>
        <span className="text-[9px] font-mono text-navy/40">VER: 4.2.0-NCR</span>
      </div>

      {/* Professional Data Visualization (Abstract Connectivity) */}
      <div className="flex min-h-[150px] flex-[1_1_auto] flex-col items-center justify-center py-2">
        <div className="relative flex h-36 w-36 items-center justify-center xl:h-40 xl:w-40">
          {/* Static Concentric Rings */}
          <div className="absolute inset-0 border border-navy/5 rounded-full" />
          <div className="absolute inset-4 border border-navy/10 rounded-full" />
          <div className="absolute inset-10 border border-navy/20 rounded-full" />
          
          {/* Saffron/Green Pulsing Accents */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-2 h-2 bg-saffron rounded-full shadow-sm" />
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-2 h-2 bg-green rounded-full shadow-sm" />
          
          {/* Core Shield Icon (SVG) */}
          <div className="z-10 bg-white p-4 rounded-full shadow-lg border border-[#d1d9e2]">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-navy" viewBox="0 0 20 20" fill="currentColor">
               <path fillRule="evenodd" d="M2.166 4.9L10 1.55l7.834 3.35a1 1 0 01.666.927v4.265c0 4.456-3.584 8.092-8.154 8.548a1 1 0 01-.692 0C5.084 17.084 1.5 13.448 1.5 8.992V5.827a1 1 0 01.666-.927zM10 14.255a1 1 0 100-2 1 1 0 000 2zM10 11a1 1 0 00-1-1V7a1 1 0 112 0v3a1 1 0 00-1 1z" clipRule="evenodd" />
            </svg>
          </div>

          {/* Data Pulse Rings */}
          <div className="absolute inset-0 border-2 border-navy/5 rounded-full animate-ping opacity-20" />
        </div>
      </div>

      {/* Core Metrics Grid */}
      <div className="mb-4 shrink-0 grid grid-cols-1 gap-3 sm:grid-cols-3">
        {[
          { label: 'EFFICIENCY', val: Math.round(optimizationEfficiency), unit: '%', color: 'text-green' },
          { label: 'CALC LOAD', val: systemLoad, unit: '%', color: 'text-navy' },
          { label: 'LATENCY', val: decisionLatency, unit: 'ms', color: 'text-saffron' }
        ].map(m => (
          <div key={m.label} className="text-center p-2 rounded bg-[#f8f9fa] border border-[#d1d9e2]">
            <p className="text-[8px] font-black text-navy/40 uppercase tracking-tighter mb-1">{m.label}</p>
            <p className={`text-sm font-black font-mono ${m.color}`}>
              <AnimatedCounter value={m.val} format={(v) => `${Math.round(v)}${m.unit}`} />
            </p>
          </div>
        ))}
      </div>

      {/* Tactical Logic Recommendations */}
      <div className="mt-auto flex min-h-0 flex-1 shrink-0 flex-col border-t border-[#d1d9e2] pt-4">
        <h4 className="text-[9px] font-black text-navy/40 uppercase tracking-[0.2em] mb-3 flex items-center justify-between">
          AI RECOMMENDATIONS
          <span className="text-[8px] text-green animate-pulse">● LIVE TRANSCRIPT</span>
        </h4>
        <div className="space-y-2">
          {recommendations.map((rec, idx) => (
            <div key={idx} className="flex items-start gap-2 bg-[#f8f9fa] p-2 rounded border-l-2 border-navy/20 hover:border-navy/50 transition-colors">
              <span className="text-[10px] text-navy font-bold">{idx + 1}.</span>
              <span className="text-[10px] text-navy/80 font-medium leading-tight">{rec.replace(/^\d+\.\s*/, '')}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
