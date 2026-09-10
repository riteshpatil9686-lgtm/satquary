import React from 'react';
import { Header } from '../shared/Header';
import { LeftPanel } from './LeftPanel';
import { CenterMap } from './CenterMap';
import { RightPanel } from './RightPanel';
import type { AnalysisResult } from '../../types/api';
import { ArrowLeft } from 'lucide-react';

interface WorkspacePageProps {
  result: AnalysisResult;
  query: string;
  onBack: () => void;
  fileUrl?: string;
}

export const WorkspacePage: React.FC<WorkspacePageProps> = ({ result, query, onBack, fileUrl }) => {
  const activeUrl =
    fileUrl ??
    result.file_url ??
    result.preview_url ??
    (result.file_tokens && result.file_tokens[0] ? `/api/files/${result.file_tokens[0]}/preview` : undefined);

  return (
    <div className="w-screen h-screen flex flex-col bg-space-black overflow-hidden grid-overlay">
      {/* Header */}
      <Header onLogoClick={onBack} />

      {/* Back button */}
      <div className="pt-16 px-4 py-2 flex items-center gap-2">
        <button onClick={onBack} className="btn-ghost flex items-center gap-1.5">
          <ArrowLeft size={12} />
          <span>Back to Globe</span>
        </button>
        <span className="text-text-secondary/30 text-xs">·</span>
        <span className="text-text-secondary text-xs font-mono truncate max-w-xs">
          {result.task_type?.toUpperCase()}
        </span>
      </div>

      {/* 3-panel layout */}
      <div className="flex-1 grid grid-cols-[260px_1fr_300px] gap-3 px-4 pb-4 min-h-0">
        {/* Left panel */}
        <div className="overflow-y-auto py-1">
          <LeftPanel result={result} query={query} />
        </div>

        {/* Center map */}
        <div className="min-h-0 py-1">
          <CenterMap result={result} fileUrl={activeUrl} />
        </div>

      {/* Right panel */}
      <div className="min-h-0 py-1 overflow-y-auto">
        <RightPanel result={result} />
      </div>
    </div>
  </div>
  );
};
