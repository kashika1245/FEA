import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { getProfiles, getThresholds } from "../api/endpoints";
import { DIRECTIONS, FROZEN_SEEDS, RESPONSES, VARIABLES } from "../api/types";
import { ErrorBanner } from "../components/ErrorBanner";
import { ExperimentPicker } from "../components/ExperimentPicker";
import { useExperimentId } from "../lib/experiment";
import { ProfileChart } from "../components/ProfileChart";
import { formatCrossing } from "../lib/format";
import { metricLabel, seriesFor, type ProfileMetric } from "../lib/profiles";
import { crossingLabel, crossingOverview } from "../lib/thresholds";

export function ProfilesPage() {
  const [experimentId] = useExperimentId();
  const [variable, setVariable] = useState("A3");
  const [output, setOutput] = useState("sigma_max");
  const [seed, setSeed] = useState(20260905);
  const [metric, setMetric] = useState<ProfileMetric>("median_relative_error_pct");
  const [compare, setCompare] = useState(true);
  const profiles = useQuery({
    queryKey: ["profiles", experimentId, variable, output, seed],
    queryFn: () => getProfiles({ experimentId, variable, output, seed, limit: 200 }),
  });
  const thresholds = useQuery({
    queryKey: ["thresholds", experimentId, seed],
    queryFn: () => getThresholds({ experimentId, seed, limit: 200 }),
  });
  const lower = useMemo(
    () => seriesFor(profiles.data?.rows ?? [], "lower", metric, seed),
    [profiles.data, metric, seed],
  );
  const upper = useMemo(
    () => seriesFor(profiles.data?.rows ?? [], "upper", metric, seed),
    [profiles.data, metric, seed],
  );
  const matrix = useMemo(
    () => crossingOverview(thresholds.data?.rows ?? [], "upper_5", seed),
    [thresholds.data, seed],
  );
  return (
    <article>
      <p className="page-kicker">Primary result</p>
      <h1 className="page-title">Variable-wise extrapolation profiles</h1>
      <p className="lede">
        Prediction error versus controlled extrapolation distance δ. Points are stored Phase 2
        medians. The polyline connects observed grid values only; it is not a fitted curve.
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
        <label className="field">
          Metric
          <select value={metric} onChange={(e) => setMetric(e.target.value as ProfileMetric)}>
            <option value="median_relative_error_pct">Median relative error</option>
            <option value="median_absolute_error">Median absolute error</option>
            <option value="median_signed_error">Median signed error</option>
          </select>
        </label>
        <label className="field">
          Compare directions
          <select value={compare ? "yes" : "no"} onChange={(e) => setCompare(e.target.value === "yes")}>
            <option value="yes">Lower and upper</option>
            <option value="no">Lower only</option>
          </select>
        </label>
      </div>
      {profiles.isLoading ? <div className="skeleton" style={{ height: 320, marginTop: 16 }} /> : null}
      <ErrorBanner error={profiles.error} />
      {!profiles.isLoading && !(profiles.data?.rows.length) ? (
        <p>No profile rows for these filters. The experiment may still be running or unused.</p>
      ) : null}
      <ProfileChart
        title={`${variable} / ${output} / seed ${seed}`}
        yLabel={metricLabel(metric)}
        lower={lower}
        upper={upper}
        compare={compare}
        showIqrBand={metric === "median_relative_error_pct" && !compare}
      />
      <section className="card">
        <h2>5% upper crossing overview</h2>
        <p>
          First observed δ at which median relative error reaches 5% (upper) for seed {seed}.
          “Not reached” is stored in the artefact. “No stored row” means this page has no matching
          threshold record — it is not a scientific crossing.
        </p>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Variable</th>
                {RESPONSES.map((response) => (
                  <th key={response}>{response}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {matrix.map((row) => (
                <tr key={row.variable}>
                  <td>{row.variable}</td>
                  {row.cells.map((cell) => (
                    <td key={cell.response}>{crossingLabel(cell)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="provenance">
          {DIRECTIONS.join(" / ")} crossings are empirical grid events. {formatCrossing("0.25")}
        </p>
      </section>
    </article>
  );
}
