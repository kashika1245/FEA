import { useQuery } from "@tanstack/react-query";
import { getInterpolation } from "../api/endpoints";
import { ErrorBanner } from "../components/ErrorBanner";
import { ExperimentPicker } from "../components/ExperimentPicker";
import { useExperimentId } from "../lib/experiment";
import { StatusBadge } from "../components/StatusBadge";
import { formatNumber, formatPercent, responseUnit } from "../lib/format";

export function InterpolationPage() {
  const [experimentId] = useExperimentId();
  const data = useQuery({
    queryKey: ["interpolation", experimentId],
    queryFn: () => getInterpolation(experimentId),
  });
  return (
    <article>
      <p className="page-kicker">Competence</p>
      <h1 className="page-title">Interpolation and model information</h1>
      <p className="lede">
        Metrics are stored seed JSON from GET /api/v1/research/interpolation. Raw FEM-versus-MLP
        pairs are not provided by the API, so no synthetic scatter plot is drawn.
      </p>
      <ExperimentPicker />
      <ErrorBanner error={data.error} />
      <section className="card" style={{ marginTop: 16 }}>
        <h2>Frozen architecture</h2>
        <p>Input 12 · Hidden 128→128→128 · ReLU · Output 3 · Loss MSE · Optimizer Adam</p>
        <p>The architecture is the predetermined Phase 2 baseline, not a claimed novelty.</p>
      </section>
      {data.isLoading ? <div className="skeleton" style={{ height: 180, marginTop: 16 }} /> : null}
      {!data.isLoading && !(data.data?.seeds.length) ? <p>No interpolation results are stored.</p> : null}
      {(data.data?.seeds ?? []).map((seed) => (
        <section className="card" key={seed.seed} style={{ marginTop: 12 }}>
          <h2>
            Seed {seed.seed} <StatusBadge status={seed.passed_gate ? "completed" : "failed"} />
          </h2>
          <p className="mono">{seed.model_id}</p>
          {seed.gate_notes?.length ? <p>Gate notes: {seed.gate_notes.join("; ")}</p> : <p>Competence gate passed.</p>}
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Response</th>
                  <th>MAE</th>
                  <th>RMSE</th>
                  <th>Median RE</th>
                  <th>R²</th>
                  <th>Mean signed</th>
                  <th>n</th>
                </tr>
              </thead>
              <tbody>
                {seed.metrics.map((metric) => (
                  <tr key={metric.response}>
                    <td>
                      {metric.response} ({responseUnit(metric.response)})
                    </td>
                    <td>{formatNumber(metric.mae)}</td>
                    <td>{formatNumber(metric.rmse)}</td>
                    <td>{formatPercent(metric.median_relative_error_pct)}</td>
                    <td>{formatNumber(metric.r2, 6)}</td>
                    <td>{formatNumber(metric.mean_signed_error)}</td>
                    <td>{metric.n}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ))}
    </article>
  );
}
