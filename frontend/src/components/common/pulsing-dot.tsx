import React from 'react';

interface PulsingDotProps {
  color?: 'navy' | 'green' | 'red' | 'saffron' | 'white';
  size?: 'sm' | 'md' | 'lg';
  animated?: boolean;
  className?: string;
}

export function PulsingDot({
  color = 'navy',
  size = 'md',
  animated = true,
  className = '',
}: PulsingDotProps) {
  const colorMap = {
    navy: 'bg-navy shadow-[0_0_8px_rgba(0,0,128,0.4)]',
    green: 'bg-green shadow-[0_0_8px_rgba(19,136,8,0.4)]',
    red: 'bg-red-600 shadow-[0_0_8px_rgba(220,38,38,0.4)]',
    saffron: 'bg-saffron shadow-[0_0_8px_rgba(255,153,51,0.4)]',
    white: 'bg-white shadow-[0_0_8px_rgba(255,255,255,0.4)]',
  };

  const sizeClasses = {
    sm: 'w-1.5 h-1.5',
    md: 'w-2.5 h-2.5',
    lg: 'w-3.5 h-3.5',
  };

  const animationClass = animated ? 'animate-pulse' : '';

  return (
    <div
      className={`
        rounded-full
        ${sizeClasses[size]}
        ${colorMap[color] || colorMap.navy}
        ${animationClass}
        ${className}
      `}
    />
  );
}
