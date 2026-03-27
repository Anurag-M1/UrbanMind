import React from 'react';
import { KPIBar } from '@/components/dashboard/kpi-bar';
import { AICoreBrain } from '@/components/dashboard/ai-core-brain';
import { IntersectionPanel } from '@/components/dashboard/intersection-panel';
import { EventTimeline } from '@/components/dashboard/event-timeline';
import { WebcamFeed } from '@/components/dashboard/webcam-feed';

export default function Overview() {
  return (
    <div className="flex h-full min-h-0 w-full flex-col overflow-hidden bg-[#f5f7fa] animate-in fade-in duration-500">
      {/* Top KPI Bar */}
      <div className="z-10 shrink-0 flex flex-col gap-4 border-b border-[#d1d9e2] bg-white px-4 py-4 shadow-sm sm:px-6 xl:flex-row xl:items-center xl:justify-between">
        <div className="flex-1 min-w-0">
          <KPIBar />
        </div>
        <div className="hidden border-l border-[#d1d9e2] pl-8 xl:block">
          <div className="flex flex-col">
            <span className="text-[10px] font-black text-navy/40 uppercase tracking-widest">Administrative Context</span>
            <span className="text-sm font-bold text-navy">National Capital Region (NCR)</span>
          </div>
        </div>
      </div>

      {/* Main Dashboard Grid */}
      <div className="grid min-h-0 flex-1 grid-cols-1 gap-6 overflow-y-auto p-4 sm:p-6 lg:grid-cols-2 xl:h-full xl:grid-cols-12 xl:overflow-hidden">
        
        {/* Left Column: AI Brain & Controls (3/12) */}
        <div className="flex min-h-0 flex-col gap-6 lg:col-span-1 xl:col-span-3 xl:grid xl:h-full xl:grid-rows-[minmax(280px,0.95fr)_minmax(320px,1.05fr)] xl:overflow-hidden">
          {/* AI Status Card */}
          <div className="group flex min-h-[300px] min-w-0 flex-col overflow-hidden rounded-lg border border-[#d1d9e2] bg-white shadow-sm transition-colors hover:border-navy/30 xl:min-h-0 xl:h-full">
            <div className="px-4 py-3 bg-[#f8f9fa] border-b border-[#d1d9e2] flex items-center justify-between">
              <h3 className="text-[11px] font-black text-navy uppercase tracking-widest">AI Core Engine</h3>
              <div className="flex gap-1">
                <div className="w-1.5 h-1.5 rounded-full bg-saffron animate-pulse" />
                <div className="w-1.5 h-1.5 rounded-full bg-white border border-gray-200" />
                <div className="w-1.5 h-1.5 rounded-full bg-green" />
              </div>
            </div>
            <div className="relative min-h-0 flex-1 bg-white">
              <AICoreBrain />
            </div>
          </div>

          {/* Interaction Panel */}
          <div className="group flex min-h-[320px] min-w-0 flex-1 flex-col overflow-hidden rounded-lg border border-[#d1d9e2] bg-white shadow-sm transition-colors hover:border-navy/30 xl:min-h-0 xl:h-full">
            <div className="px-4 py-3 bg-[#f8f9fa] border-b border-[#d1d9e2]">
              <h3 className="text-[11px] font-black text-navy uppercase tracking-widest">Sector Deployment</h3>
            </div>
            <div className="flex-1 overflow-auto p-4">
               <IntersectionPanel />
            </div>
          </div>
        </div>

        {/* Center: Live Traffic Webcam (6/12) */}
        <div className="relative flex min-h-[360px] min-w-0 flex-col gap-6 lg:col-span-2 xl:col-span-6 xl:h-full xl:overflow-hidden">
          <div className="group relative flex-1 overflow-hidden rounded-lg border-2 border-navy/20 bg-black shadow-xl xl:min-h-0 xl:h-full">
             {/* Security Frame Corner Accents */}
             <div className="absolute top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-white/20 z-20" />
             <div className="absolute top-0 right-0 w-8 h-8 border-t-2 border-r-2 border-white/20 z-20" />
             <div className="absolute bottom-0 left-0 w-8 h-8 border-b-2 border-l-2 border-white/20 z-20" />
             <div className="absolute bottom-0 right-0 w-8 h-8 border-b-2 border-r-2 border-white/20 z-20" />
             
             <WebcamFeed />
          </div>
        </div>

        {/* Right Column: Events & Analytics (3/12) */}
        <div className="flex min-h-[320px] min-w-0 flex-col gap-6 lg:col-span-1 xl:col-span-3 xl:h-full xl:overflow-hidden">
          <div className="group flex min-h-[320px] flex-1 flex-col overflow-hidden rounded-lg border border-[#d1d9e2] bg-white shadow-sm transition-colors hover:border-navy/30 xl:min-h-0 xl:h-full">
            <div className="px-4 py-3 bg-[#f8f9fa] border-b border-[#d1d9e2]">
              <h3 className="text-[11px] font-black text-navy uppercase tracking-widest">Administrative Log</h3>
            </div>
            <div className="flex-1 overflow-auto p-0 scroll-smooth">
              <EventTimeline />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
