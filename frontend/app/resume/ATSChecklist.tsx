import type { ResumeJobAnalysisResponse } from "@/lib/api";

type RequirementItem =
  | string
  | {
      text?: string;
      requirement?: string;
      normalized?: string;
      category?: string;
      importance?: string;
      status?: string;
      evidence?: string[];
      [key: string]: unknown;
    };

type MatchItem = {
  requirement?: string;
  text?: string;
  category?: string;
  status?: string;
  evidence?: string[];
  confidence?: number;
  [key: string]: unknown;
};

function getText(item: RequirementItem): string {
  if (typeof item === "string") return item;

  return (
    item.requirement ??
    item.text ??
    item.normalized ??
    "Requirement"
  );
}

function getLabel(value: unknown, fallback = "Review"): string {
  if (typeof value === "string" && value.trim()) return value;
  return fallback;
}

function getScore(value: unknown): number | null {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return null;
  }

  return Math.max(0, Math.min(100, value));
}

function scoreClass(score: number): string {
  if (score >= 80) {
    return "text-emerald-400";
  }

  if (score >= 60) {
    return "text-amber-400";
  }

  return "text-red-400";
}

function statusClass(status: string): string {
  const normalized = status.toLowerCase();

  if (
    normalized.includes("match") ||
    normalized.includes("supported") ||
    normalized.includes("strong") ||
    normalized.includes("pass")
  ) {
    return "border-emerald-400/20 bg-emerald-400/10 text-emerald-300";
  }

  if (
    normalized.includes("partial") ||
    normalized.includes("weak") ||
    normalized.includes("mention")
  ) {
    return "border-amber-400/20 bg-amber-400/10 text-amber-300";
  }

  if (
    normalized.includes("missing") ||
    normalized.includes("fail")
  ) {
    return "border-red-400/20 bg-red-400/10 text-red-300";
  }

  return "border-white/10 bg-white/[0.04] text-white/60";
}

function KeywordGroup({
  title,
  values,
  tone,
}: {
  title: string;
  values: string[];
  tone: "positive" | "warning" | "negative";
}) {
  if (!values.length) return null;

  const toneClass =
    tone === "positive"
      ? "border-emerald-400/15 bg-emerald-400/[0.04]"
      : tone === "warning"
        ? "border-amber-400/15 bg-amber-400/[0.04]"
        : "border-red-400/15 bg-red-400/[0.04]";

  return (
    <div className={`rounded-2xl border p-4 ${toneClass}`}>
      <div className="text-xs uppercase tracking-[0.16em] text-white/50">
        {title}
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {values.map((keyword, index) => (
          <span
            key={`${title}-${index}-${keyword}`}
            className="rounded-full border border-white/10 bg-black/20 px-3 py-1.5 text-xs text-white/75"
          >
            {keyword}
          </span>
        ))}
      </div>
    </div>
  );
}

