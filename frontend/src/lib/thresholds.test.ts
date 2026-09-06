import { describe, expect, it } from "vitest";
import type { ThresholdRow } from "../api/types";
import { crossingLabel, crossingOverview } from "./thresholds";

const row = (variable: string, response: string, upper_5: string): ThresholdRow => ({
  model_id: "m",
  seed: 20260905,
  variable,
  response,
  lower_5: "not reached",
  upper_5,
  lower_10: "not reached",
  upper_10: "not reached",
});

describe("crossingOverview", () => {
  it("does not treat a missing variable/response as not reached", () => {
    const matrix = crossingOverview([row("A3", "sigma_max", "0.15")], "upper_5", 20260905);
    const a3 = matrix.find((item) => item.variable === "A3");
    const a1 = matrix.find((item) => item.variable === "A1");
    expect(a3?.cells.find((cell) => cell.response === "sigma_max")?.state).toBe("reached");
    expect(a3?.cells.find((cell) => cell.response === "u_max")?.state).toBe("missing");
    expect(a1?.cells.every((cell) => cell.state === "missing")).toBe(true);
    expect(crossingLabel({ response: "u_max", value: null, state: "missing" })).toBe("No stored row");
    expect(crossingLabel({ response: "u_max", value: "not reached", state: "not_reached" })).toBe(
      "Not reached",
    );
  });
});
