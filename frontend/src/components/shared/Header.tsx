import React, { useState, useEffect } from 'react';
import { Satellite, Activity } from 'lucide-react';
import { ModeBadge } from './ModeBadge';
import { getHealth } from '../../services/api';
import type { HealthResponse } from '../../types/api';

interface HeaderProps {
  onLogoClick?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onLogoClick }) => {
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    getHealth().then(setHealth).catch(() => null);
  }, []);

  return (
    <header className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-3 glass border-b border-tech">
      {/* Logo */}
      <button
        onClick={onLogoClick}
        className="flex items-center gap-2.5 group"
      >
        <div className="relative">
          <Satellite size={20} className="text-accent-cyan group-hover:text-white transition-colors" />
          <div className="absolute -inset-1 bg-accent-cyan/10 rounded-full group-hover:bg-accent-cyan/20 transition-colors" />
        </div>
        <div>
          <span className="text-text-primary font-semibold tracking-wide text-sm">SatQuery</span>
          <span className="text-accent-cyan font-semibold tracking-wide text-sm"> AI</span>
        </div>
      </button>

      {/* Center: System status */}
      <div className="hidden md:flex items-center gap-2 text-xs font-mono text-text-secondary">
        <Activity size={12} className={health?.status === 'healthy' ? 'text-green-400' : 'text-yellow-400'} />
        <span className="tracking-wider uppercase">
          {health ? `SATELLITE DATA ${health.status === 'healthy' ? 'ONLINE' : 'DEGRADED'}` : 'CONNECTING…'}
        </span>
      </div>

      {/* Right: Mode badge + device */}
      <div className="flex items-center gap-3">
        {health && <ModeBadge mode={health.mode} />}
        {health && (
          <span className="hidden sm:block font-mono text-[10px] text-text-secondary tracking-wider uppercase">
            {health.device.toUpperCase()}
          </span>
        )}
      </div>
    </header>
  );
};
