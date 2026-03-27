import React from 'react';

interface GlowBadgeProps {
  text: string;
  color?: 'navy' | 'green' | 'red' | 'saffron' | 'gray';
  size?: 'sm' | 'md' | 'lg';
  animated?: boolean;
  className?: string;
}

export function GlowBadge({
  text,
  color = 'navy',
  size = 'md',
  animated = false,
  className = '',
}: GlowBadgeProps) {
  const colorMap = {
    navy: { text: 'text-navy', bg: 'bg-navy/5', border: 'border-navy/20' },
    green: { text: 'text-green', bg: 'bg-green/5', border: 'border-green/20' },
    red: { text: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200' },
    saffron: { text: 'text-saffron', bg: 'bg-saffron/5', border: 'border-saffron/20' },
    gray: { text: 'text-gray-600', bg: 'bg-gray-50', border: 'border-gray-200' },
  };

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-[9px]',
    md: 'px-3 py-1 text-[10px]',
    lg: 'px-4 py-1.5 text-xs',
  };

  const { text: textColor, bg, border } = colorMap[color] || colorMap.navy;
  const animationClass = animated ? 'animate-pulse' : '';

  return (
    <span
      className={`
        inline-block rounded border font-black uppercase tracking-widest transition-all
        ${sizeClasses[size]}
        ${textColor}
        ${bg}
        ${border}
        ${animationClass}
        ${className}
      `}
    >
      {text}
    </span>
  );
}
