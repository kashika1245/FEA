import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { cancelJob, createExperiment, getJobs, runExperiment } from "../api/endpoints";
import { ErrorBanner } from "../components/ErrorBanner";
import { StatusBadge } from "../components/StatusBadge";
import { formatTimestamp } from "../lib/format";
import { isTerminal } from "../lib/status";

export function JobsPage() {
  const client = useQueryClient();
  const jobs = useQuery({
    queryKey: ["jobs"],
    queryFn: () => getJobs(0, 50),
    refetchInterval: (query) => {
      const rows = query.state.data ?? [];
      return rows.some((job) => !isTerminal(job.status)) ? 2000 : false;
    },
  });
  const launch = useMutation({
    mutationFn: async () => {
      const suffix = new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 12);
      const experimentId = `paper-a.phase3.tiny-${suffix}`;
      await createExperiment(experimentId);
      return runExperiment(experimentId, "FULL_PHASE2_PIPELINE");
    },
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ["jobs"] });
      void client.invalidateQueries({ queryKey: ["experiments"] });
    },
  });
  return (
    <article>
      <p className="page-kicker">Execution</p>
      <h1 className="page-title">Job monitor</h1>
      <p className="lede">
        States come from SQLite via GET /api/v1/jobs. Progress is stage-based. A fabricated
        percentage is never shown. Launch creates a new <span className="mono">paper-a.phase3.tiny-*</span>{" "}
        experiment and runs the real Phase 2 engine with the tiny profile.
      </p>
      <button type="button" disabled={launch.isPending} onClick={() => launch.mutate()}>
        Launch tiny Phase 2 pipeline
      </button>
      <ErrorBanner error={jobs.error ?? launch.error} />
      {jobs.isLoading ? <div className="skeleton" style={{ height: 140, marginTop: 16 }} /> : null}
      {(jobs.data ?? []).length === 0 && !jobs.isLoading ? <p>No jobs have been recorded yet.</p> : null}
      <div className="grid" style={{ marginTop: 16 }}>
        {(jobs.data ?? []).map((job) => (
          <section className="card" key={job.job_id}>
            <div className="job-rail" aria-label="Lifecycle">
              {["queued", "running", job.status === "failed" ? "failed" : job.status === "cancelled" || job.status === "cancel_requested" ? job.status : "completed"].map(
                (step, index, arr) => (
                  <span key={step}>
                    {step}
                    {index < arr.length - 1 ? " → " : ""}
                  </span>
                ),
              )}
            </div>
            <p>
              <StatusBadge status={job.status} /> {job.job_type}
            </p>
            <p>
              Experiment <Link to={`/experiments/${job.experiment_id}`}>{job.experiment_id}</Link>
            </p>
            <p className="mono">{job.job_id}</p>
            <p>
              created {formatTimestamp(job.created_at)} · started {formatTimestamp(job.started_at)} ·
              finished {formatTimestamp(job.completed_at)}
            </p>
            <p>
              Stage {job.progress.stage ?? "—"}
              {job.progress.completed != null && job.progress.total
                ? ` (${job.progress.completed}/${job.progress.total} stages)`
                : ""}
            </p>
            {job.error_message ? <p>Failure: {job.error_code} — {job.error_message}</p> : null}
            {!isTerminal(job.status) ? (
              <button
                type="button"
                className="secondary"
                onClick={() =>
                  cancelJob(job.job_id).then(() => client.invalidateQueries({ queryKey: ["jobs"] }))
                }
              >
                Request cancel
              </button>
            ) : null}
          </section>
        ))}
      </div>
    </article>
  );
}
