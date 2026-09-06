export type JobType =
  | "TRAIN_SURROGATE"
  | "INTERPOLATION_EVALUATION"
  | "EXTRAPOLATION"
  | "COMBINED_EXTRAPOLATION"
  | "PROFILE_BUILD"
  | "REPORT_BUILD"
  | "FULL_PHASE2_PIPELINE";

export type JobStatus =
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "cancel_requested"
  | "cancelled";

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    request_id: string;
  };
}

export interface HealthResponse {
  status: "ok";
}

export interface ReadinessResponse {
  ready: boolean;
  checks: Record<string, boolean>;
}

export interface ArtifactSummary {
  artifact_id: string;
  experiment_id: string;
  relative_path: string;
  media_type: string;
  size_bytes: number;
  sha256: string | null;
}

export interface ExperimentSummary {
  experiment_id: string;
  status: string | null;
  immutable: boolean;
  dataset_hash: string | null;
  normalization_hash: string | null;
  configuration_hash: string | null;
  artifact_count: number;
  variable_wise_rows: number | null;
  combined_rows: number | null;
  profile_rows: number | null;
}

export interface ExperimentDetail extends ExperimentSummary {
  manifest: Record<string, unknown> | null;
  artifacts: ArtifactSummary[];
  validation_ranking: Record<string, unknown> | null;
  frozen_dataset_hash: string;
}

export interface JobProgress {
  stage: string | null;
  completed: number | null;
  total: number | null;
  fraction: number | null;
}

export interface JobSummary {
  job_id: string;
  experiment_id: string;
  job_type: string;
  status: JobStatus;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface JobDetail extends JobSummary {
  progress: JobProgress;
  message: string | null;
  error_code: string | null;
  error_message: string | null;
}

export interface ProfileRow {
  model_id: string;
  seed: number;
  variable: string;
  direction: "lower" | "upper" | string;
  delta: number;
  response: string;
  n_anchors: number;
  q1_relative_error_pct: number;
  median_relative_error_pct: number;
  q3_relative_error_pct: number;
  mean_relative_error_pct: number;
  median_absolute_error: number;
  rmse: number;
  mean_signed_error: number;
  median_signed_error: number;
  max_relative_error_pct: number;
  primary_metric: string;
  [key: string]: unknown;
}

export interface ThresholdRow {
  model_id: string;
  seed: number;
  variable: string;
  response: string;
  lower_5: string;
  upper_5: string;
  lower_10: string;
  upper_10: string;
  [key: string]: unknown;
}

export interface AsymmetryRow {
  model_id: string;
  seed: number;
  variable: string;
  response: string;
  delta: number;
  upper_median_relative_error_pct: number;
  lower_median_relative_error_pct: number;
  upper_minus_lower_median_relative_error_pct: number;
  [key: string]: unknown;
}

export interface InterpolationMetric {
  response: string;
  mae: number;
  rmse: number;
  mean_relative_error_pct: number;
  median_relative_error_pct: number;
  max_relative_error_pct: number;
  mean_signed_error: number;
  median_signed_error: number;
  r2: number;
  n: number;
}

export interface InterpolationSeed {
  seed: number;
  model_id: string;
  passed_gate: boolean;
  gate_notes: string[];
  metrics: InterpolationMetric[];
}

export interface CombinedCell {
  delta_a3: number;
  delta_f: number;
  median_relative_error_pct: number;
  n: number;
}

export interface CombinedResponse {
  experiment_id: string;
  response: string;
  direction_a3: string;
  direction_f: string;
  seed: number;
  cells: CombinedCell[];
}

export const VARIABLES = [
  "A1",
  "A2",
  "A3",
  "A4",
  "A5",
  "A6",
  "A7",
  "A8",
  "A9",
  "A10",
  "E",
  "F",
] as const;

export const RESPONSES = ["u_max", "sigma_max", "C"] as const;
export const DIRECTIONS = ["lower", "upper"] as const;
export const FROZEN_SEEDS = [20260905, 20260906, 20260907, 20260908, 20260909] as const;
export const NOT_REACHED = "not reached";
