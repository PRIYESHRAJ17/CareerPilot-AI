export type TelemetryEvent = { name: string; value?: number; route?: string; detail?: Record<string, string | number | boolean | null> };
export function reportTelemetry(event: TelemetryEvent) {
  if (typeof window === "undefined") return;
  const payload = JSON.stringify({ ...event, route: event.route ?? window.location.pathname, timestamp: new Date().toISOString() });
  try { navigator.sendBeacon?.("/api/telemetry", new Blob([payload], { type: "application/json" })); }
  catch { void fetch("/api/telemetry", { method: "POST", body: payload, headers: { "Content-Type": "application/json" }, keepalive: true }).catch(() => undefined); }
}
