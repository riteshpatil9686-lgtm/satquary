import React from 'react';
import { CheckCircle, XCircle, Loader, Circle } from 'lucide-react';
import type { TraceStep } from '../../types/api';

const STEP_LABELS = [
  'File Validation',
  'Understanding Request',
  'Compatibility Check',
  'Selecting AI Model',
  'Running AI Analysis',
  'Fusing Results',
  'Estimating Confidence',
  'Generating Evidence',
  'Assembling Report',
];

interface PipelineStepsProps {
  traceSteps: TraceStep[];
}

const StepIcon: React.FC<{ status: TraceStep['status'] }> = ({ status }) => {
  switch (status) {
    case 'completed': return <CheckCircle size={14} className="text-green-400 flex-shrink-0" />;
    case 'error':     return <XCircle size={14} className="text-red-400 flex-shrink-0" />;
    case 'running':   return <Loader size={14} className="text-accent-cyan flex-shrink-0 animate-spin" />;
    case 'skipped':   return <Circle size={14} className="text-limitation flex-shrink-0 opacity-40" />;
    default:          return <Circle size={14} className="text-border-dim flex-shrink-0" />;
  }
};

export const PipelineSteps: React.FC<PipelineStepsProps> = ({ traceSteps }) => {
  return (
    <div className="flex flex-col gap-2 w-full max-w-xs">
      {STEP_LABELS.map((label, i) => {
        const step = traceSteps.find((s) => s.step_index === i);
        const status = step?.status ?? 'pending';
        return (
          <div
            key={i}
            className={`flex items-start gap-3 transition-opacity duration-300 ${
              status === 'pending' || status === 'skipped' ? 'opacity-30' : 'opacity-100'
            }`}
          >
            <StepIcon status={status} />
            <div className="flex-1 min-w-0">
              <p className={`text-xs font-mono tracking-wide pipeline-step-${status}`}>
                {`${String(i + 1).padStart(2, '0')} ${label.toUpperCase()}`}
              </p>
              {step?.message && status !== 'pending' && (
                <p className="text-[10px] text-text-secondary truncate mt-0.5">{step.message}</p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};


interface ProcessingOverlayProps {
  traceSteps: TraceStep[];
  query: string;
}

export const ProcessingOverlay: React.FC<ProcessingOverlayProps> = ({ traceSteps, query }) => {
  const runningStep = traceSteps.find((s) => s.status === 'running');
  const completedCount = traceSteps.filter((s) => s.status === 'completed').length;

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-space-black/85 backdrop-blur-sm animate-fade-in">
      <div className="glass glow-cyan p-8 max-w-sm w-full mx-4 animate-slide-up">
        {/* Orbital loader */}
        <div className="flex justify-center mb-6">
          <div className="relative">
            <div className="orbital-ring w-14 h-14" />
            <div
              className="absolute inset-2 orbital-ring opacity-50"
              style={{ animationDirection: 'reverse', animationDuration: '1.5s' }}
            />
          </div>
        </div>

        <h3 className="text-text-primary font-semibold text-center mb-1 text-sm">
          {runningStep ? runningStep.step_name : 'Processing…'}
        </h3>
        <p className="text-text-secondary text-center text-xs mb-6 truncate px-2">"{query}"</p>

        {/* Progress */}
        <div className="confidence-bar-track mb-6">
          <div
            className="confidence-bar-fill"
            style={{ width: `${(completedCount / 9) * 100}%` }}
          />
        </div>

        {/* Steps */}
        <div className="flex justify-center">
          <PipelineSteps traceSteps={traceSteps} />
        </div>

        <p className="text-text-secondary/40 text-center text-[10px] font-mono mt-6 tracking-wider">
          SATQUERY AI • EARTH OBSERVATION INTELLIGENCE
        </p>
      </div>
    </div>
  );
};
