import React from 'react';
import { AlertTriangle } from 'lucide-react';

interface ErrorBannerProps {
  message: string;
  title?: string;
  onDismiss?: () => void;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({ message, title, onDismiss }) => (
  <div className="animate-slide-up flex items-start gap-3 p-4 rounded-lg border border-red-500/20 bg-red-500/08">
    <AlertTriangle size={16} className="text-red-400 flex-shrink-0 mt-0.5" />
    <div className="flex-1">
      {title && <p className="text-red-400 font-semibold text-sm mb-1">{title}</p>}
      <p className="text-text-secondary text-sm leading-relaxed">{message}</p>
    </div>
    {onDismiss && (
      <button onClick={onDismiss} className="btn-ghost text-text-secondary hover:text-red-400 p-1">✕</button>
    )}
  </div>
);
