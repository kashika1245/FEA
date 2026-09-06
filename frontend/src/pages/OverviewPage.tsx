import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getResearchSummary } from "../api/endpoints";
import { ErrorBanner } from "../components/ErrorBanner";
import { DEFAULT_EXPERIMENT } from "../lib/experiment";
import { formatHash, formatNumber } from "../lib/format";

export function OverviewPage() {
  const summary = useQuery({
    queryKey: ["summary", DEFAULT_EXPERIMENT],
    queryFn: () => getResearchSummary(DEFAULT_EXPERIMENT),
  });
  const manifest = summary.data?.manifest ?? {};
  return (
    <article>
      <p className="page-kicker">Paper A</p>
      <h1 className="page-title">How far can a structural surrogate be trusted?</h1>
      <p className="lede">
        Variable-wise extrapolation profiles for truss response models. This observatory reads
        stored Phase 2 artefacts through the Phase 3 API. It does not recompute FEM or MLP
        inference in the browser.
      </p>
      {summary.isLoading ? <div className="skeleton" style={{ height: 120 }} /> : null}
      <ErrorBanner error={summary.error} />
      <section className="grid grid-3" style={{ marginTop: "1.5rem" }}>
        <div className="card">
          <h2>Benchmark</h2>
          <p>Canonical 10-bar planar truss. Linear-elastic direct-stiffness FEM oracle.</p>
          <p className="mono">{String(manifest.geometry_version ?? "tenbar.cantilever.v1")}</p>
        </div>
        <div className="card">
          <h2>Surrogate</h2>
          <p>MLP 12→128→128→128→3, ReLU, MSE, Adam. Train-only z-score I/O.</p>
          <p>{Array.isArray(manifest.seeds) ? `${manifest.seeds.length} retained seeds` : "Seeds from API"}</p>
        </div>
        <div className="card">
          <h2>Frozen experiment</h2>
          <p className="mono">{summary.data?.experiment_id ?? DEFAULT_EXPERIMENT}</p>
          <p>Status {summary.data?.status ?? "—"}</p>
        </div>
      </section>
      <section className="card" style={{ marginTop: "1rem" }}>
        <h2>Provenance from stored artefacts</h2>
        <table>
          <tbody>
            <tr>
              <th>Dataset hash</th>
              <td className="mono">{formatHash(summary.data?.dataset_hash)}</td>
            </tr>
            <tr>
              <th>Normalization hash</th>
              <td className="mono">{formatHash(summary.data?.normalization_hash)}</td>
            </tr>
            <tr>
              <th>Variable-wise observations</th>
              <td>{formatNumber(summary.data?.variable_wise_rows, 0)}</td>
            </tr>
            <tr>
              <th>Combined A3+F observations</th>
              <td>{formatNumber(summary.data?.combined_rows, 0)}</td>
            </tr>
            <tr>
              <th>Profile rows</th>
              <td>{formatNumber(summary.data?.profile_rows, 0)}</td>
            </tr>
          </tbody>
        </table>
        <p className="provenance">
          FEM → Phase 1 · Surrogate/profiles → Phase 2 · API → Phase 3 · This view → Phase 4
        </p>
        <p>
          <Link to="/profiles">Open extrapolation profiles</Link> ·{" "}
          <Link to="/methodology">Read methodology</Link>
        </p>
      </section>
    </article>
  );
}
