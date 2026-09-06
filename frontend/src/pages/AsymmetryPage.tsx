import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { getAsymmetry } from "../api/endpoints";
import { FROZEN_SEEDS, RESPONSES, VARIABLES } from "../api/types";
import { ErrorBanner } from "../components/ErrorBanner";
import { ExperimentPicker } from "../components/ExperimentPicker";
import { useExperimentId } from "../lib/experiment";
import { ProfileChart } from "../components/ProfileChart";
import { formatPercent } from "../lib/format";

export function AsymmetryPage() {
  const [experimentId] = useExperimentId();
  const [variable, setVariable] = useState("A3");
  const [output, setOutput] = useState("sigma_max");
  const [seed, setSeed] = useState(20260905);
  const data = useQuery({
    queryKey: ["asymmetry", experimentId, variable, output, seed],
    queryFn: () => getAsymmetry({ experimentId, variable, output, seed, limit: 200 }),
  });
  const lower = useMemo(
    () =>
      (data.data?.rows ?? []).map((row) => ({
        delta: row.delta,
        median: row.lower_median_relative_error_pct,
        q1: row.lower_median_relative_error_pct,
        q3: row.lower_median_relative_error_pct,
        seed: row.seed,
      })),
    [data.data],
  );
  const upper = useMemo(
    () =>
      (data.data?.rows ?? []).map((row) => ({
        delta: row.delta,
        median: row.upper_median_relative_error_pct,
        q1: row.upper_median_relative_error_pct,
        q3: row.upper_median_relative_error_pct,
        seed: row.seed,
      })),
    [data.data],
  );
  return (
    <article>
      <p className="page-kicker">Direction</p>
      <h1 className="page-title">Lower versus upper asymmetry</h1>
      <p className="lede">
        Lower and upper extrapolation are evaluated independently relative to the training-domain
        boundary. The plotted values are stored API fields, not a browser-side recomputation of
        thresholds.
      </p>
      <div className="filters">
        <ExperimentPicker />
        <label className="field">
          Variable
          <select value={variable} onChange={(e) => setVariable(e.target.value)}>
            {VARIABLES.map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </label>
        <label className="field">
          Response
          <select value={output} onChange={(e) => setOutput(e.target.value)}>
            {RESPONSES.map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </label>
        <label className="field">
          Seed
          <select value={seed} onChange={(e) => setSeed(Number(e.target.value))}>
            {FROZEN_SEEDS.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
      </div>
      <ErrorBanner error={data.error} />
      {!data.isLoading && !(data.data?.rows.length) ? <p>No asymmetry rows for these filters.</p> : null}
      <ProfileChart
        title={`${variable} / ${output} lower vs upper`}
        yLabel="Median relative error (%)"
        lower={[...lower].sort((a, b) => a.delta - b.delta)}
        upper={[...upper].sort((a, b) => a.delta - b.delta)}
        compare
        showIqrBand={false}
      />
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>δ</th>
              <th>Lower median RE</th>
              <th>Upper median RE</th>
              <th>Upper − lower</th>
            </tr>
          </thead>
          <tbody>
            {(data.data?.rows ?? []).map((row) => (
              <tr key={`${row.delta}-${row.seed}`}>
                <td>{row.delta.toFixed(2)}</td>
                <td>{formatPercent(row.lower_median_relative_error_pct)}</td>
                <td>{formatPercent(row.upper_median_relative_error_pct)}</td>
                <td>{formatPercent(row.upper_minus_lower_median_relative_error_pct)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </article>
  );
}
