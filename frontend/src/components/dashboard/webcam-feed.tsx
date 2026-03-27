'use client';

import React from 'react';
import { buildCameraEmbedUrl, getCameraNodeById } from '@/lib/camera-nodes';
import { useTrafficStore } from '@/lib/store';

interface WebcamFeedProps {
  nodeId?: string;
  compact?: boolean;
}

export function WebcamFeed({ nodeId, compact = false }: WebcamFeedProps) {
  const selectedCameraNodeId = useTrafficStore((s) => s.selectedCameraNodeId);
  const totalVehicles = useTrafficStore((s) => s.totalVehicles);
  const liveVisionStatus = useTrafficStore((s) => s.liveVisionStatus);
  const lastDetectionCount = useTrafficStore((s) => s.lastDetectionCount);
  const activeNode = getCameraNodeById(nodeId ?? selectedCameraNodeId);
  const [showGT, setShowGT] = React.useState(false);
  const [iframeSrc, setIframeSrc] = React.useState('');

  const buildEmbedUrl = React.useCallback(
    () => buildCameraEmbedUrl(activeNode.videoId, window.location.origin),
    [activeNode.videoId]
  );

  const refreshIframe = React.useCallback(() => {
    setIframeSrc(buildEmbedUrl());
  }, [buildEmbedUrl]);

  // Trigger pulse when a real ground-truth update arrives
  React.useEffect(() => {
    if (liveVisionStatus === 'Synced') {
      setShowGT(true);
      const timer = setTimeout(() => setShowGT(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [liveVisionStatus, lastDetectionCount]);

  React.useEffect(() => {
    refreshIframe();

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        refreshIframe();
      }
    };
    const handleOnline = () => refreshIframe();
    const handleFocus = () => refreshIframe();
    const periodicRearm = window.setInterval(() => {
      refreshIframe();
    }, 25000);

    window.addEventListener('focus', handleFocus);
    window.addEventListener('online', handleOnline);
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      window.clearInterval(periodicRearm);
      window.removeEventListener('focus', handleFocus);
      window.removeEventListener('online', handleOnline);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [refreshIframe]);

  React.useEffect(() => {
    refreshIframe();
  }, [activeNode.id, liveVisionStatus, refreshIframe]);

  if (compact) {
    return (
      <div className="relative h-full w-full overflow-hidden border border-navy/20 bg-black">
        <iframe
          key={iframeSrc}
          src={iframeSrc}
          title={`${activeNode.name} live traffic feed`}
          className="h-full w-full border-0 brightness-[0.92] contrast-[1.08]"
          allow="autoplay; encrypted-media; picture-in-picture"
          loading="eager"
        />
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-black/10" />
        <div className="absolute left-3 right-3 top-3 z-20 flex items-start justify-between text-white">
          <div>
            <p className="text-[9px] font-black uppercase tracking-[0.22em]">{activeNode.name}</p>
            <p className="mt-1 text-[8px] font-mono uppercase tracking-tight text-white/65">{activeNode.cameraId} // {activeNode.location}</p>
          </div>
          <span className="rounded bg-white/10 px-2 py-1 text-[8px] font-black uppercase tracking-[0.18em]">
            {activeNode.status}
          </span>
        </div>
        <div className="absolute bottom-3 left-3 right-3 z-20 flex items-center justify-between text-white">
          <span className="text-[8px] font-black uppercase tracking-[0.18em]">{Math.round(totalVehicles).toLocaleString('en-IN')} veh detected</span>
          <span className="text-[8px] font-mono uppercase tracking-tight text-white/70">{activeNode.latencyMs}ms</span>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full flex flex-col bg-black overflow-hidden relative border border-navy/20">
      {/* Official Security Header Overlay */}
      <div className="absolute top-0 left-0 right-0 z-20 p-4 bg-gradient-to-b from-navy/90 via-navy/40 to-transparent flex justify-between items-start pointer-events-none">
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-red-600 animate-pulse shadow-[0_0_8px_rgba(220,38,38,0.5)]" />
            <span className="text-[10px] font-black text-white uppercase tracking-widest leading-none">
              SECURE FEED // {activeNode.cameraId}
            </span>
          </div>
          <div className="flex items-center gap-2 ml-4">
            <span className={`text-[8px] font-mono uppercase tracking-[0.2em] transition-all duration-300 ${showGT ? 'text-green font-black' : 'text-white/60'}`}>
              {showGT ? '● GROUND_TRUTH_VERIFIED' : liveVisionStatus === 'Projected' ? 'PROJECTION: AI_MODEL_FLOW' : 'YOLO_V8_LIVE_STREAM'}
            </span>
          </div>
        </div>
        
        {/* Detection Metadata */}
        <div className="flex flex-col items-end gap-1">
          <div className={`px-2 py-1 rounded bg-white shadow-lg border-b-2 border-navy transition-all duration-300 ${showGT ? 'scale-105 ring-2 ring-green' : ''}`}>
            <span className="text-[11px] font-black text-navy tabular-nums">
              {Math.round(totalVehicles).toLocaleString('en-IN')}
            </span>
            <span className="text-[8px] font-black text-navy/40 ml-1 uppercase">VEH DETECTED</span>
          </div>
          <div className="flex items-center gap-1.5">
             <span className="text-[7px] font-black text-white/40 uppercase tracking-tighter">
               ENCRYPTION: AES-256
             </span>
             <div className="w-1.5 h-1.5 rounded-full bg-green/50" />
          </div>
        </div>
      </div>

      {/* Frame Container */}
      <div className="flex-1 relative">
        <iframe
          key={iframeSrc}
          src={iframeSrc}
          title={`${activeNode.name} live traffic feed`}
          className="w-full h-full border-0 contrast-[1.1] saturate-[0.8] brightness-[0.9]"
          allow="autoplay; encrypted-media; picture-in-picture"
          loading="eager"
        />

        {/* Pointer events blocker - locks the view */}
        <div className="absolute inset-0 z-10 cursor-default pointer-events-auto bg-transparent" />

        {/* Subtle Scanline / CRT Effect for 'Security Monitor' Feel */}
        <div className="absolute inset-0 pointer-events-none bg-scanlines opacity-[0.02]" />

        {/* Tactical Corner Brackets */}
        <div className="absolute top-6 left-6 w-6 h-6 border-t-2 border-l-2 border-white/30" />
        <div className="absolute top-6 right-6 w-6 h-6 border-t-2 border-r-2 border-white/30" />
        <div className="absolute bottom-6 left-6 w-6 h-6 border-b-2 border-l-2 border-white/30" />
        <div className="absolute bottom-6 right-6 w-6 h-6 border-b-2 border-r-2 border-white/30" />

        {/* Official Metadata Label */}
        <div className="absolute bottom-6 left-8 flex items-center gap-2 pointer-events-none">
          <div className="flex flex-col">
            <span className="text-[9px] font-black text-white uppercase tracking-widest drop-shadow-md">
              {activeNode.name} // UrbanMind Vision
            </span>
            <span className="text-[7px] font-mono text-white/50 uppercase tracking-tighter">
              CAMERA_ID: {activeNode.cameraId} // LATENCY: {activeNode.latencyMs}ms // {activeNode.sector}
            </span>
          </div>
        </div>

      </div>

      {/* Flag Accent Strip at bottom of feed */}
      <div className="absolute bottom-0 left-0 right-0 h-1 flex z-20">
        <div className="flex-1 bg-saffron/40" />
        <div className="flex-1 bg-white/40" />
        <div className="flex-1 bg-green/40" />
      </div>
    </div>
  );
}
