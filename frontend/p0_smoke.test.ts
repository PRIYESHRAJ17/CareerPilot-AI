import { describe, expect, it } from "vitest";
import {
  clampScore,
  normalizeConfidence,
} from "./lib/config";

describe("P0 frontend foundations", () => {
  it("clamps scores", () => {
    expect(clampScore(130)).toBe(100);
    expect(clampScore(-2)).toBe(0);
  });

  it("normalizes confidence", () => {
    expect(normalizeConfidence(0.82)).toBe(82);
    expect(normalizeConfidence(82)).toBe(82);
  });
});
