import React from 'react';
import type { AnalysisResult } from '../../types/api';
import { SubtaskResults } from './SubtaskResults';
import { ConfidenceBadge } from './ConfidenceBadge';
import { ExecutionTrace } from './ExecutionTrace';
import { ReportDownloadBtn } from './ReportDownloadBtn';
import { ModelRegistryModal } from './ModelRegistryModal';
import { Brain, Database } from 'lucide-react';

interface RightPanelProps {
  result: AnalysisResult;
}

export const RightPanel: React.FC<RightPanelProps> = ({ result }) => {
  const [showRegistry, setShowRegistry] = React.useState(false);

  return (
    <div className="flex flex-col gap-3 h-full overflow-y-auto pr-1">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <Brain size={14} className="text-accent-cyan" />
          <h3 className="text-text-primary font-semibold text-sm">SatQuery Analysis</h3>
        </div>
        <p className="text-text-secondary text-xs font-mono tracking-wide">
          {result.task_type?.toUpperCase()} · {result.model_info?.model_mode?.toUpperCase()}
        </p>
      </div>

      {/* Subtask results — bound to backend subtasks[] */}
      <SubtaskResults subtasks={result.subtasks} />

      {/* Confidence breakdown — bound to backend heuristic_confidence */}
      {result.heuristic_confidence ? (
        <ConfidenceBadge data={result.heuristic_confidence} />
      ) : (
        <div className="limitation-notice text-xs">Confidence data unavailable.</div>
      )}

      {/* Model info */}
      <div className="glass-sm p-3 border border-tech-sm">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1.5">
            <Database size={11} className="text-text-secondary" />
            <span className="text-[10px] font-mono text-text-secondary tracking-wider uppercase">Model</span>
          </div>
          <button
            onClick={() => setShowRegistry(true)}
            className="text-[10px] font-mono text-accent-cyan hover:underline"
          >
            View Registry
          </button>
        </div>
        {result.model_info && (
          <div className="flex flex-col gap-0.5">
            <p className="text-xs text-text-primary">{result.model_info.name}</p>
            <p className="text-[10px] font-mono text-text-secondary">
              Encoder: <span className="text-text-telemetry">{result.model_info.encoder}</span>
            </p>
            <p className="text-[10px] font-mono text-text-secondary">
              Training: <span className="text-text-primary">{result.model_info.training_status}</span>
            </p>
            <p className="text-[10px] font-mono text-text-secondary/50 leading-relaxed mt-1">
              {result.model_info.inference_provenance}
            </p>
          </div>
        )}
      </div>

      {/* Execution trace */}
      <ExecutionTrace traceSteps={result.trace_steps} />

      {/* Report download */}
      <ReportDownloadBtn jobId={result.job_id} />

      {/* Model registry modal */}
      {showRegistry && <ModelRegistryModal onClose={() => setShowRegistry(false)} />}
    </div>
  );
};
