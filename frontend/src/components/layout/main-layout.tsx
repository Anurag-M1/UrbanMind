import React from 'react';
import { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { TopBar } from './top-bar';
import { Sidebar } from './sidebar';
import { EmergencyOverlay } from '@/components/emergency/emergency-overlay';
import { CorridorAnimation } from '@/components/emergency/corridor-animation';

interface MainLayoutProps {
  children: React.ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  return (
    <div className="h-screen flex flex-col bg-background overflow-hidden relative">
      {/* Indian Flag Top Strips */}
      <div className="flex w-full h-1.5 shrink-0">
        <div className="flex-1 bg-saffron" />
        <div className="flex-1 bg-white" />
        <div className="flex-1 bg-green" />
      </div>

      <EmergencyOverlay />
      <CorridorAnimation />
      <TopBar onMenuToggle={() => setSidebarOpen((open) => !open)} />
      <div className="flex min-h-0 flex-1 overflow-hidden">
        <Sidebar mobileOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        {sidebarOpen && (
          <button
            type="button"
            aria-label="Close navigation"
            className="fixed inset-0 z-30 bg-navy/25 xl:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
        <main className="flex min-h-0 flex-1 overflow-y-auto overflow-x-hidden bg-[#f8f9fa] shadow-inner min-w-0 xl:overflow-hidden">
          <div className="mx-auto flex h-full min-h-0 w-full max-w-[1600px] flex-col">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
