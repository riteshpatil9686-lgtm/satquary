import { useState, useCallback } from 'react';
import { LandingPage } from './components/landing/LandingPage';
import { ProcessingOverlay } from './components/processing/ProcessingOverlay';
import { WorkspacePage } from './components/workspace/WorkspacePage';
import { ClarificationModal } from './components/shared/ClarificationModal';
import { ErrorBanner } from './components/shared/ErrorBanner';
import { startAnalysis, getResults } from './services/api';
import { startPolling } from './services/polling';
import type { AnalysisResult, TraceStep } from './types/api';
import type { AOIBounds } from './types/globe';

type AppView = 'landing' | 'processing' | 'workspace';

export default function App() {
  const [view, setView] = useState<AppView>('landing');
  const [jobId, setJobId] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [traceSteps, setTraceSteps] = useState<TraceStep[]>([]);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [clarificationCandidates, setClarificationCandidates] = useState<
    { task: string; description: string }[] | null
  >(null);
  const [fileTokens, setFileTokens] = useState<string[]>([]);

  const handleAnalyze = useCallback(
    async (q: string, tokens: string[], aoi?: AOIBounds) => {
      setQuery(q);
      setFileTokens(tokens);
      setError(null);
      setResult(null);
      setTraceSteps([]);
      setClarificationCandidates(null);

      try {
        const { job_id } = await startAnalysis(tokens, q, aoi);
        setJobId(job_id);
        setView('processing');

        const stopPolling = startPolling(
          job_id,
          (job) => {
            setTraceSteps(job.trace_steps);

            if (job.status === 'needs_clarification') {
              stopPolling();
              setClarificationCandidates(job.clarification_candidates ?? []);
            } else if (job.status === 'incompatible') {
              stopPolling();
              setError(job.compatibility_message ?? 'Images are incompatible for this analysis.');
              setView('landing');
            } else if (job.status === 'error') {
              stopPolling();
              setError(job.error_message ?? 'An error occurred during analysis.');
              setView('landing');
            } else if (job.status === 'completed') {
              stopPolling();
              getResults(job_id).then((r) => {
                setResult(r);
                setView('workspace');
              });
            }
          },
          (err) => {
            setError(err.message);
            setView('landing');
          }
        );
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to start analysis.');
        setView('landing');
      }
    },
    []
  );

  const handleClarificationDone = useCallback(
    (updatedJobId: string) => {
      setClarificationCandidates(null);
      setView('processing');

      const stopPolling = startPolling(
        updatedJobId,
        (job) => {
          setTraceSteps(job.trace_steps);
          if (job.status === 'completed') {
            stopPolling();
            getResults(updatedJobId).then((r) => {
              setResult(r);
              setView('workspace');
            });
          } else if (job.status === 'error' || job.status === 'incompatible') {
            stopPolling();
            setError(job.error_message ?? job.compatibility_message ?? 'Analysis failed.');
            setView('landing');
          }
        },
        (err) => {
          setError(err.message);
          setView('landing');
        }
      );
    },
    []
  );

  return (
    <>
      {/* Error banner (dismissable) */}
      {error && view === 'landing' && (
        <div className="fixed top-16 left-4 right-4 z-50 max-w-xl mx-auto">
          <ErrorBanner
            title="Analysis Error"
            message={error}
            onDismiss={() => setError(null)}
          />
        </div>
      )}

      {/* Clarification modal */}
      {clarificationCandidates && jobId && view === 'processing' && (
        <ClarificationModal
          jobId={jobId}
          candidates={clarificationCandidates}
          onDone={handleClarificationDone}
          onClose={() => {
            setClarificationCandidates(null);
            setView('landing');
          }}
        />
      )}

      {/* Processing overlay */}
      {view === 'processing' && !clarificationCandidates && (
        <ProcessingOverlay traceSteps={traceSteps} query={query} />
      )}

      {/* Main views */}
      {view === 'landing' && (
        <LandingPage onAnalyze={handleAnalyze} isLoading={false} />
      )}

      {view === 'workspace' && result && (
        <WorkspacePage
          result={result}
          query={query}
          fileUrl={
            result.file_url ??
            result.preview_url ??
            (result.file_tokens && result.file_tokens[0] ? `/api/files/${result.file_tokens[0]}/preview` : undefined) ??
            (fileTokens && fileTokens[0] ? `/api/files/${fileTokens[0]}/preview` : undefined)
          }
          onBack={() => {
            setView('landing');
            setResult(null);
          }}
        />
      )}
    </>
  );
}