export function ATSChecklist({
  result,
}: {
  result: ResumeJobAnalysisResponse | null;
}) {
  const ats = result?.ats_analysis;

  if (!ats) {
    return (
      <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6 backdrop-blur">
        <div className="text-xs uppercase tracking-[0.18em] text-white/60">
          ATS Analysis
        </div>

        <div className="mt-5 rounded-2xl border border-dashed border-white/10 p-8 text-center">
          <div className="text-sm font-medium text-white/80">
            No ATS analysis available
          </div>

          <p className="mt-2 text-sm text-white/45">
            Run a job-specific resume analysis to generate ATS matching,
            keyword coverage, requirements, and recommendations.
          </p>
        </div>
      </section>
    );
  }

  const overallScore = getScore(ats.overall_score);
  const keywordScore = getScore(ats.keyword_coverage_score);
  const skillScore = getScore(ats.skill_match_score);
  const experienceScore = getScore(ats.experience_alignment_score);
  const educationScore = getScore(ats.education_alignment_score);
  const sectionScore = getScore(ats.section_coverage_score);

  const requirements = (ats.requirements ?? []) as RequirementItem[];
  const matches = (ats.matches ?? []) as MatchItem[];

  const missingRequirements = (ats.missing_requirements ?? [])
    .map(String)
    .filter(Boolean);

  const matchedKeywords = (ats.matched_keywords ?? [])
    .map(String)
    .filter(Boolean);

  const missingKeywords = (ats.missing_keywords ?? [])
    .map(String)
    .filter(Boolean);

  const weakKeywords = (ats.weak_keywords ?? [])
    .map(String)
    .filter(Boolean);

  const supportedRequirements = (ats.supported_requirements ?? [])
    .map(String)
    .filter(Boolean);

  const mentionedOnlyRequirements = (ats.mentioned_only_requirements ?? [])
    .map(String)
    .filter(Boolean);

  const strengths = (ats.strengths ?? [])
    .map(String)
    .filter(Boolean);

  const issues = (ats.issues ?? [])
    .map(String)
    .filter(Boolean);

  const recommendations = (ats.recommendations ?? [])
    .map(String)
    .filter(Boolean);

  return (
    <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6 backdrop-blur">
      {/* HEADER */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="text-xs uppercase tracking-[0.18em] text-white/60">
            ATS Resume Analysis
          </div>

          <h2 className="mt-2 text-xl font-semibold text-white">
            Applicant Tracking System Readiness
          </h2>

          <p className="mt-2 max-w-3xl text-sm leading-6 text-white/50">
            This analysis compares the resume evidence against the target
            requirements and identifies keyword coverage, requirement
            alignment, missing evidence, and ATS risks.
          </p>
        </div>

        {overallScore !== null && (
          <div className="flex min-w-[150px] items-center gap-4 rounded-2xl border border-white/10 bg-black/20 px-5 py-4">
            <div>
              <div className="text-xs uppercase tracking-[0.14em] text-white/40">
                Overall ATS
              </div>

              <div
                className={`mt-1 text-3xl font-semibold ${scoreClass(
                  overallScore,
                )}`}
              >
                {overallScore.toFixed(0)}%
              </div>
            </div>
          </div>
        )}
      </div>

      {/* SCORE GRID */}
      <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        {[
          ["Keywords", keywordScore],
          ["Skills", skillScore],
          ["Experience", experienceScore],
          ["Education", educationScore],
          ["Sections", sectionScore],
        ].map(([label, value]) => {
          const score =
            typeof value === "number" ? value : null;

          return (
            <div
              key={String(label)}
              className="rounded-2xl border border-white/10 bg-black/15 p-4"
            >
              <div className="text-xs uppercase tracking-[0.12em] text-white/40">
                {label}
              </div>

              <div
                className={`mt-2 text-2xl font-semibold ${
                  score !== null
                    ? scoreClass(score)
                    : "text-white/30"
                }`}
              >
                {score !== null ? `${score.toFixed(0)}%` : "—"}
              </div>
            </div>
          );
        })}
      </div>

      {/* SUMMARY */}
      {ats.summary && (
        <div className="mt-6 rounded-2xl border border-white/10 bg-black/15 p-5">
          <div className="text-xs uppercase tracking-[0.16em] text-white/40">
            ATS Summary
          </div>

          <p className="mt-3 text-sm leading-6 text-white/70">
            {ats.summary}
          </p>
        </div>
      )}

      {/* KEYWORD ANALYSIS */}
      {(matchedKeywords.length ||
        missingKeywords.length ||
        weakKeywords.length) > 0 && (
        <div className="mt-6">
          <div className="text-xs uppercase tracking-[0.16em] text-white/50">
            Keyword Coverage
          </div>

          <div className="mt-3 grid gap-3 xl:grid-cols-3">
            <KeywordGroup
              title="Matched Keywords"
              values={matchedKeywords}
              tone="positive"
            />

            <KeywordGroup
              title="Weak Keywords"
              values={weakKeywords}
              tone="warning"
            />

            <KeywordGroup
              title="Missing Keywords"
              values={missingKeywords}
              tone="negative"
            />
          </div>
        </div>
      )}

      {/* REQUIREMENT MATCHES */}
      {(requirements.length ||
        matches.length ||
        supportedRequirements.length ||
        mentionedOnlyRequirements.length ||
        missingRequirements.length) > 0 && (
        <div className="mt-6">
          <div className="text-xs uppercase tracking-[0.16em] text-white/50">
            Requirement Matching
          </div>

          <div className="mt-3 space-y-2.5">
            {matches.length > 0
              ? matches.map((match, index) => {
                  const requirement =
                    match.requirement ??
                    match.text ??
                    "Requirement";

                  const status = getLabel(
                    match.status,
                    "Review",
                  );

                  const confidence =
                    typeof match.confidence === "number"
                      ? Math.round(match.confidence * 100)
                      : null;

                  return (
                    <div
                      key={`match-${index}-${requirement}`}
                      className="rounded-2xl border border-white/10 bg-black/15 p-4"
                    >
                      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                        <div className="min-w-0">
                          <div className="font-medium text-white/90">
                            {requirement}
                          </div>

                          {match.category && (
                            <div className="mt-1 text-xs text-white/40">
                              {match.category}
                            </div>
                          )}
                        </div>

                        <div className="flex shrink-0 items-center gap-2">
                          {confidence !== null && (
                            <span className="rounded-full border border-white/10 bg-white/[0.03] px-2.5 py-1 text-xs text-white/50">
                              {confidence}% confidence
                            </span>
                          )}

                          <span
                            className={`rounded-full border px-2.5 py-1 text-xs ${statusClass(
                              status,
                            )}`}
                          >
                            {status}
                          </span>
                        </div>
                      </div>

                      {match.evidence?.length ? (
                        <div className="mt-3 rounded-xl bg-white/[0.02] p-3">
                          <div className="text-[11px] uppercase tracking-[0.12em] text-white/35">
                            Resume Evidence
                          </div>

                          <ul className="mt-2 space-y-1">
                            {match.evidence.map(
                              (evidence, evidenceIndex) => (
                                <li
                                  key={`${index}-evidence-${evidenceIndex}`}
                                  className="text-xs leading-5 text-white/55"
                                >
                                  {evidence}
                                </li>
                              ),
                            )}
                          </ul>
                        </div>
                      ) : null}
                    </div>
                  );
                })
              : requirements.map((item, index) => {
                  const requirement = getText(item);

                  const status =
                    typeof item === "string"
                      ? "Review"
                      : getLabel(
                          item.status,
                          item.importance ?? "Review",
                        );

                  return (
                    <div
                      key={`requirement-${index}-${requirement}`}
                      className="flex flex-col gap-3 rounded-2xl border border-white/10 bg-black/15 p-4 sm:flex-row sm:items-center sm:justify-between"
                    >
                      <div>
                        <div className="font-medium text-white/90">
                          {requirement}
                        </div>

                        {typeof item !== "string" &&
                          item.category && (
                            <div className="mt-1 text-xs text-white/40">
                              {item.category}
                            </div>
                          )}
                      </div>

                      <span
                        className={`self-start rounded-full border px-2.5 py-1 text-xs sm:self-auto ${statusClass(
                          status,
                        )}`}
                      >
                        {status}
                      </span>
                    </div>
                  );
                })}
          </div>
        </div>
      )}

      {/* REQUIREMENT BREAKDOWN */}
      {(supportedRequirements.length ||
        mentionedOnlyRequirements.length ||
        missingRequirements.length) > 0 && (
        <div className="mt-6 grid gap-3 lg:grid-cols-3">
          {[
            {
              title: "Supported",
              values: supportedRequirements,
              tone: "positive" as const,
            },
            {
              title: "Mentioned Only",
              values: mentionedOnlyRequirements,
              tone: "warning" as const,
            },
            {
              title: "Missing",
              values: missingRequirements,
              tone: "negative" as const,
            },
          ].map((group) => (
            <div
              key={group.title}
              className="rounded-2xl border border-white/10 bg-black/15 p-4"
            >
              <div className="text-xs uppercase tracking-[0.14em] text-white/45">
                {group.title}
              </div>

              <div className="mt-3 space-y-2">
                {group.values.length ? (
                  group.values.map((value, index) => (
                    <div
                      key={`${group.title}-${index}-${value}`}
                      className="rounded-xl border border-white/8 bg-white/[0.02] px-3 py-2 text-xs leading-5 text-white/65"
                    >
                      {value}
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-white/25">
                    None identified
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* STRENGTHS / ISSUES */}
      {(strengths.length || issues.length) > 0 && (
        <div className="mt-6 grid gap-3 lg:grid-cols-2">
          {strengths.length > 0 && (
            <div className="rounded-2xl border border-emerald-400/15 bg-emerald-400/[0.035] p-5">
              <div className="text-xs uppercase tracking-[0.16em] text-emerald-300/70">
                ATS Strengths
              </div>

              <div className="mt-3 space-y-2">
                {strengths.map((strength, index) => (
                  <div
                    key={`strength-${index}`}
                    className="text-sm leading-6 text-white/70"
                  >
                    • {strength}
                  </div>
                ))}
              </div>
            </div>
          )}

          {issues.length > 0 && (
            <div className="rounded-2xl border border-red-400/15 bg-red-400/[0.035] p-5">
              <div className="text-xs uppercase tracking-[0.16em] text-red-300/70">
                ATS Issues
              </div>

              <div className="mt-3 space-y-2">
                {issues.map((issue, index) => (
                  <div
                    key={`issue-${index}`}
                    className="text-sm leading-6 text-white/70"
                  >
                    • {issue}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* RECOMMENDATIONS */}
      {recommendations.length > 0 && (
        <div className="mt-6 rounded-2xl border border-white/10 bg-black/15 p-5">
          <div className="text-xs uppercase tracking-[0.16em] text-white/45">
            ATS Recommendations
          </div>

          <div className="mt-3 space-y-3">
            {recommendations.map((recommendation, index) => (
              <div
                key={`recommendation-${index}`}
                className="flex gap-3"
              >
                <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-white/10 text-xs text-white/60">
                  {index + 1}
                </div>

                <div className="text-sm leading-6 text-white/70">
                  {recommendation}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* RISK FLAGS */}
{(() => {
  const riskFlags: string[] = Array.isArray(ats.risk_flags)
    ? ats.risk_flags.map((flag: unknown) => String(flag))
    : [];

  const hasRiskSignals =
    Boolean(ats.keyword_stuffing_risk) ||
    Boolean(ats.unsupported_claim_risk) ||
    riskFlags.length > 0;

  if (!hasRiskSignals) {
    return null;
  }

  return (
    <div className="mt-6 rounded-2xl border border-amber-400/15 bg-amber-400/[0.035] p-5">
      <div className="text-xs uppercase tracking-[0.16em] text-amber-300/70">
        ATS Risk Signals
      </div>

      <div className="mt-3 space-y-2">
        {ats.keyword_stuffing_risk && (
          <div className="text-sm text-white/70">
            • Keyword stuffing risk detected.
          </div>
        )}

        {ats.unsupported_claim_risk && (
          <div className="text-sm text-white/70">
            • Unsupported-claim risk detected.
          </div>
        )}

        {riskFlags.map((flag, index) => (
          <div
            key={`risk-${index}-${flag}`}
            className="text-sm text-white/70"
          >
            • {flag}
          </div>
        ))}
      </div>
    </div>
  );
})()}
    </section>
  );
}