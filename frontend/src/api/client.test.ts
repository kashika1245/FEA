import { describe, expect, it } from "vitest";
import { publicMessage, queryString } from "./client";

describe("api client helpers", () => {
  it("maps conflict and network errors without leaking internals", () => {
    expect(publicMessage(0, "NETWORK", "x")).toBe("Unable to connect to research API.");
    expect(publicMessage(404, "EXPERIMENT_NOT_FOUND", "x")).toBe("Experiment not found.");
    expect(publicMessage(409, "JOB_ALREADY_RUNNING", "x")).toBe(
      "This experiment already has an active run.",
    );
    expect(publicMessage(500, "INTERNAL_ERROR", "traceback")).toBe(
      "The research API reported an unexpected error.",
    );
  });

  it("omits empty query values", () => {
    expect(queryString({ a: "1", b: undefined, c: "" })).toBe("?a=1");
  });
});
