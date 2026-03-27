'use client';

import React from 'react';
import { useTrafficStore } from '@/lib/store';
import { GlowBadge } from '@/components/common/glow-badge';

export function EmergencyOverlay() {
  const { emergencyMode } = useTrafficStore();

  if (!emergencyMode) return null;

  return (
    <div
      className="fixed inset-0 pointer-events-none z-40"
      style={{
        backgroundColor: 'rgba(220, 38, 38, 0.1)',
        animation: 'emergency-pulse 1.5s infinite',
      }}
    >
      {/* Corner indicators */}
      <div className="absolute top-6 right-8">
        <div className="flex items-center gap-3 bg-red-600 text-white px-4 py-2 rounded shadow-2xl border-2 border-white/20">
           <div className="w-2 h-2 rounded-full bg-white animate-ping" />
           <span className="text-[10px] font-black uppercase tracking-[0.2em]">Priority Protocol: Emergency Corridor Active</span>
        </div>
      </div>

      {/* Official Red Border */}
      <div
        className="absolute inset-0 border-[8px] border-red-600/30 pointer-events-none"
        style={{
          boxShadow: 'inset 0 0 100px rgba(220, 38, 38, 0.2)',
        }}
      />

      {/* High-speed scan line for tactical feel */}
      <div className="absolute inset-0 overflow-hidden opacity-20">
        <div
          className="w-full h-[2px] bg-red-600"
          style={{
            animation: 'scan-line 2s linear infinite',
          }}
        />
      </div>
    </div>
  );
}
