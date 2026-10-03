"use client";

import dynamic from "next/dynamic";
import { ChevronDown } from "lucide-react";
import { useState } from "react";
import {
  analyzeResume,
  type ResumeAnalysisResponse,
  type ResumeJobAnalysisResponse,
} from "@/lib/api";
import { ResumeUpload } from "./ResumeUpload";
import { ResumeScores } from "./ResumeScores";

const ATSChecklist =
  dynamic(() =>
    import("./ATSChecklist").then(
      (module) =>
        module.ATSChecklist,
    ),
  );

const JobMatcher =
  dynamic(() =>
    import("./JobMatcher").then(
      (module) =>
        module.JobMatcher,
    ),
  );

const RewriteSuggestions =
  dynamic(() =>
    import("./RewriteSuggestions").then(
      (module) =>
        module.RewriteSuggestions,
    ),
  );

type JobView =
  | "overview"
  | "requirements"
  | "rewrite"
  | "ai";

export default function ResumeClient() {
  const [
    file,
    setFile,
  ] = useState<File | null>(
    null,
  );

  const [
    resumeResult,
    setResumeResult,
  ] = useState<ResumeAnalysisResponse | null>(
    null,
  );

  const [
    jobResult,
    setJobResult,
  ] = useState<ResumeJobAnalysisResponse | null>(
    null,
  );

  const [
    activeView,
    setActiveView,
  ] = useState<JobView>(
    "overview",
  );

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState("");

  const [
    expandedExperience,
    setExpandedExperience,
  ] = useState<number | null>(null);


  async function runResumeAnalysis() {
    if (!file) {
      setError(
        "Please choose a resume first.",
      );
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response =
        await analyzeResume(
          file,
        );

      setResumeResult(
        response,
      );
      setJobResult(null);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to analyze the resume.",
      );
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setExpandedExperience(null);
    setFile(null);
    setResumeResult(null);
    setJobResult(null);
    setActiveView(
      "overview",
    );
    setError("");
    setLoading(false);
  }

  return (
    <main className="min-h-screen bg-[#080a0f] p-5 text-white md:p-8">
      <div className="mx-auto max-w-7xl">
        <header className="border-b border-white/10 pb-7">
          <div className="text-[10px] uppercase tracking-[0.2em] text-white/60">
            CareerPilot Intelligence
          </div>

          <h1 className="mt-3 text-4xl font-semibold">
            Resume Intelligence
          </h1>

          <p className="mt-3 max-w-2xl text-sm leading-6 text-white/70">
            Parse resume evidence, measure quality, compare against a target job,
            and produce evidence-backed rewrite suggestions.
          </p>
        </header>

        <div className="mt-6 grid gap-6 lg:grid-cols-[360px_1fr]">
          <div className="space-y-4">
            <ResumeUpload
              file={file}
              onSelect={(selected) => {
                setFile(selected);
                setResumeResult(null);
                setJobResult(null);
                setError("");
              }}
              onError={setError}
            />

            {error && (
              <div className="rounded-2xl border border-red-400/15 bg-red-400/[0.04] p-4 text-sm text-red-100/80">
                {error}
              </div>
            )}

            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                disabled={
                  loading ||
                  !file
                }
                onClick={() =>
                  void runResumeAnalysis()
                }
                className="rounded-xl bg-white px-4 py-2.5 text-xs font-semibold text-black disabled:opacity-50"
              >
                {loading
                  ? "Analyzing..."
                  : "Analyze resume"}
              </button>

              <button
                type="button"
                onClick={reset}
                className="rounded-xl border border-white/10 px-4 py-2.5 text-xs text-white/70 transition hover:bg-white/5"
              >
                Reset
              </button>
            </div>
          </div>

          <div className="space-y-5">
            {resumeResult ? (
              <>
                <ResumeScores
                  result={
                    resumeResult
                  }
                />

                <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6 backdrop-blur">
                  <div className="text-xs uppercase tracking-[0.18em] text-white/60">Experience</div>
                  <div className="mt-4 space-y-2">
                    {(resumeResult.resume.experience ?? []).length === 0 ? (
                      <p className="text-sm text-white/50">No experience entries were detected.</p>
                    ) : (
                      resumeResult.resume.experience.map((experience, index) => {
                        const expanded = expandedExperience === index;
                        return (
                          <div key={`${experience.job_title ?? "role"}-${experience.company ?? "company"}-${index}`} className="rounded-2xl border border-white/10">
                            <button
                              type="button"
                              className="flex w-full items-center justify-between gap-4 p-4 text-left"
                              aria-expanded={expanded}
                              aria-controls={`resume-experience-${index}`}
                              onClick={() => setExpandedExperience(expanded ? null : index)}
                            >
                              <span className="min-w-0">
                                <span className="block text-sm font-medium text-white/90">{experience.job_title || "Role not detected"}</span>
                                <span className="mt-1 block text-xs text-white/60">{experience.company || "Company not detected"}</span>
                              </span>
                              <ChevronDown className={`h-4 w-4 shrink-0 text-white/60 transition ${expanded ? "rotate-180" : ""}`} />
                            </button>
                            {expanded && (
                              <div id={`resume-experience-${index}`} className="border-t border-white/10 px-4 pb-4 pt-3">
                                {experience.description && <p className="whitespace-pre-line text-sm leading-6 text-white/70">{experience.description}</p>}
                                {(experience.achievements ?? []).length > 0 && (
                                  <div className="mt-3 space-y-1">
                                    {(experience.achievements ?? []).map((item) => <p key={item} className="text-sm leading-6 text-white/70">{item}</p>)}
                                  </div>
                                )}
                                {(experience.technologies ?? []).length > 0 && (
                                  <div className="mt-3 flex flex-wrap gap-2">
                                    {(experience.technologies ?? []).map((technology) => <span key={technology} className="rounded-full bg-white/[0.05] px-2.5 py-1 text-[11px] text-white/70">{technology}</span>)}
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })
                    )}
                  </div>
                </section>

                <div className="sr-only" aria-live="polite">{loading ? "Analyzing resume..." : resumeResult ? "Resume analysis ready." : ""}</div>

                <div
                  role="tablist"
                  aria-label="Resume intelligence panels"
                  className="flex flex-wrap gap-2"
                >
                  {(
                    [
                      [
                        "overview",
                        "Overview",
                      ],
                      [
                        "requirements",
                        "ATS",
                      ],
                      [
                        "rewrite",
                        "Rewrite",
                      ],
                      [
                        "ai",
                        "Job match",
                      ],
                    ] as const
                  ).map(
                    ([id, label]) => (
                      <button
                        key={id}
                        type="button"
                        role="tab"
                        aria-selected={
                          activeView ===
                          id
                        }
                        onClick={() =>
                          setActiveView(
                            id,
                          )
                        }
                        className={[
                          "min-h-11 rounded-xl border px-3 py-2 text-xs",
                          activeView ===
                          id
                            ? "border-white/20 bg-white text-black"
                            : "border-white/10 text-white/55",
                        ].join(" ")}
                      >
                        {label}
                      </button>
                    ),
                  )}
                </div>

                {activeView ===
                  "overview" && (
                  <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6 backdrop-blur">
                    <div className="text-xs uppercase tracking-[0.18em] text-white/60">
                      Strengths
                    </div>

                    <div className="mt-4 space-y-2">
                      {(
                        resumeResult
                          .intelligence
                          .strengths ??
                        []
                      ).map(
                        (item) => (
                          <div
                            key={item}
                            className="rounded-2xl border border-white/8 bg-white/[0.02] p-3 text-sm text-white/80"
                          >
                            {item}
                          </div>
                        ),
                      )}
                    </div>
                  </section>
                )}

                {activeView ===
                  "requirements" && (
                  <ATSChecklist
                    result={
                      jobResult
                    }
                  />
                )}

                {activeView ===
                  "rewrite" && (
                  <RewriteSuggestions
                    result={
                      jobResult
                    }
                  />
                )}

                {activeView ===
                  "ai" && (
                  <JobMatcher
                    file={file}
                    result={
                      jobResult
                    }
                    onResult={
                      setJobResult
                    }
                    onError={
                      setError
                    }
                  />
                )}
              </>
            ) : (
              <div className="rounded-3xl border border-dashed border-white/10 p-10 text-center text-sm text-white/50">
                Upload a resume and run analysis to populate the intelligence panels.
              </div>
            )}
          </div>
        </div>

        <div className="mt-6 rounded-3xl border border-white/10 bg-white/[0.02] p-5 text-xs text-white/60">
          Maximum accepted upload size: 10 MB. PDF format only.
        </div>
      </div>
    </main>
  );
}
