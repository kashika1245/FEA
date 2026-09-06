import type { ProfileRow } from "../api/types";

export type ProfileMetric =
  | "median_relative_error_pct"
  | "median_absolute_error"
  | "median_signed_error";

export interface SeriesPoint {
  delta: number;
  median: number;
  q1: number;
  q3: number;
  seed: number;
}

export function metricLabel(metric: ProfileMetric): string {
  if (metric === "median_relative_error_pct") return "Median relative error (%)";
  if (metric === "median_absolute_error") return "Median absolute error";
  return "Median signed error";
}

export function seriesFor(
  rows: ProfileRow[],
  direction: string,
  metric: ProfileMetric,
  seed?: number,
): SeriesPoint[] {
  return rows
    .filter((row) => row.direction === direction && (seed === undefined || row.seed === seed))
    .map((row) => ({
      delta: Number(row.delta),
      median: Number(row[metric]),
      q1: Number(row.q1_relative_error_pct),
      q3: Number(row.q3_relative_error_pct),
      seed: Number(row.seed),
    }))
    .sort((a, b) => a.delta - b.delta || a.seed - b.seed);
}
