'use client';

import React, { useState, useEffect } from 'react';
import { Menu } from 'lucide-react';
import { useTrafficStore } from '@/lib/store';

interface TopBarProps {
  onMenuToggle?: () => void;
}

export function TopBar({ onMenuToggle }: TopBarProps) {
  const { systemStatus, decisionLatency, activeEmergencies } = useTrafficStore();
  const [currentTime, setCurrentTime] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      setCurrentTime(new Date().toLocaleTimeString('en-IN', { 
        timeZone: 'Asia/Kolkata',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
      }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const statusColor = systemStatus === 'connected' ? '#10b981' : systemStatus === 'syncing' ? '#fbbf24' : '#ef4444';

  return (
    <header className="relative z-10 w-full border-b border-navy/20 bg-navy px-3 py-2 shadow-md sm:px-4 lg:px-6">
      <div className="flex items-center justify-between gap-3">
        {/* Left: Official Branding */}
        <div className="flex min-w-0 items-center gap-3">
          <button
            type="button"
            onClick={onMenuToggle}
            className="rounded border border-white/15 bg-white/5 p-2 text-white xl:hidden"
            aria-label="Toggle navigation"
          >
            <Menu size={18} />
          </button>
          <div className="bg-white p-1 rounded-sm shadow-sm ring-1 ring-black/5">
            <img src="/logo.png" alt="UrbanMind Logo" className="h-8 w-auto object-contain sm:h-10" />
          </div>
          <div className="min-w-0 border-l border-white/20 py-1 pl-3 text-white sm:pl-4">
            <h1 className="truncate text-lg font-black leading-none tracking-tight uppercase sm:text-xl">
              UrbanMind
            </h1>
            <p className="mt-1 hidden truncate text-[10px] font-medium uppercase tracking-wider text-white/70 lg:block">
              Ministry of Traffic • Government of India
            </p>
          </div>
        </div>

        {/* Center: Live Data Metrics */}
        <div className="hidden items-center gap-4 rounded-full border border-white/10 bg-white/5 px-4 py-2 xl:flex lg:gap-6 lg:px-6">
          <div className="flex flex-col items-center">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: statusColor }} />
              <span className="text-[10px] text-white/50 uppercase font-bold tracking-widest">System Status</span>
            </div>
            <span className="text-xs font-mono text-white capitalize">{systemStatus}</span>
          </div>
          
          <div className="w-px h-6 bg-white/10" />
          
          <div className="flex flex-col items-center">
            <span className="text-[10px] text-white/50 uppercase font-bold tracking-widest">Latency</span>
            <span className="text-xs font-mono text-white">{decisionLatency}ms</span>
          </div>

          <div className="w-px h-6 bg-white/10" />

          <div className="flex flex-col items-center">
            <span className="text-[10px] text-white/50 uppercase font-bold tracking-widest">Emergencies</span>
            <span className="text-xs font-mono text-white">{activeEmergencies}</span>
          </div>

          <div className="w-px h-6 bg-white/10" />

          <div className="flex flex-col items-center">
            <span className="text-[10px] text-white/50 uppercase font-bold tracking-widest">IST Time</span>
            <span className="text-xs font-mono text-white">{currentTime}</span>
          </div>
        </div>

        {/* Right: Security Badge */}
        <div className="flex items-center gap-2 sm:gap-3">
          <div className="mr-3 hidden text-right xl:block">
            <p className="text-[9px] text-white/40 uppercase font-bold">Encrypted Session</p>
            <p className="text-[10px] text-[#10b981] font-bold">SECURE CHANNEL</p>
          </div>
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/10 border border-white/20 text-white shadow-inner">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M2.166 4.9L10 1.55l7.834 3.35a1 1 0 01.666.927v4.265c0 4.456-3.584 8.092-8.154 8.548a1 1 0 01-.692 0C5.084 17.084 1.5 13.448 1.5 8.992V5.827a1 1 0 01.666-.927zM10 14.255a1 1 0 100-2 1 1 0 000 2zM10 11a1 1 0 00-1-1V7a1 1 0 112 0v3a1 1 0 00-1 1z" clipRule="evenodd" />
            </svg>
          </div>
        </div>
      </div>

      <div className="mt-2 flex flex-wrap items-center justify-between gap-2 rounded border border-white/10 bg-white/5 px-3 py-2 text-white xl:hidden">
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full animate-pulse" style={{ backgroundColor: statusColor }} />
          <span className="text-[10px] font-bold uppercase tracking-widest">{systemStatus}</span>
        </div>
        <span className="text-[10px] font-mono">{decisionLatency}ms</span>
        <span className="text-[10px] font-mono">{currentTime}</span>
      </div>
    </header>
  );
}
