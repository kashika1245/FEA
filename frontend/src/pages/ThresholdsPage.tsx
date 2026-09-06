import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { getThresholds } from "../api/endpoints";
import { RESPONSES, VARIABLES } from "../api/types";
import { ErrorBanner } from "../components/ErrorBanner";
import { ExperimentPicker } from "../components/ExperimentPicker";
import { useExperimentId } from "../lib/experiment";
import { formatCrossing, isReached } from "../lib/format";

export function ThresholdsPage() {
  const [experimentId] = useExperimentId();
  const [variable, setVariable] = useState("");
  const [output, setOutput] = useState("");
  const thresholds = useQuery({
    queryKey: ["thresholds", experimentId, variable, output],
    queryFn: () =>
      getThresholds({
        experimentId,
        variable: variable || undefined,
        output: output || undefined,
        limit: 200,
      }),
  });
  return (
    <article>
      <p className="page-kicker">Empirical crossings</p>
      <h1 className="page-title">Threshold analysis</h1>
      <p className="lede">
        Values are first observed δ on the discrete grid where median relative error meets 5% or
        10%. They are not a continuous validity boundary. “Not reached within tested range” is
        distinct from 0.50 and from infinity.
      </p>
      <div className="filters">
        <ExperimentPicker />
        <label className="field">
          Variable
          <select value={variable} onChange={(e) => setVariable(e.target.value)}>
            <option value="">All</option>
            {VARIABLES.map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </label>
        <label className="field">
          Response
          <select value={output} onChange={(e) => setOutput(e.target.value)}>
            <option value="">All</option>
            {RESPONSES.map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </label>
      </div>
      <ErrorBanner error={thresholds.error} />
      {thresholds.isLoading ? <div className="skeleton" style={{ height: 200, marginTop: 16 }} /> : null}
      {!thresholds.isLoading && !(thresholds.data?.rows.length) ? (
        <p>No threshold crossing was observed / stored for these filters.</p>
      ) : null}
      <div className="table-wrap" style={{ marginTop: 16 }}>
        <table>
          <thead>
            <tr>
              <th>Variable</th>
              <th>Response</th>
              <th>Seed</th>
              <th>Lower 5%</th>
              <th>Upper 5%</th>
              <th>Lower 10%</th>
              <th>Upper 10%</th>
            </tr>
          </thead>
          <tbody>
            {(thresholds.data?.rows ?? []).map((row, index) => (
              <tr key={`${row.variable}-${row.response}-${row.seed}-${index}`}>
                <td>{row.variable}</td>
                <td>{row.response}</td>
                <td>{row.seed}</td>
                <CrossingCell value={row.lower_5} />
                <CrossingCell value={row.upper_5} />
                <CrossingCell value={row.lower_10} />
                <CrossingCell value={row.upper_10} />
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="provenance">{formatCrossing("0.25")} · Source: GET /api/v1/research/thresholds</p>
    </article>
  );
}

function CrossingCell({ value }: { value: string }) {
  return (
    <td>
      {isReached(value) ? (
        <span>
          δ = {value} <span className="sr-only">reached</span>
        </span>
      ) : (
        <span>
          Not reached <span className="sr-only">within tested range</span>
        </span>
      )}
    </td>
  );
}
