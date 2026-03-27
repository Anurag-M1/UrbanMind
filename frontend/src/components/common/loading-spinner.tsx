import React from 'react';

export function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center">
      <div className="relative w-10 h-10">
        <svg
          className="w-full h-full animate-spin"
          viewBox="0 0 50 50"
        >
          <circle
            cx="25"
            cy="25"
            r="20"
            fill="none"
            stroke="rgba(0, 0, 128, 0.1)"
            strokeWidth="4"
          />
          <circle
            cx="25"
            cy="25"
            r="20"
            fill="none"
            stroke="url(#spinner-gradient)"
            strokeWidth="4"
            strokeDasharray="30 100"
            strokeLinecap="round"
          />
          <defs>
            <linearGradient id="spinner-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#ff9933" />
              <stop offset="50%" stopColor="#ffffff" />
              <stop offset="100%" stopColor="#138808" />
            </linearGradient>
          </defs>
        </svg>
      </div>
    </div>
  );
}
