import axios from 'axios';
import type {
  UploadResponse,
  JobRecord,
  AnalysisResult,
  HealthResponse,
  ModelInfo,
} from '../types/api';

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000';

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
});

// Never expose stack traces — interceptor masks raw errors
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const detail = err?.response?.data?.detail;
    const message = typeof detail === 'string'
      ? detail
      : 'An error occurred. Please try again.';
    return Promise.reject(new Error(message));
  }
);

export const uploadFile = async (
  file: File,
  temporalLabel: 'single' | 't1' | 't2' = 'single'
): Promise<UploadResponse> => {
  const form = new FormData();
  form.append('file', file);
  const res = await api.post<UploadResponse>(
    `/api/upload?temporal_label=${temporalLabel}`,
    form,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  );
  return res.data;
};

export const startAnalysis = async (
  fileTokens: string[],
  query: string,
  aoiBounds?: { north: number; south: number; east: number; west: number }
): Promise<{ job_id: string; status: string }> => {
  const res = await api.post('/api/analyze', {
    file_tokens: fileTokens,
    query,
    aoi_bounds: aoiBounds ?? null,
  });
  return res.data;
};

export const getJobStatus = async (jobId: string): Promise<JobRecord> => {
  const res = await api.get<JobRecord>(`/api/jobs/${jobId}`);
  return res.data;
};

export const getResults = async (jobId: string): Promise<AnalysisResult> => {
  const res = await api.get<AnalysisResult>(`/api/results/${jobId}`);
  return res.data;
};

export const submitClarification = async (
  jobId: string,
  chosenTask: string
): Promise<{ job_id: string; status: string; chosen_task: string }> => {
  const res = await api.post(`/api/clarify/${jobId}`, { chosen_task: chosenTask });
  return res.data;
};

export const listModels = async (): Promise<{ models: ModelInfo[] }> => {
  const res = await api.get('/api/models');
  return res.data;
};

export const getHealth = async (): Promise<HealthResponse> => {
  const res = await api.get<HealthResponse>('/api/health');
  return res.data;
};

export const getReportUrl = (jobId: string): string =>
  `${BASE_URL}/api/report/${jobId}`;
