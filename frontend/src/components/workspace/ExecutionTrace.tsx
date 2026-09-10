import React, { useState } from 'react';
import type { TraceStep } from '../../types/api';
import { ChevronDown, ChevronRight } from 'lucide-react';

interface ExecutionTraceProps {
  traceSteps: TraceStep[];
}

const STATUS_COLOR: Record<string, string> = {
  completed: 'text-green-400',
  error:     'text-red-400',
  running:   'text-accent-cyan',
  skipped:   'text-limitation',
  pending:   'text-border-dim',
};

const STATUS_ICON: Record<string, string> = {
  completed: '✓',
  error:     '✗',
  running:   '⟳',
  skipped:   '—',
  pending:   '·',
};

export const ExecutionTrace: React.FC<ExecutionTraceProps> = ({ traceSteps }) => {
  const [open, setOpen] = useState(false);

  return (
    <div className="glass-sm border border-tech-sm">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-3 py-2 text-xs font-mono text-text-secondary hover:text-text-primary transition-colors"
      >
        <span className="tracking-widest uppercase">Execution Trace</span>
        {open ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
      </button>

      {open && (
        <div className="px-3 pb-3 flex flex-col gap-1.5 border-t border-border-dim animate-fade-in">
          {traceSteps.map((step) => (
            <div key={step.step_index} className="flex items-start gap-2">
              <span className={`font-telemetry text-[10px] flex-shrink-0 w-3 ${STATUS_COLOR[step.status]}`}>
                {STATUS_ICON[step.status]}
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-baseline gap-2">
                  <span className={`text-[10px] font-mono tracking-wide ${STATUS_COLOR[step.status]}`}>
                    [{step.step_index}] {step.step_name}
                  </span>
                  {step.completed_at && (
                    <span className="text-[9px] text-text-secondary/40 font-mono flex-shrink-0">
                      {step.completed_at.slice(11, 19)} UTC
                    </span>
                  )}
                </div>
                {step.message && (
                  <p className="text-[10px] text-text-secondary leading-relaxed break-words mt-0.5">{step.message}</p>
                )}
                {step.detail && typeof step.detail === 'object' && (step.detail as any).scenario_match && (
                  <div className="mt-1 p-1.5 bg-black/40 border border-tech-sm text-[9px] font-mono space-y-0.5 text-text-secondary">
                    <div><span className="text-accent-cyan">Scenario Match:</span> {(step.detail as any).scenario_match}</div>
                    <div><span className="text-text-muted">Matched task:</span> {(step.detail as any).matched_task}</div>
                    <div><span className="text-text-muted">Matched intent:</span> {(step.detail as any).matched_intent}</div>
                    <div><span className="text-text-muted">Matched fixture:</span> {(step.detail as any).matched_fixture}</div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
