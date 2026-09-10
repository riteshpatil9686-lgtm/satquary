import React from 'react';
import type { SubtaskResult } from '../../types/api';
import { ProvenanceBadge } from '../shared/ModeBadge';
import { LimitationNotice } from './LimitationNotice';
import { CheckCircle, AlertTriangle } from 'lucide-react';

interface SubtaskResultsProps {
  subtasks: SubtaskResult[];
}

const TASK_TYPE_LABELS: Record<string, string> = {
  'rs-vqa-binary': 'Binary VQA',
  'rs-vqa-mcq': 'Multiple-Choice VQA',
  'captioning': 'Scene Description',
  'grounding': 'Spatial Grounding',
  'change-vqa': 'Change Analysis',
  'fusion': 'Multi-Sensor Fusion',
};

export const SubtaskResults: React.FC<SubtaskResultsProps> = ({ subtasks }) => {
  if (subtasks.length === 0) return null;

  return (
    <div className="flex flex-col gap-3">
      {subtasks.map((sub, i) => (
        <div key={sub.subtask_id} className="glass-sm p-3 border border-tech-sm animate-slide-up">
          {/* Header */}
          <div className="flex items-center gap-2 mb-2">
            {sub.supported
              ? <CheckCircle size={13} className="text-green-400 flex-shrink-0" />
              : <AlertTriangle size={13} className="text-yellow-400 flex-shrink-0" />}
            <span className="text-[10px] font-mono text-text-secondary tracking-wider uppercase">
              {subtasks.length > 1 ? `Subtask ${i + 1} · ` : ''}{TASK_TYPE_LABELS[sub.task_type] ?? sub.task_type}
            </span>
          </div>

          {/* Query fragment */}
          {subtasks.length > 1 && (
            <p className="text-text-secondary text-xs mb-2 italic">"{sub.query_fragment}"</p>
          )}

          {/* Answer or limitation */}
          {sub.supported && sub.answer ? (
            <p className="text-text-primary text-sm leading-relaxed">{sub.answer}</p>
          ) : (
            <LimitationNotice
              message={sub.limitation_message ?? 'This subtask could not be performed with the available input.'}
            />
          )}

          {/* Counting result */}
          {sub.count !== null && sub.count !== undefined && (
            <div className="mt-2 flex items-center gap-2">
              <span className="font-telemetry text-accent-cyan text-sm">{sub.count}</span>
              <span className="text-text-secondary text-xs">instances detected</span>
            </div>
          )}
          {sub.count_note && (
            <p className="text-[10px] text-text-secondary/60 font-mono mt-1">{sub.count_note}</p>
          )}

          {/* Evidence count */}
          {sub.evidence.length > 0 && (
            <p className="text-[10px] font-mono text-accent-cyan/60 mt-2">
              {sub.evidence.length} evidence item{sub.evidence.length > 1 ? 's' : ''} overlaid on map
            </p>
          )}

          {/* Grounding limitation */}
          {!sub.grounding_supported && sub.supported && (
            <p className="text-[10px] font-mono text-limitation mt-1">
              Spatial grounding is unavailable for the selected model.
            </p>
          )}

          {/* Provenance */}
          <div className="mt-2 flex items-center gap-2">
            {sub.evidence[0] && (
              <ProvenanceBadge
                provenance={sub.evidence[0].provenance}
              />
            )}
          </div>
        </div>
      ))}
    </div>
  );
};
