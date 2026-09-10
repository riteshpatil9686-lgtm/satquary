import React from 'react';
import type { HeuristicConfidence } from '../../types/api';
import { Lock } from 'lucide-react';

interface ConfidenceBadgeProps {
  data: HeuristicConfidence;
}

const Bar: React.FC<{ value: number | null; label: string; weight: string }> = ({ value, label, weight }) => (
  <div className="mb-2">
    <div className="flex justify-between items-center mb-1">
      <span className="text-[10px] text-text-secondary font-mono">{label}</span>
      <div className="flex items-center gap-2">
        <span className="text-[10px] text-text-secondary/50 font-mono">w={weight}</span>
        <span className="text-[10px] font-mono text-text-telemetry">
          {value !== null ? value.toFixed(3) : 'N/A'}
        </span>
      </div>
    </div>
    <div className="confidence-bar-track">
      <div
        className="confidence-bar-fill"
        style={{ width: value !== null ? `${value * 100}%` : '0%', opacity: value !== null ? 1 : 0.3 }}
      />
    </div>
  </div>
);

export const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({ data }) => {
  const pct = Math.round(data.final_confidence * 100);

  return (
    <div className="glass-sm p-3 border border-tech-sm">
      {/* Label */}
      <p className="text-[10px] text-text-secondary font-mono mb-2 tracking-wide">{data.label}</p>

      {/* Final score */}
      <div className="flex items-center gap-2 mb-3">
        <span
          className="text-2xl font-bold font-telemetry"
          style={{ color: pct > 70 ? '#22c55e' : pct > 50 ? '#00d4ff' : '#f59e0b' }}
        >
          {pct}%
        </span>
        {data.capped && (
          <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-yellow-500/10 border border-yellow-500/20">
            <Lock size={9} className="text-yellow-400" />
            <span className="text-[10px] text-yellow-400 font-mono">CAPPED</span>
          </div>
        )}
      </div>
      {data.cap_reason && (
        <p className="text-[10px] text-yellow-400/70 font-mono mb-3 leading-relaxed">{data.cap_reason}</p>
      )}

      {/* Formula breakdown */}
      <Bar value={data.query_confidence} label="Query Interpretation" weight="0.25" />
      <Bar value={data.compatibility_score} label="Compatibility Score" weight="0.20" />
      <Bar value={data.model_confidence} label="Model Confidence" weight="0.35" />
      <Bar value={data.evidence_consistency} label="Evidence Consistency" weight="0.20" />

      {/* Formula display */}
      <div className="mt-2 pt-2 border-t border-border-dim">
        <p className="text-[9px] font-mono text-text-secondary/40 leading-relaxed">
          0.25×{data.query_confidence?.toFixed(2)} + 0.20×{data.compatibility_score?.toFixed(2)} + 0.35×
          {data.model_confidence?.toFixed(2) ?? 'N/A'} + 0.20×{data.evidence_consistency?.toFixed(2) ?? 'N/A'} = {data.final_confidence.toFixed(3)}
          {data.capped ? ' → CAPPED at 0.60' : ''}
        </p>
      </div>
    </div>
  );
};
