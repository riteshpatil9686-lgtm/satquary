import React from 'react';
import type { AnalysisResult } from '../../types/api';
import { FileText, Globe } from 'lucide-react';

interface LeftPanelProps {
  result: AnalysisResult;
  query: string;
}

const TASK_LABELS: Record<string, string> = {
  'rs-vqa-binary': 'Binary VQA',
  'rs-vqa-mcq': 'Multiple-Choice VQA',
  'captioning': 'Scene Captioning',
  'grounding': 'Spatial Grounding',
  'change-vqa': 'Change Detection',
  'fusion': 'Multi-Sensor Fusion',
};

export const LeftPanel: React.FC<LeftPanelProps> = ({ result, query }) => (
  <div className="flex flex-col gap-3">
    {/* Query */}
    <div className="glass-sm p-3 border border-tech-sm">
      <div className="flex items-center gap-1.5 mb-2">
        <FileText size={11} className="text-text-secondary" />
        <span className="text-[10px] font-mono text-text-secondary tracking-wider uppercase">Query</span>
      </div>
      <p className="text-text-primary text-sm leading-relaxed">"{query}"</p>
    </div>

    {/* Analysis details — all from backend result */}
    <div className="glass-sm p-3 border border-tech-sm">
      <div className="flex items-center gap-1.5 mb-2">
        <Globe size={11} className="text-text-secondary" />
        <span className="text-[10px] font-mono text-text-secondary tracking-wider uppercase">Analysis Details</span>
      </div>
      <div className="flex flex-col gap-1.5">
        <Row label="Task Type" value={TASK_LABELS[result.task_type] ?? result.task_type} />
        <Row label="Mode" value={result.model_info?.model_mode?.toUpperCase() ?? '—'} />
        <Row label="Encoder" value={result.model_info?.encoder ?? '—'} highlight />
        <Row label="Training" value={result.model_info?.training_status ?? '—'} />
        <Row label="Temporal Pair" value={result.temporal_pair ? 'Yes (Before/After)' : 'No (Single Image)'} />
        <Row
          label="Compatibility"
          value={result.compatibility_status?.toUpperCase() ?? '—'}
          warn={result.compatibility_status === 'warning'}
        />
      </div>
    </div>

    {/* Compatibility message if warning */}
    {result.compatibility_status === 'warning' && result.compatibility_message && (
      <div className="flex items-start gap-2 px-3 py-2 rounded-lg bg-yellow-500/08 border border-yellow-500/20">
        <span className="text-yellow-400 text-xs">⚠</span>
        <p className="text-yellow-400/80 text-[10px] font-mono leading-relaxed">{result.compatibility_message}</p>
      </div>
    )}
  </div>
);

const Row: React.FC<{ label: string; value: string; highlight?: boolean; warn?: boolean }> = ({
  label, value, highlight, warn
}) => (
  <div className="flex items-center justify-between">
    <span className="text-[10px] font-mono text-text-secondary">{label}</span>
    <span className={`text-[10px] font-mono ${
      warn ? 'text-yellow-400' : highlight ? 'text-accent-cyan' : 'text-text-primary'
    }`}>
      {value}
    </span>
  </div>
);
