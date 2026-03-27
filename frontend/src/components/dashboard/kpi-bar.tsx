'use client';

import React from 'react';
import { useTrafficStore } from '@/lib/store';
import { GovCard } from '@/components/common/gov-card';
import { AnimatedCounter } from '@/components/common/animated-counter';

export function KPIBar() {
  const { totalVehicles, nextRecalcSeconds, activeIntersections, networkAvgWait } = useTrafficStore();

  const kpis = [
    {
      label: 'TOTAL VEHICLES',
      value: totalVehicles,
      unit: 'DETECTED today',
      accent: 'saffron' as const,
      format: (v: number) => Math.round(v).toLocaleString('en-IN'),
    },
    {
      label: 'NETWORK AVG WAIT',
      value: networkAvgWait,
      unit: 'SECONDS live',
      accent: 'white' as const,
      format: (v: number) => `${Math.round(v)}s`,
    },
    {
      label: 'NEXT RECALCULATION',
      value: nextRecalcSeconds,
      unit: 'SECONDS remaining',
      accent: 'navy' as const,
      format: (v: number) => `${Math.round(v)}s`,
    },
    {
      label: 'ACTIVE SECTORS',
      value: activeIntersections,
      unit: 'OPERATIONAL nodes',
      accent: 'navy' as const,
      format: (v: number) => v.toString(),
    },
    {
      label: 'GOI CARBON CREDIT',
      value: (totalVehicles * 0.38) / 1000,
      unit: 'METRIC TONS saved',
      accent: 'green' as const,
      format: (v: number) => Math.round(v).toLocaleString('en-IN'),
    },
  ];

  return (
    <div className="grid w-full grid-cols-1 gap-4 sm:grid-cols-2 2xl:grid-cols-5">
      {kpis.map((kpi, idx) => (
        <GovCard
          key={idx}
          accent={kpi.accent}
          className="p-3"
        >
          <p className="text-[10px] font-black text-navy/40 uppercase tracking-widest">{kpi.label}</p>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-xl font-bold text-navy font-mono">
              <AnimatedCounter value={kpi.value} format={kpi.format} />
            </span>
            <span className="text-[9px] font-bold text-navy/40 uppercase tracking-tighter">{kpi.unit}</span>
          </div>
        </GovCard>
      ))}
    </div>
  );
}
