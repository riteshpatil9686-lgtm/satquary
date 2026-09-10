import React from 'react';

interface LoadingSpinnerProps {
  size?: number;
  label?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ size = 32, label }) => (
  <div className="flex flex-col items-center gap-3">
    <div
      className="orbital-ring"
      style={{ width: size, height: size }}
    />
    {label && (
      <p className="text-text-secondary text-xs font-mono tracking-wider animate-pulse">{label}</p>
    )}
  </div>
);
