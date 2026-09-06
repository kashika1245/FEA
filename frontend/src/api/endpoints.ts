import { apiBaseUrl, apiFetch, queryString } from "./client";
import type {
  ArtifactSummary,
  AsymmetryRow,
  CombinedResponse,
  ExperimentDetail,
  ExperimentSummary,
  HealthResponse,
  InterpolationSeed,
  JobDetail,
  JobType,
  ProfileRow,
  ReadinessResponse,
  ThresholdRow,
} from "./types";

export function getHealth() {
  return apiFetch<HealthResponse>("/api/v1/health");
}

export function getReady() {
  return apiFetch<ReadinessResponse>("/api/v1/ready");
}

export function getExperiments(offset = 0, limit = 50) {
  return apiFetch<ExperimentSummary[]>(
    `/api/v1/experiments${queryString({ offset, limit })}`,
  );
}

export function getExperiment(experimentId: string) {
  return apiFetch<ExperimentDetail>(`/api/v1/experiments/${encodeURIComponent(experimentId)}`);
}

export function createExperiment(experimentId: string) {
  return apiFetch<ExperimentSummary>("/api/v1/experiments", {
    method: "POST",
    body: JSON.stringify({ experiment_id: experimentId }),
  });
}

export function runExperiment(experimentId: string, jobType: JobType, idempotencyKey?: string) {
  const headers: Record<string, string> = {};
  if (idempotencyKey) headers["X-Idempotency-Key"] = idempotencyKey;
  return apiFetch<JobDetail>(`/api/v1/experiments/${encodeURIComponent(experimentId)}/run`, {
    method: "POST",
    headers,
    body: JSON.stringify({ job_type: jobType }),
  });
}

export function cancelExperiment(experimentId: string) {
  return apiFetch<JobDetail>(`/api/v1/experiments/${encodeURIComponent(experimentId)}/cancel`, {
    method: "POST",
  });
}

export function getJobs(offset = 0, limit = 50, experimentId?: string) {
  return apiFetch<JobDetail[]>(
    `/api/v1/jobs${queryString({ offset, limit, experiment_id: experimentId })}`,
  );
}

export function getJob(jobId: string) {
  return apiFetch<JobDetail>(`/api/v1/jobs/${encodeURIComponent(jobId)}`);
}

export function cancelJob(jobId: string) {
  return apiFetch<JobDetail>(`/api/v1/jobs/${encodeURIComponent(jobId)}/cancel`, { method: "POST" });
}

export function getArtifacts(experimentId: string, offset = 0, limit = 100) {
  return apiFetch<ArtifactSummary[]>(
    `/api/v1/artifacts${queryString({ experiment_id: experimentId, offset, limit })}`,
  );
}

export async function getAllArtifacts(experimentId: string) {
  const collected: ArtifactSummary[] = [];
  let offset = 0;
  const pageSize = 100;
  while (offset < 2000) {
    const page = await getArtifacts(experimentId, offset, pageSize);
    collected.push(...page);
    if (page.length < pageSize) break;
    offset += pageSize;
  }
  return collected;
}

export function getArtifact(artifactId: string) {
  return apiFetch<ArtifactSummary>(`/api/v1/artifacts/${encodeURIComponent(artifactId)}`);
}

export function artifactDownloadUrl(artifactId: string): string {
  return `${apiBaseUrl()}/api/v1/artifacts/${encodeURIComponent(artifactId)}/download`;
}

export function getResearchSummary(experimentId: string) {
  return apiFetch<ExperimentDetail>(
    `/api/v1/research/summary${queryString({ experiment_id: experimentId })}`,
  );
}

export function getProfiles(params: {
  experimentId: string;
  variable?: string;
  output?: string;
  seed?: number;
  offset?: number;
  limit?: number;
}) {
  return apiFetch<{ experiment_id: string; rows: ProfileRow[] }>(
    `/api/v1/research/profiles${queryString({
      experiment_id: params.experimentId,
      variable: params.variable,
      output: params.output,
      seed: params.seed,
      offset: params.offset ?? 0,
      limit: params.limit ?? 200,
    })}`,
  );
}

export function getThresholds(params: {
  experimentId: string;
  variable?: string;
  output?: string;
  seed?: number;
  offset?: number;
  limit?: number;
}) {
  return apiFetch<{ experiment_id: string; rows: ThresholdRow[] }>(
    `/api/v1/research/thresholds${queryString({
      experiment_id: params.experimentId,
      variable: params.variable,
      output: params.output,
      seed: params.seed,
      offset: params.offset ?? 0,
      limit: params.limit ?? 200,
    })}`,
  );
}

export function getAsymmetry(params: {
  experimentId: string;
  variable?: string;
  output?: string;
  seed?: number;
  offset?: number;
  limit?: number;
}) {
  return apiFetch<{ experiment_id: string; rows: AsymmetryRow[] }>(
    `/api/v1/research/asymmetry${queryString({
      experiment_id: params.experimentId,
      variable: params.variable,
      output: params.output,
      seed: params.seed,
      offset: params.offset ?? 0,
      limit: params.limit ?? 200,
    })}`,
  );
}

export function getInterpolation(experimentId: string) {
  return apiFetch<{ experiment_id: string; seeds: InterpolationSeed[] }>(
    `/api/v1/research/interpolation${queryString({ experiment_id: experimentId })}`,
  );
}

export function getCombined(params: {
  experimentId: string;
  output: string;
  directionA3: string;
  directionF: string;
  seed: number;
}) {
  return apiFetch<CombinedResponse>(
    `/api/v1/research/combined${queryString({
      experiment_id: params.experimentId,
      output: params.output,
      direction_a3: params.directionA3,
      direction_f: params.directionF,
      seed: params.seed,
    })}`,
  );
}
