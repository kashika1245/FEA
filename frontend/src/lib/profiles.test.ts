import { describe, expect, it } from "vitest";
import type { ProfileRow } from "../api/types";
import { seriesFor } from "./profiles";

const row = (delta: number, direction: string): ProfileRow => ({
  model_id: "m",
  seed: 1,
  variable: "A3",
  direction,
  delta,
  response: "sigma_max",
  n_anchors: 2,
  q1_relative_error_pct: 1,
  median_relative_error_pct: 2 + delta,
  q3_relative_error_pct: 3,
  mean_relative_error_pct: 2,
  median_absolute_error: 0.1,
  rmse: 0.2,
  mean_signed_error: 0,
  median_signed_error: 0,
  max_relative_error_pct: 4,
  primary_metric: "median_relative_error_pct",
});

describe("seriesFor", () => {
  it("uses stored medians in delta order without smoothing", () => {
    const series = seriesFor([row(0.2, "lower"), row(0.0, "lower"), row(0.1, "upper")], "lower", "median_relative_error_pct", 1);
    expect(series.map((p) => p.delta)).toEqual([0, 0.2]);
    expect(series[0].median).toBe(2);
    expect(series[1].median).toBe(2.2);
  });
});
