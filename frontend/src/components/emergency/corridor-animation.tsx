'use client';

import React, { useState, useEffect } from 'react';
import { useTrafficStore } from '@/lib/store';

export function CorridorAnimation() {
  const { emergencyMode, intersections } = useTrafficStore();
  const [activeIntersections, setActiveIntersections] = useState<string[]>([]);

  useEffect(() => {
    if (!emergencyMode) {
      setActiveIntersections([]);
      return;
    }

    // Simulate sequential signal activation along a route
    const route = intersections.slice(0, 5); // Use first 5 intersections as route
    let currentIdx = 0;

    const interval = setInterval(() => {
      setActiveIntersections(route.slice(0, currentIdx + 1).map((i) => i.id));
      currentIdx = (currentIdx + 1) % route.length;
    }, 800);

    return () => clearInterval(interval);
  }, [emergencyMode, intersections]);

  if (!emergencyMode) return null;

  return (
    <div className="fixed inset-0 pointer-events-none z-30">
      {intersections.map((intersection, idx) => {
        const isActive = activeIntersections.includes(intersection.id);
        const gridSize = 5;
        const parts = intersection.id.split('-');
        const i = parts.length > 1 ? parseInt(parts[1]) : 0;
        const j = parts.length > 2 ? parseInt(parts[2]) : 0;

        // Map to approximate screen position
        const x = (j / gridSize) * (typeof window !== 'undefined' ? window.innerWidth : 1200) * 0.7 + (typeof window !== 'undefined' ? window.innerWidth : 1200) * 0.2;
        const y = (i / gridSize) * (typeof window !== 'undefined' ? window.innerHeight : 800) * 0.6 + (typeof window !== 'undefined' ? window.innerHeight : 800) * 0.15;

        if (!isActive) return null;

        return (
          <div
            key={intersection.id}
            className="absolute w-12 h-12 pointer-events-none"
            style={{
              left: `${x}px`,
              top: `${y}px`,
              transform: 'translate(-50%, -50%)',
            }}
          >
            {/* Professional Ring Pulse */}
            <div className="absolute inset-0 rounded-full border-4 border-red-600/50 animate-ping" />
            
            {/* Core Indicator */}
            <div className="absolute inset-2 rounded-full bg-red-600 shadow-[0_0_15px_rgba(220,38,38,0.8)] flex items-center justify-center">
               <span className="text-white text-[8px] font-black">SEC</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
