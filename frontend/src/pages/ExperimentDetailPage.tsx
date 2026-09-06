import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import type { JobType } from "../api/types";
import { cancelExperiment, getExperiment, getJobs, runExperiment } from "../api/endpoints";
import { ErrorBanner } from "../components/ErrorBanner";
import { StatusBadge } from "../components/StatusBadge";
import { formatHash, formatNumber, formatTimestamp } from "../lib/format";
import { isTerminal } from "../lib/status";

export function ExperimentDetailPage() {
  const { id = "" } = useParams();
  const client = useQueryClient();
  const [jobType, setJobType] = useState<JobType>("FULL_PHASE2_PIPELINE");
  const detail = useQuery({ queryKey: ["experiment", id], queryFn: () => getExperiment(id), enabled: Boolean(id) });
  const jobs = useQuery({
    queryKey: ["jobs", id],
    queryFn: () => getJobs(0, 20, id),
    refetchInterval: (query) => {
      const rows = query.state.data ?? [];
      return rows.some((job) => !isTerminal(job.status)) ? 2000 : false;
    },
  });
  const run = useMutation({
    mutationFn: () => runExperiment(id, jobType, crypto.randomUUID().replaceAll("-", "")),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ["jobs", id] });
    },
  });
  const cancel = useMutation({
    mutationFn: () => cancelExperiment(id),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ["jobs", id] });
    },
  });
  const manifest = detail.data?.manifest ?? {};
  return (
    <article>
      <p className="page-kicker">Experiment</p>
      <h1 className="page-title">{id}</h1>
      {detail.isLoading ? <div className="skeleton" style={{ height: 180 }} /> : null}
      <ErrorBanner error={detail.error ?? run.error ?? cancel.error} />
      {detail.data ? (
        <>
          <section className="grid grid-3">
            <div className="card">
              <h2>Identity</h2>
              <p>
                <StatusBadge status={detail.data.status} /> {detail.data.immutable ? "immutable" : "mutable"}
              </p>
              <p className="mono">dataset {formatHash(detail.data.dataset_hash)}</p>
              <p className="mono">norm {formatHash(detail.data.normalization_hash)}</p>
              <p className="mono">config {formatHash(detail.data.configuration_hash)}</p>
            </div>
            <div className="card">
              <h2>Scientific scope</h2>
              <p>Architecture {String(manifest.model_architecture ?? "—")}</p>
              <p>Anchors {String(manifest.anchor_count ?? "—")}</p>
              <p>Directions {Array.isArray(manifest.directions) ? manifest.directions.join(", ") : "—"}</p>
              <p>δ grid from stored manifest, 0.00–0.50 when present.</p>
            </div>
            <div className="card">
              <h2>Outputs</h2>
              <p>Profiles {formatNumber(detail.data.profile_rows, 0)}</p>
              <p>Variable-wise {formatNumber(detail.data.variable_wise_rows, 0)}</p>
              <p>Combined {formatNumber(detail.data.combined_rows, 0)}</p>
              <p>
                <Link to={`/profiles?experiment=${id}`}>Profiles</Link> ·{" "}
                <Link to={`/artifacts?experiment=${id}`}>Artifacts</Link>
              </p>
            </div>
          </section>
          <section className="card" style={{ marginTop: 16 }}>
            <h2>Run a real job</h2>
            <p>
              Frozen Phase 2 IDs cannot be overwritten. New work must use <span className="mono">paper-a.phase3.*</span>.
              Cancellation is cooperative between scientific stages.
            </p>
            <div className="filters">
              <label className="field">
                Job type
                <select value={jobType} onChange={(e) => setJobType(e.target.value as JobType)}>
                  <option value="FULL_PHASE2_PIPELINE">FULL_PHASE2_PIPELINE</option>
                  <option value="TRAIN_SURROGATE">TRAIN_SURROGATE</option>
                  <option value="INTERPOLATION_EVALUATION">INTERPOLATION_EVALUATION</option>
                  <option value="EXTRAPOLATION">EXTRAPOLATION</option>
                </select>
              </label>
              <button type="button" disabled={run.isPending || detail.data.immutable} onClick={() => run.mutate()}>
                Launch job
              </button>
              <button type="button" className="secondary" disabled={cancel.isPending} onClick={() => cancel.mutate()}>
                Cancel active job
              </button>
            </div>
          </section>
          <section className="card" style={{ marginTop: 16 }}>
            <h2>Jobs for this experiment</h2>
            {(jobs.data ?? []).length === 0 ? <p>No jobs recorded for this experiment.</p> : null}
            <ul>
              {(jobs.data ?? []).map((job) => (
                <li key={job.job_id}>
                  <StatusBadge status={job.status} /> {job.job_type} · {job.progress.stage ?? "—"} · created{" "}
                  {formatTimestamp(job.created_at)}
                  {job.progress.fraction != null
                    ? ` · stage ${job.progress.completed}/${job.progress.total}`
                    : ""}
                </li>
              ))}
            </ul>
          </section>
        </>
      ) : null}
    </article>
  );
}
