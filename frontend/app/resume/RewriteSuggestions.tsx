"use client";

import { useState } from "react";
import { Check, Copy, Sparkles } from "lucide-react";
import type { ResumeJobAnalysisResponse, RewriteSuggestion } from "@/lib/api";

function StatusBadge({ status }: { status: RewriteSuggestion["evidence_status"] }) {
  const styles = {
    SUPPORTED: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
    PARTIAL: "border-amber-500/30 bg-amber-500/10 text-amber-300",
    UNSUPPORTED: "border-rose-500/30 bg-rose-500/10 text-rose-300",
  }[status] ?? "border-white/10 bg-white/5 text-white/70";

  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-[11px] font-medium ${styles}`}>
      {status}
    </span>
  );
}

export function RewriteSuggestions({
  result,
}: {
  result: ResumeJobAnalysisResponse | null;
}) {
  const suggestions = result?.rewrite_analysis?.suggestions ?? [];
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  function copyRewrite(text: string, index: number) {
    if (typeof window === "undefined") return;
    navigator.clipboard.writeText(text).then(() => {
      setCopiedIndex(index);
      setTimeout(() => setCopiedIndex(null), 2000);
    });
  }

  return (
    <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6 backdrop-blur">
      <div className="flex items-center justify-between border-b border-white/10 pb-4">
        <div>
          <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-white/60">
            <Sparkles size={14} className="text-cyan-400" />
            Evidence-Backed Rewrites
          </div>
          <p className="mt-1 text-xs text-white/60">
            Targeted enhancements aligned with job requirements while avoiding resume fabrication.
          </p>
        </div>

        {suggestions.length > 0 && (
          <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-white/70">
            {suggestions.length} suggestion{suggestions.length === 1 ? "" : "s"}
          </span>
        )}
      </div>

      <div className="mt-5 space-y-4">
        {suggestions.length > 0 ? (
          suggestions.map((item, index) => {
            const isCopied = copiedIndex === index;

            return (
              <div
                key={`rewrite-${index}-${item.section}`}
                className="rounded-2xl border border-white/10 bg-white/[0.02] p-5 transition hover:border-white/20"
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-white/90">
                      {item.section}
                    </span>
                    {item.target_requirement && (
                      <span className="text-xs text-white/60">
                        • Target: {item.target_requirement}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-3">
                    <StatusBadge status={item.evidence_status} />
                    <button
                      type="button"
                      aria-label={`Copy rewrite for ${item.section}`}
                      onClick={() => copyRewrite(item.suggested_rewrite, index)}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-white/70 transition hover:bg-white/10 hover:text-white"
                    >
                      {isCopied ? (
                        <>
                          <Check size={12} className="text-emerald-400" />
                          <span className="text-emerald-400">Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy size={12} />
                          <span>Copy</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {item.issue && (
                  <div className="mt-2 text-xs text-amber-300/80">
                    <span className="font-medium">Issue:</span> {item.issue}
                  </div>
                )}

                <div className="mt-4 grid gap-3 lg:grid-cols-2">
                  {item.source_text ? (
                    <div className="rounded-xl border border-rose-500/20 bg-rose-500/[0.03] p-3 text-xs leading-5">
                      <div className="mb-1 font-semibold uppercase tracking-wider text-rose-300/80">
                        Original Content
                      </div>
                      <p className="text-white/70">{item.source_text}</p>
                    </div>
                  ) : null}

                  <div
                    className={`rounded-xl border border-emerald-500/20 bg-emerald-500/[0.03] p-3 text-xs leading-5 ${
                      !item.source_text ? "lg:col-span-2" : ""
                    }`}
                  >
                    <div className="mb-1 flex items-center justify-between font-semibold uppercase tracking-wider text-emerald-300/80">
                      <span>Suggested Rewrite</span>
                      {item.confidence > 0 && (
                        <span className="text-[10px] text-white/50">
                          {Math.round(item.confidence * 100)}% confidence
                        </span>
                      )}
                    </div>
                    <p className="font-medium text-white/90">{item.suggested_rewrite}</p>
                  </div>
                </div>

                {item.available_evidence && item.available_evidence.length > 0 && (
                  <div className="mt-3 flex flex-wrap items-center gap-1.5">
                    <span className="text-[11px] text-white/50">Grounding:</span>
                    {item.available_evidence.map((ev, evIdx) => (
                      <span
                        key={evIdx}
                        className="rounded border border-white/8 bg-white/[0.03] px-1.5 py-0.5 text-[10px] text-white/60"
                      >
                        {ev}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })
        ) : (
          <div className="rounded-2xl border border-dashed border-white/10 p-8 text-center text-sm text-white/60">
            <p>Run a job-specific analysis above to generate evidence-backed rewrite candidates.</p>
            <p className="mt-1 text-xs text-white/50">
              Suggestions compare your resume against real job requirements with verifiable proof.
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
