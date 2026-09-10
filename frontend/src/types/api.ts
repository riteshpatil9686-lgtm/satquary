// Authoritative TypeScript interfaces for SatQuery AI API responses.
// ALL frontend components must bind to these interfaces only.
// No ad-hoc fields or hardcoded values allowed.

export interface HeuristicConfidence {
  query_confidence: number;
  compatibility_score: number;
  model_confidence: number | null;       // null if unavailable from model
  evidence_consistency: number | null;   // null if unavailable
  final_confidence: number;
  capped: boolean;
  cap_reason: string | null;
  label: 'Estimated confidence (heuristic, uncalibrated)';
}

export interface EvidenceItem {
  id: string;
  type: 'bounding_box' | 'mask' | 'point' | 'text' | 'none';
  provenance: 'real-specialist-model' | 'demo-scenario' | 'derived-computation';
  coordinates: [number, number, number, number] | null;  // [x1,y1,x2,y2]
  label: string | null;
  roi_confidence: number | null;  // from model's localization score; null if unavailable
}

export interface SubtaskResult {
  subtask_id: string;
  task_type: string;
  query_fragment: string;
  supported: boolean;
  limitation_message: string | null;
  answer: string | null;
  count: number | null;
  count_note: string | null;
  evidence: EvidenceItem[];
  grounding_supported: boolean;
}

export interface ModelCapabilities {
  tasks: string[];
  accepts_modalities: string[];
  requires_temporal_pair: boolean;
  grounding_supported: boolean;
  counting_supported: boolean;
  min_bands: number;
  max_bands: number;
  preferred_gsd_min_m: number | null;
  preferred_gsd_max_m: number | null;
}

export interface ModelInfo {
  name: string;
  checkpoint: string;
  model_mode: 'real' | 'demo';
  encoder: 'RemoteCLIP' | 'generic-fallback' | 'demo-encoder';
  training_status: 'pretrained' | 'fine-tuned' | 'demo';
  capabilities: ModelCapabilities;
  inference_provenance: string;
  grounding_supported: boolean;
}

export interface TraceStep {
  step_index: number;
  step_name: string;
  status: 'pending' | 'running' | 'completed' | 'error' | 'skipped';
  message: string | null;
  detail: Record<string, unknown> | null;
  started_at: string | null;
  completed_at: string | null;
}

export type JobStatus =
  | 'pending'
  | 'processing'
  | 'completed'
  | 'error'
  | 'needs_clarification'
  | 'incompatible';

export interface JobRecord {
  job_id: string;
  status: JobStatus;
  mode: 'demo' | 'real';
  query_text: string | null;
  task_type: string | null;
  compatibility_status: 'compatible' | 'warning' | 'incompatible' | null;
  compatibility_message: string | null;
  gsd_limitation_note: string | null;
  error_message: string | null;
  clarification_candidates: { task: string; description: string }[] | null;
  temporal_pair: boolean;
  file_tokens?: string[];
  file_url?: string | null;
  preview_url?: string | null;
  created_at: string | null;
  trace_steps: TraceStep[];
}

export interface AnalysisResult {
  job_id: string;
  status: JobStatus;
  task_type: string;
  model_info: ModelInfo;
  subtasks: SubtaskResult[];
  heuristic_confidence: HeuristicConfidence | null;
  temporal_pair: boolean;
  grounding_supported: boolean;
  compatibility_status: 'compatible' | 'warning' | 'incompatible';
  compatibility_message: string | null;
  gsd_limitation_note: string | null;
  error_message: string | null;
  clarification_candidates: { task: string; description: string }[] | null;
  trace_steps: TraceStep[];
  file_tokens?: string[];
  file_url?: string | null;
  preview_url?: string | null;
  preview_urls?: string[];
  routing_decision?: Record<string, unknown>;
}

export interface UploadResponse {
  file_token: string;
  original_filename: string;
  modality: string;
  gsd_meters: number | null;
  band_count: number;
  width_px: number;
  height_px: number;
  crs: string | null;
  temporal_label: string;
  file_size_mb: number;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded';
  mode: 'demo' | 'real';
  device: string;
  database: string;
  pytorch: string;
}
