'use client';

import React from 'react';
import { Link } from 'react-router-dom';
import { X } from 'lucide-react';
import { CAMERA_NODES } from '@/lib/camera-nodes';
import { useTrafficStore, type CurrentPage } from '@/lib/store';
import { cn } from '@/lib/utils';

interface NavItem {
  name: string;
  href: string;
  page: CurrentPage;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  {
    name: 'Sector Dashboard',
    href: '/overview',
    page: 'dashboard',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
        <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
      </svg>
    ),
  },
  {
    name: 'All Footages',
    href: '/footages',
    page: 'footages',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
        <path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zM14.553 7.106A1 1 0 0014 8v4a1 1 0 00.553.894l2 1A1 1 0 0018 13V7a1 1 0 00-1.447-.894l-2 1z" />
      </svg>
    ),
  },
  {
    name: 'Traffic Analytics',
    href: '/analytics',
    page: 'analytics',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
        <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
      </svg>
    ),
  },
  {
    name: 'Emergency Ops',
    href: '/emergency',
    page: 'emergency',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.381z" clipRule="evenodd" />
      </svg>
    ),
  },
  {
    name: 'Economic ROI',
    href: '/roi',
    page: 'roi',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
        <path d="M2 10a8 8 0 018-8v8h8a8 8 0 11-16 0z" />
        <path d="M12 2.252A8.014 8.014 0 0117.748 8H12V2.252z" />
      </svg>
    ),
  },
  {
    name: 'Manual Vision',
    href: '/video',
    page: 'video',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
        <path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zM14.553 7.106A1 1 0 0014 8v4a1 1 0 00.553.894l2 1A1 1 0 0018 13V7a1 1 0 00-1.447-.894l-2 1z" />
      </svg>
    ),
  },
  {
    name: 'Digital Twin',
    href: '/digital-twin',
    page: 'digital-twin',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
        <path d="M11 3a1 1 0 10-2 0v1a1 1 0 102 0V3zM15.657 5.757a1 1 0 00-1.414-1.414l-.707.707a1 1 0 001.414 1.414l.707-.707zM18 10a1 1 0 01-1 1h-1a1 1 0 110-2h1a1 1 0 011 1zM5.05 6.464A1 1 0 106.464 5.05l-.707-.707a1 1 0 00-1.414 1.414l.707.707zM5 10a1 1 0 11-2 0 1 1 0 012 0zM8 16v-1a1 1 0 10-2 0v1a1 1 0 102 0zM13.414 14.121a1 1 0 00-1.414 1.414l.707.707a1 1 0 001.414-1.414l-.707-.707z" />
      </svg>
    ),
  },
  {
    name: 'Settings',
    href: '/settings',
    page: 'settings',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
      </svg>
    ),
  },
];

interface SidebarProps {
  mobileOpen?: boolean;
  onClose?: () => void;
}

