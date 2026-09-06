import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { getCombined } from "../api/endpoints";
import { DIRECTIONS, FROZEN_SEEDS, RESPONSES } from "../api/types";
import { ErrorBanner } from "../components/ErrorBanner";
import { ExperimentPicker } from "../components/ExperimentPicker";
import { useExperimentId } from "../lib/experiment";
import { Heatmap } from "../components/Heatmap";

export function CombinedPage() {
  const [experimentId] = useExperimentId();
  const [output, setOutput] = useState("sigma_max");
  const [directionA3, setDirectionA3] = useState("upper");
  const [directionF, setDirectionF] = useState("upper");
  const [seed, setSeed] = useState(20260905);
  const data = useQuery({
    queryKey: ["combined", experimentId, output, directionA3, directionF, seed],
    queryFn: () =>
      getCombined({ experimentId, output, directionA3, directionF, seed }),
  });
  return (
    <article>
      <p className="page-kicker">Two-variable probe</p>
      <h1 className="page-title">Combined A3 + F extrapolation</h1>
      <p className="lede">
        One-dimensional profiles do not define a full multidimensional validity domain. This grid
        is the median of stored combined-observation relative errors at each (δ_A3, δ_F) node.
      </p>
      <div className="filters">
        <ExperimentPicker />
        <label className="field">
          Response
          <select value={output} onChange={(e) => setOutput(e.target.value)}>
            {RESPONSES.map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </label>
        <label className="field">
          A3 direction
          <select value={directionA3} onChange={(e) => setDirectionA3(e.target.value)}>
            {DIRECTIONS.map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </label>
        <label className="field">
          F direction
          <select value={directionF} onChange={(e) => setDirectionF(e.target.value)}>
            {DIRECTIONS.map((item) => (
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
      {data.isLoading ? <div className="skeleton" style={{ height: 360, marginTop: 16 }} /> : null}
      {!data.isLoading && !(data.data?.cells.length) ? (
        <p>No combined grid is stored for this experiment (tiny pilots skip combined).</p>
      ) : null}
      {data.data?.cells.length ? (
        <Heatmap
          cells={data.data.cells}
          title={`A3 ${directionA3} · F ${directionF} · ${output} · seed ${seed}`}
        />
      ) : null}
    </article>
  );
}
