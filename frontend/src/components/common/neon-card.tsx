import React from 'react';

interface NeonCardProps {
  children: React.ReactNode;
  className?: string;
  glowColor?: 'cyan' | 'green' | 'red' | 'amber' | 'purple' | 'navy' | 'saffron';
  animated?: boolean;
}

/**
 * @deprecated Use GovCard for the new professional government aesthetic.
 * This component is maintained for compatibility but styled as a clean Gov card.
 */
export function NeonCard({
  children,
  className = '',
  glowColor = 'navy',
  animated = false,
}: NeonCardProps) {
  const accentMap = {
    cyan: 'border-t-navy',
    green: 'border-t-green',
    red: 'border-t-red-600',
    amber: 'border-t-saffron',
    purple: 'border-t-navy',
    navy: 'border-t-navy',
    saffron: 'border-t-saffron',
  };

  const borderAccent = accentMap[glowColor] || accentMap.navy;
  const animationClass = animated ? 'animate-pulse' : '';

  return (
    <div
      className={`
        bg-white rounded border border-[#d1d9e2] border-t-4 shadow-sm transition-all
        ${borderAccent}
        ${animationClass}
        ${className}
      `}
    >
      {children}
    </div>
  );
}