export function Sidebar({ mobileOpen = false, onClose }: SidebarProps) {
  const {
    currentPage,
    setCurrentPage,
    selectedCameraNodeId,
    setSelectedCameraNodeId,
    optimizationEfficiency,
    systemStatus,
    liveVisionStatus,
    lastDetectionCount,
    uptimeSeconds,
  } = useTrafficStore();
  const baseAiConfidence = Math.max(
    80,
    Math.min(
      90,
      optimizationEfficiency +
        (systemStatus === 'connected' ? 1 : systemStatus === 'syncing' ? 0 : -2) +
        (liveVisionStatus === 'Synced' ? 1 : liveVisionStatus === 'Projected' ? 0 : -1)
    )
  );
  const [aiConfidence, setAiConfidence] = React.useState(baseAiConfidence);

  React.useEffect(() => {
    const updateConfidence = () => {
      const fluctuationSeed = Math.floor(Date.now() / 2800) + lastDetectionCount + Math.floor(uptimeSeconds / 30);
      const fluctuation = (fluctuationSeed % 5) - 2;
      const nextConfidence = Math.max(80, Math.min(90, baseAiConfidence + fluctuation));
      setAiConfidence(nextConfidence);
    };

    updateConfidence();
    const interval = window.setInterval(updateConfidence, 2800);
    return () => window.clearInterval(interval);
  }, [baseAiConfidence, lastDetectionCount, uptimeSeconds]);

  return (
    <aside
      className={cn(
        'fixed inset-y-0 left-0 z-40 flex h-full w-[86vw] max-w-72 flex-col border-r border-[#d1d9e2] bg-white shadow-[2px_0_10px_rgba(0,0,0,0.02)] transition-transform duration-300 xl:static xl:z-10 xl:w-64',
        mobileOpen ? 'translate-x-0' : '-translate-x-full xl:translate-x-0'
      )}
    >
      {/* Navigation Title */}
      <div className="flex items-center justify-between border-b border-[#f0f2f5] px-6 py-6">
        <h3 className="text-[10px] font-black text-navy/40 uppercase tracking-[0.2em]">Administrative Portal</h3>
        <button
          type="button"
          className="rounded border border-[#d1d9e2] p-1 text-navy xl:hidden"
          onClick={onClose}
        >
          <X size={16} />
        </button>
      </div>

      {/* Navigation */}
      <div className="flex-1 overflow-y-auto px-3 py-4">
        <nav className="space-y-1">
          {navItems.map((item) => (
            <Link key={item.page} to={item.href}>
              <button
                onClick={() => {
                  setCurrentPage(item.page);
                  onClose?.();
                }}
                className={`
                  w-full flex items-center gap-3 px-4 py-2.5 rounded transition-all duration-200 group
                  ${
                    currentPage === item.page
                      ? 'bg-navy/5 text-navy border-l-4 border-l-navy shadow-sm font-bold'
                      : 'text-navy/60 hover:text-navy hover:bg-gray-50 border-l-4 border-l-transparent'
                  }
                `}
              >
                <span className={`transition-colors ${currentPage === item.page ? 'text-navy' : 'text-navy/40 group-hover:text-navy/70'}`}>
                  {item.icon}
                </span>
                <span className="truncate text-[13px] tracking-tight">{item.name}</span>
                {currentPage === item.page && (
                  <div className="ml-auto flex gap-0.5">
                    <div className="w-1 h-3 bg-saffron rounded-full" />
                    <div className="w-1 h-3 bg-white border border-gray-100 rounded-full" />
                    <div className="w-1 h-3 bg-green rounded-full" />
                  </div>
                )}
              </button>
            </Link>
          ))}
        </nav>

        <div className="mt-5 rounded border border-[#d1d9e2] bg-[#f8f9fa] p-3">
          <div className="mb-3 flex items-center justify-between">
            <div>
              <p className="text-[9px] font-black uppercase tracking-[0.25em] text-navy/40">Available Nodes</p>
              <p className="mt-1 text-[10px] font-bold uppercase tracking-wider text-navy/70">{CAMERA_NODES.length} live footage points</p>
            </div>
            <span className="rounded bg-green/10 px-2 py-1 text-[8px] font-black uppercase tracking-[0.2em] text-green">
              {liveVisionStatus || 'SYNCING'}
            </span>
          </div>

          <div className="max-h-[38vh] space-y-2 overflow-y-auto pr-1">
            {CAMERA_NODES.map((node) => {
              const isActiveNode = node.id === selectedCameraNodeId;

              return (
                <button
                  key={node.id}
                  type="button"
                  onClick={() => {
                    setSelectedCameraNodeId(node.id);
                    onClose?.();
                  }}
                  className={cn(
                    'w-full rounded border px-3 py-2 text-left transition-colors',
                    isActiveNode
                      ? 'border-navy bg-white shadow-sm'
                      : 'border-[#d1d9e2] bg-white/70 hover:border-navy/30 hover:bg-white'
                  )}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="truncate text-[10px] font-black uppercase tracking-wide text-navy">{node.name}</p>
                      <p className="mt-1 truncate text-[9px] font-mono uppercase tracking-tight text-navy/45">{node.cameraId} // {node.location}</p>
                    </div>
                    <span className={cn(
                      'rounded px-1.5 py-0.5 text-[8px] font-black uppercase tracking-[0.18em]',
                      node.status === 'LIVE'
                        ? 'bg-green/10 text-green'
                        : node.status === 'PRIORITY'
                          ? 'bg-saffron/15 text-saffron'
                          : 'bg-navy/10 text-navy'
                    )}>
                      {isActiveNode ? 'ACTIVE' : node.status}
                    </span>
                  </div>
                  <div className="mt-2 flex items-center justify-between gap-3 text-[9px] font-bold uppercase tracking-wide text-navy/35">
                    <span className="truncate">{node.sector}</span>
                    <span>{node.latencyMs}ms</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Footer / System Status */}
      <div className="p-4 bg-[#f8f9fa] border-t border-[#d1d9e2]">
        <div className="p-3 bg-white rounded border border-[#d1d9e2] shadow-sm space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-[9px] font-bold text-navy/40 uppercase tracking-wider">AI Confidence</span>
            <span className="text-[11px] font-black text-green">{aiConfidence}%</span>
          </div>
          <div className="w-full bg-[#f0f2f5] h-1 rounded-full overflow-hidden">
            <div className="bg-green h-full transition-all duration-500" style={{ width: `${aiConfidence}%` }} />
          </div>
          <div className="flex justify-between items-center text-[9px] font-bold text-navy/30 uppercase">
            <span>Uptime: {Math.floor(uptimeSeconds / 3600)}h</span>
            <span className="text-[#10b981]">● ACTIVE</span>
          </div>
        </div>
        
        <div className="mt-4 px-1">
          <p className="text-[9px] text-navy/30 font-medium leading-relaxed">
            GOI-UM-INFRA-SYS-01<br />
            Secure Government Intranet
          </p>
        </div>
      </div>
    </aside>
  );
}
