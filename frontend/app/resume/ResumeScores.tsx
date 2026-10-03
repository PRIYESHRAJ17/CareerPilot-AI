"use client";

import { useState } from "react";
import type { ResumeAnalysisResponse } from "@/lib/api";
import { clampScore } from "@/lib/config";

export function ResumeScores({
  result,
}: {
  result: ResumeAnalysisResponse;
}) {
  const [expandedExperience, setExpandedExperience] = useState<number | null>(null);

  const score = clampScore(result.intelligence.overall_score);

  return (
    <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6 backdrop-blur">
      <div className="text-xs uppercase tracking-[0.18em] text-white/60">
        Resume Intelligence Scores
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-2 md:grid-cols-4">
        <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-4">
          <div className="text-xs text-white/60">Overall Readiness</div>
          <div className="mt-2 text-3xl font-semibold text-white">{score}%</div>
        </div>

        {(result.intelligence.section_scores ?? []).slice(0, 3).map((item) => (
          <div key={item.section} className="rounded-2xl border border-white/10 bg-white/[0.02] p-4">
            <div className="text-xs text-white/60">{item.section}</div>
            <div className="mt-2 text-3xl font-semibold text-white">
              {clampScore(item.score)}%
            </div>
          </div>
        ))}
      </div>

      {result.resume.experience.length > 0 && (
        <div className="mt-6 border-t border-white/10 pt-5">
          <div className="text-xs uppercase tracking-[0.16em] text-white/60">
            Work Experience Evidence ({result.resume.experience.length})
          </div>

          <div className="mt-3 space-y-2.5">
            {result.resume.experience.map((item, index) => (
              <button
                key={`experience-${index}`}
                type="button"
                aria-expanded={expandedExperience === index}
                onClick={() =>
                  setExpandedExperience(expandedExperience === index ? null : index)
                }
                className="w-full rounded-2xl border border-white/8 bg-white/[0.02] p-4 text-left transition hover:border-white/15"
              >
                <div className="flex items-center justify-between">
                  <div className="font-semibold text-white/90">
                    {item.job_title || "Experience"}
                  </div>
                  <span className="text-xs text-cyan-400">
                    {expandedExperience === index ? "Collapse" : "Expand"}
                  </span>
                </div>

                <div className="mt-1 text-xs text-white/60">
                  {item.company || "Company not specified"}
                </div>

                {expandedExperience === index && (
                  <p className="mt-3 text-sm leading-6 text-white/70">
                    {item.description ||
                      item.achievements?.join(" ") ||
                      "No additional evidence recorded."}
                  </p>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
