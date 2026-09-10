import { getJobStatus } from './api';
import type { JobRecord, JobStatus } from '../types/api';

const TERMINAL_STATUSES: JobStatus[] = [
  'completed',
  'error',
  'needs_clarification',
  'incompatible',
];

/**
 * Poll GET /api/jobs/{jobId} at a given interval until the job reaches a terminal status.
 * onUpdate is called with each polled JobRecord.
 * Returns a stop function to cancel polling.
 */
export function startPolling(
  jobId: string,
  onUpdate: (job: JobRecord) => void,
  onError: (err: Error) => void,
  intervalMs = 1500
): () => void {
  let stopped = false;
  let timeoutId: ReturnType<typeof setTimeout>;

  const poll = async () => {
    if (stopped) return;
    try {
      const job = await getJobStatus(jobId);
      onUpdate(job);
      if (!TERMINAL_STATUSES.includes(job.status)) {
        timeoutId = setTimeout(poll, intervalMs);
      }
    } catch (err) {
      onError(err instanceof Error ? err : new Error('Polling failed'));
    }
  };

  poll();
  return () => {
    stopped = true;
    clearTimeout(timeoutId);
  };
}
