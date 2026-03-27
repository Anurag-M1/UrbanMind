'use client';

import React from 'react';
import { useTrafficStore } from '@/lib/store';

export function EventTimeline() {
  const { events } = useTrafficStore();

  const getEventBadgeClass = (type: string) => {
    switch (type) {
      case 'alert':
      case 'emergency':
        return 'bg-red-600 text-white';
      case 'warning':
        return 'bg-saffron text-white';
      case 'info':
        return 'bg-navy text-white';
      case 'success':
        return 'bg-green text-white';
      default:
        return 'bg-gray-500 text-white';
    }
  };

  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true });
  };

  return (
    <div className="flex h-full min-h-0 w-full flex-col overflow-hidden">
      <div className="min-h-0 flex-1 overflow-y-auto">
        {events.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-6 grayscale opacity-40">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-[10px] font-bold uppercase tracking-widest">No Administrative<br />Events Logged</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {events.map((event) => (
              <div 
                key={event.id} 
                className="p-4 hover:bg-gray-50 transition-colors border-l-4 border-transparent hover:border-l-navy group"
              >
                <div className="flex justify-between items-start mb-1.5">
                  <div className={`px-1.5 py-0.5 rounded text-[8px] font-black uppercase tracking-tighter ${getEventBadgeClass(event.type)}`}>
                    {event.type}
                  </div>
                  <span className="text-[10px] font-mono text-navy/30 group-hover:text-navy/50 transition-colors">
                    {formatTime(event.timestamp)}
                  </span>
                </div>
                
                <h4 className="text-[11px] font-black text-navy uppercase leading-tight mb-1">
                  {event.title}
                </h4>
                <p className="text-[10px] text-navy/60 leading-relaxed line-clamp-2">
                  {event.description}
                </p>

                {event.type === 'emergency' && (
                  <div className="mt-2 flex items-center gap-2">
                    <div className="w-full h-1 bg-red-100 rounded-full overflow-hidden">
                      <div className="h-full bg-red-600 animate-pulse w-full" />
                    </div>
                    <span className="text-[8px] font-black text-red-600 uppercase whitespace-nowrap">Priority Response</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Official Log Footer */}
      <div className="border-t border-[#d1d9e2] bg-[#f8f9fa] p-3 text-center">
        <p className="text-[9px] font-bold text-navy/30 uppercase tracking-[0.2em]">Live Administrative Transcript</p>
      </div>
    </div>
  );
}
