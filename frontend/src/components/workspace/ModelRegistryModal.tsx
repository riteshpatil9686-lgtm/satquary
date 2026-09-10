import React, { useEffect, useState } from 'react';
import { X, Database } from 'lucide-react';
import { listModels } from '../../services/api';
import type { ModelInfo } from '../../types/api';
import { ProvenanceBadge } from '../shared/ModeBadge';

interface ModelRegistryModalProps {
  onClose: () => void;
}

export const ModelRegistryModal: React.FC<ModelRegistryModalProps> = ({ onClose }) => {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listModels()
      .then((r) => setModels(r.models))
      .catch(() => setModels([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-space-black/80 backdrop-blur-sm animate-fade-in">
      <div className="glass glow-cyan max-w-lg w-full mx-4 p-5 animate-slide-up max-h-[80vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Database size={16} className="text-accent-cyan" />
            <h3 className="text-text-primary font-semibold text-sm">Specialist Model Registry</h3>
          </div>
          <button onClick={onClose} className="btn-ghost p-1"><X size={14} /></button>
        </div>

        {loading ? (
          <p className="text-text-secondary text-xs font-mono animate-pulse">Loading registry…</p>
        ) : (
          <div className="flex flex-col gap-3">
            {models.map((m) => (
              <div key={m.name} className="glass-sm p-3 border border-tech-sm">
                <div className="flex items-center justify-between mb-1.5">
                  <p className="text-text-primary text-sm font-medium">{m.name}</p>
                  <ProvenanceBadge
                    provenance={m.model_mode === 'demo' ? 'demo-scenario' : 'real-specialist-model'}
                    encoder={m.encoder}
                  />
                </div>
                <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-[10px] font-mono text-text-secondary">
                  <span>Encoder: <span className="text-text-telemetry">{m.encoder}</span></span>
                  <span>Training: <span className="text-text-primary">{m.training_status}</span></span>
                  <span>Tasks: <span className="text-text-primary">{m.capabilities.tasks.join(', ')}</span></span>
                  <span>Grounding: <span className={m.grounding_supported ? 'text-green-400' : 'text-limitation'}>{m.grounding_supported ? 'Yes' : 'No'}</span></span>
                </div>
                <p className="text-[9px] text-text-secondary/50 font-mono mt-1.5 leading-relaxed">
                  {m.inference_provenance}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
