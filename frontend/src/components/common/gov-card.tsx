import React from 'react';

interface GovCardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  accent?: 'saffron' | 'white' | 'green' | 'navy';
}

export function GovCard({ children, className = '', title, accent }: GovCardProps) {
  const accentColors = {
    saffron: 'border-l-saffron',
    white: 'border-l-gray-200',
    green: 'border-l-green',
    navy: 'border-l-navy',
  };

  const accentClass = accent ? `border-l-4 ${accentColors[accent]}` : '';

  return (
    <div className={`bg-white border border-[#d1d9e2] rounded shadow-sm overflow-hidden flex flex-col ${accentClass} ${className}`}>
      {title && (
        <div className="px-4 py-2 bg-[#f8f9fa] border-b border-[#d1d9e2]">
          <h4 className="text-[10px] font-black text-navy/60 uppercase tracking-widest">{title}</h4>
        </div>
      )}
      <div className="flex-1">
        {children}
      </div>
    </div>
  );
}
