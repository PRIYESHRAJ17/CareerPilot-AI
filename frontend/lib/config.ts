
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

export const DEFAULT_REQUEST_TIMEOUT_MS = 20_000;
export const RESUME_REQUEST_TIMEOUT_MS = 30_000;
export const MAX_RESUME_BYTES = 10 * 1024 * 1024;

export function isValidHttpUrl(value: unknown): value is string {
  if (typeof value !== "string" || !value.trim()) return false;
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

export function clampScore(value: unknown, min = 0, max = 100): number {
  const numeric = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(numeric)) return min;
  return Math.min(max, Math.max(min, numeric));
}

export function normalizeConfidence(value: unknown): number {
  const numeric = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(numeric)) return 0;
  return Math.round(numeric >= 0 && numeric <= 1 ? numeric * 100 : clampScore(numeric));
}

export function friendlyStatus(value: unknown, loading = false): string {
  if (loading) return "Orchestrating agents...";
  if (typeof value !== "string" || !value) return "System ready";
  const labels: Record<string, string> = {
    PENDING: "Queued",
    DISPATCHED: "Dispatching agents",
    AGENT_EXECUTION: "Agents working",
    VALIDATING: "Validating evidence",
    COMPLETED: "Analysis complete",
    PARTIAL: "Partial result",
    FAILED: "Workflow failed",
  };
  return labels[value] ?? value.replaceAll("_", " ").toLowerCase();
}
