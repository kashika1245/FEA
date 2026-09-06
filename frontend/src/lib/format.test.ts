import { describe, expect, it } from "vitest";
import { crossingSortValue, formatCrossing, formatHash, isReached, responseUnit, variableUnit } from "./format";

describe("format helpers", () => {
  it("shortens hashes without inventing them", () => {
    const hash = "a78de261b1686363ed6d830cd370b763800da657bce0991047fe43fb9504e99e";
    expect(formatHash(hash)).toContain("a78de261b1");
    expect(formatHash(hash)).not.toBe(hash);
  });

  it("does not treat not-reached as zero", () => {
    expect(isReached("not reached")).toBe(false);
    expect(isReached("0.25")).toBe(true);
    expect(crossingSortValue("not reached")).toBe(Number.POSITIVE_INFINITY);
    expect(formatCrossing("not reached")).toBe("Not reached within tested range");
    expect(formatCrossing("0.25")).toContain("grid crossing");
  });

  it("keeps display units explicit", () => {
    expect(variableUnit("E")).toBe("GPa");
    expect(variableUnit("F")).toBe("kN");
    expect(responseUnit("sigma_max")).toBe("N/mm²");
  });
});
