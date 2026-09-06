import { NOT_REACHED, RESPONSES, VARIABLES, type ThresholdRow } from "../api/types";
import { isReached } from "./format";

export type CrossingCell = {
  response: string;
  value: string | null;
  state: "reached" | "not_reached" | "missing";
};

export type CrossingOverviewRow = {
  variable: string;
  cells: CrossingCell[];
};

export function crossingOverview(
  rows: ThresholdRow[],
  field: "upper_5" | "lower_5" | "upper_10" | "lower_10",
  seed?: number,
): CrossingOverviewRow[] {
  const filtered = seed === undefined ? rows : rows.filter((row) => row.seed === seed);
  return VARIABLES.map((variable) => ({
    variable,
    cells: RESPONSES.map((response) => {
      const match = filtered.find((row) => row.variable === variable && row.response === response);
      if (!match) {
        return { response, value: null, state: "missing" };
      }
      const value = match[field];
      return {
        response,
        value,
        state: isReached(value) ? "reached" : "not_reached",
      };
    }),
  }));
}

export function crossingLabel(cell: CrossingCell): string {
  if (cell.state === "missing") return "No stored row";
  if (cell.state === "not_reached" || cell.value === NOT_REACHED) {
    return "Not reached";
  }
  return `δ=${cell.value}`;
}
