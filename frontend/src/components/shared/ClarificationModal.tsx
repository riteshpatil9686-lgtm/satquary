import React from 'react';
import { HelpCircle } from 'lucide-react';
import { submitClarification } from '../../services/api';

interface ClarificationModalProps {
  jobId: string;
  candidates: { task: string; description: string }[];
  onDone: (updatedJobId: string) => void;
  onClose: () => void;
}

const TASK_LABELS: Record<string, string> = {
  'rs-vqa-binary': 'Answer a Yes/No Question',
  'rs-vqa-mcq': 'Multiple-Choice Analysis',
  'captioning': 'Describe the Scene',
  'grounding': 'Locate a Region or Object',
  'change-vqa': 'Change Detection (Before/After)',
  'fusion': 'Optical + SAR Fusion',
};

export const ClarificationModal: React.FC<ClarificationModalProps> = ({
  jobId, candidates, onDone, onClose
}) => {
  const [loading, setLoading] = React.useState<string | null>(null);

  const choose = async (task: string) => {
    setLoading(task);
    try {
      const res = await submitClarification(jobId, task);
      onDone(res.job_id);
    } catch (err) {
      setLoading(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-space-black/80 backdrop-blur-sm animate-fade-in">
      <div className="glass glow-cyan max-w-md w-full mx-4 p-6 animate-slide-up">
        <div className="flex items-center gap-2 mb-4">
          <HelpCircle size={18} className="text-accent-cyan" />
          <h3 className="text-text-primary font-semibold text-base">Clarify Your Request</h3>
        </div>
        <p className="text-text-secondary text-sm mb-5 leading-relaxed">
          I'm not fully sure what you're asking — did you mean one of these?
        </p>
        <div className="flex flex-col gap-2">
          {candidates.map((c) => (
            <button
              key={c.task}
              onClick={() => choose(c.task)}
              disabled={loading !== null}
              className="w-full text-left p-3 rounded-lg border border-tech hover:border-accent-cyan/40 hover:bg-accent-cyan/05 transition-all group"
            >
              <p className="text-text-primary font-medium text-sm group-hover:text-accent-cyan transition-colors">
                {TASK_LABELS[c.task] ?? c.task}
              </p>
              <p className="text-text-secondary text-xs mt-0.5">{c.description}</p>
              {loading === c.task && (
                <p className="text-accent-cyan text-xs mt-1 font-mono animate-pulse">Confirming…</p>
              )}
            </button>
          ))}
        </div>
        <button onClick={onClose} className="btn-ghost mt-4 w-full text-center">Cancel</button>
      </div>
    </div>
  );
};
