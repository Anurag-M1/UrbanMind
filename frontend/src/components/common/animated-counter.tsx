'use client';

import React, { useState, useEffect } from 'react';

interface AnimatedCounterProps {
  value: number;
  duration?: number;
  format?: (value: number) => string;
  className?: string;
}

export function AnimatedCounter({
  value,
  duration = 1000,
  format,
  className = '',
}: AnimatedCounterProps) {
  const [displayValue, setDisplayValue] = useState(value);

  const defaultFormat = (v: number) => {
    return Math.round(v).toLocaleString('en-IN');
  };

  const finalFormat = format || defaultFormat;

  useEffect(() => {
    let startValue = displayValue;
    const startTime = Date.now();
    const difference = value - startValue;

    const updateValue = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // Easing function (out-cubic)
      const easeProgress = 1 - Math.pow(1 - progress, 3);
      
      const newValue = startValue + difference * easeProgress;
      setDisplayValue(newValue);

      if (progress < 1) {
        requestAnimationFrame(updateValue);
      }
    };

    if (difference !== 0) {
      requestAnimationFrame(updateValue);
    }
  }, [value, duration]);

  return <span className={className}>{finalFormat(Math.round(displayValue))}</span>;
}
