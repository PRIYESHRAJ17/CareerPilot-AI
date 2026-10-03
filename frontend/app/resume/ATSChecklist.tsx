import type { ResumeJobAnalysisResponse } from "@/lib/api";

export function ATSChecklist({
  result,
}: {
  result: ResumeJobAnalysisResponse | null;
}) {
  const items =
    result?.ats_analysis?.requirements ??
    result?.ats_analysis?.missing_requirements ??
    [];

  return (
    <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6 backdrop-blur">
      <div className="text-xs uppercase tracking-[0.18em] text-white/60">
        ATS Checklist & Keyword Requirements
      </div>

      <div className="mt-4 space-y-2.5">
        {items.length ? (
          items.map((item, index) => (
            <div
              key={`ats-${index}-${item.requirement ?? "item"}`}
              className="rounded-2xl border border-white/8 bg-white/[0.02] p-3.5 text-sm transition hover:border-white/15"
            >
              <div className="font-medium text-white/90">
                {item.requirement || "Requirement"}
              </div>
              <div className="mt-1 text-xs text-white/60">
                {item.status || item.importance || "Review"}
              </div>
            </div>
          ))
        ) : (
          <div className="rounded-2xl border border-dashed border-white/10 p-6 text-center text-sm text-white/50">
            Run a job-specific analysis to populate the ATS keyword checklist.
          </div>
        )}
      </div>
    </section>
  );
}
