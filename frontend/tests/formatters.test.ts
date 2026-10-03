import { describe, expect, it } from "vitest";
import { formatCurrency, formatDateTime, formatRelativeTime } from "../lib/formatters";

describe("formatters", () => {
  it("handles currency edges and locale-aware formatting", () => {
    expect(formatCurrency(null)).toBe("Undisclosed");
    expect(formatCurrency(undefined)).toBe("Undisclosed");
    expect(formatCurrency("   ")).toBe("Undisclosed");
    expect(formatCurrency(-10)).toContain("10");
    expect(formatCurrency(100000)).toBe("₹1,00,000");
    expect(formatCurrency(100000, "USD", "en-US")).toBe("$100,000");
  });
  it("formats dates safely", () => {
    expect(formatDateTime("not-a-date")).toBe("—");
    expect(formatDateTime("2026-01-01T00:00:00Z")).not.toBe("—");
  });
  it("formats relative dates", () => {
    expect(formatRelativeTime(null)).toBe("—");
    expect(formatRelativeTime(new Date())).toMatch(/now|second|minute|hour|day/);
  });
});
