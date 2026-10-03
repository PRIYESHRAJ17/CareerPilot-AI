const MAX_BODY = 16 * 1024;
export async function POST(request: Request) {
  const text = (await request.text()).slice(0, MAX_BODY);
  let body: unknown = null; try { body = JSON.parse(text); } catch { body = { raw: text }; }
  // Production deployments should forward this normalized payload to Sentry/Datadog/PagerDuty.
  console.warn("careerpilot.telemetry", body);
  return Response.json({ accepted: true }, { status: 202, headers: { "Cache-Control": "no-store" } });
}
