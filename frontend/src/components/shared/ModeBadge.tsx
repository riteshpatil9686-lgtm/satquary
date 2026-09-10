import React from 'react';

interface ModeBadgeProps {
  mode: 'demo' | 'real';
}

export const ModeBadge: React.FC<ModeBadgeProps> = ({ mode }) => (
  <span
    className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono font-medium tracking-widest uppercase border ${
      mode === 'demo'
        ? 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400'
        : 'bg-green-500/10 border-green-500/30 text-green-400'
    }`}
  >
    <span className={`w-1.5 h-1.5 rounded-full ${mode === 'demo' ? 'bg-yellow-400' : 'bg-green-400 animate-pulse'}`} />
    {mode === 'demo' ? 'DEMO MODE' : 'REAL MODE'}
  </span>
);

interface ProvenanceBadgeProps {
  provenance: 'real-specialist-model' | 'demo-scenario' | 'derived-computation';
  encoder?: string;
}

export const ProvenanceBadge: React.FC<ProvenanceBadgeProps> = ({ provenance, encoder }) => {
  if (provenance === 'demo-scenario') {
    return <span className="badge-demo-scenario">demo scenario</span>;
  }
  if (encoder === 'generic-fallback') {
    return <span className="badge-fallback">generic-fallback</span>;
  }
  return <span className="badge-real-model">real model</span>;
};
