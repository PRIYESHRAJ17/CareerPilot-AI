"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  BriefcaseBusiness,
  Building2,
  CalendarDays,
  Check,
  ChevronDown,
  CircleUserRound,
  ExternalLink,
  FileText,
  LayoutDashboard,
  Loader2,
  MapPin,
  MessageSquareText,
  Moon,
  Search,
  Settings,
  Sparkles,
  Target,
  UserRound,
  X,
} from "lucide-react";

import {
  searchJobs,
  type JobResult,
  type SourceRecord,
} from "@/lib/api";

const navItems = [
  {
    label: "Dashboard",
    icon: LayoutDashboard,
    href: "/dashboard",
    active: false,
  },
  {
    label: "Opportunities",
    icon: BriefcaseBusiness,
    href: "/opportunities",
    active: true,
  },
  {
    label: "Career Twin",
    icon: Target,
    href: "/career-twin",
    active: false,
  },
  {
    label: "Resume",
    icon: FileText,
    href: "/resume",
    active: false,
  },
  {
    label: "Companies",
    icon: Building2,
    href: "/companies",
    active: false,
  },
  {
    label: "Interviews",
    icon: MessageSquareText,
    href: "/interviews",
    active: false,
  },
  {
    label: "Applications",
    icon: CalendarDays,
    href: "/applications",
    active: false,
  },
];

const defaultSkills = [
  "Python",
  "SQL",
  "DSA",
  "Git",
];

function formatDecision(
  decision: string | null | undefined,
) {
  switch (decision) {
    case "APPLY_NOW":
      return "Apply now";

    case "GOOD_MATCH":
      return "Good match";

    case "STRETCH":
      return "Stretch";

    case "LOW_PRIORITY":
      return "Low priority";

    default:
      return "Review";
  }
}

function getDecisionClass(
  decision: string | null | undefined,
) {
  switch (decision) {
    case "APPLY_NOW":
      return "border-emerald-400/20 bg-emerald-400/5 text-emerald-200";

    case "GOOD_MATCH":
      return "border-sky-400/20 bg-sky-400/5 text-sky-200";

    case "STRETCH":
      return "border-amber-400/20 bg-amber-400/5 text-amber-200";

    default:
      return "border-white/10 bg-white/[0.03] text-white/45";
  }
}

function formatSalary(
  job: JobResult,
) {
  if (!job.salary_disclosed) {
    return "Salary not disclosed";
  }

  const min = job.salary_min_lpa;
  const max = job.salary_max_lpa;

  if (
    min != null &&
    max != null
  ) {
    return `₹${min}–${max} LPA`;
  }

  if (min != null) {
    return `₹${min}+ LPA`;
  }

  if (max != null) {
    return `Up to ₹${max} LPA`;
  }

  return "Salary not disclosed";
}

function formatSourceSalary(
  source: SourceRecord,
) {
  const min = source.salary_min_lpa;
  const max = source.salary_max_lpa;

  if (
    min != null &&
    max != null &&
    min > 0 &&
    max > 0
  ) {
    return `₹${min}–${max} LPA`;
  }

  if (
    min != null &&
    min > 0
  ) {
    return `₹${min}+ LPA`;
  }

  if (
    max != null &&
    max > 0
  ) {
    return `Up to ₹${max} LPA`;
  }

  return "Salary not disclosed";
}

function ResultSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from(
        { length: 6 },
        (_, index) => (
          <div
            key={index}
            className="animate-pulse rounded-[24px] border border-white/8 bg-white/[0.02] p-5"
          >
            <div className="flex flex-col gap-5 xl:flex-row xl:items-center">
              <div className="flex flex-1 items-start gap-4">
                <div className="h-12 w-12 rounded-2xl bg-white/5" />

                <div className="min-w-0 flex-1">
                  <div className="h-3 w-28 rounded bg-white/5" />

                  <div className="mt-3 h-4 w-72 max-w-full rounded bg-white/5" />

                  <div className="mt-3 h-3 w-52 rounded bg-white/5" />

                  <div className="mt-4 flex gap-2">
                    <div className="h-5 w-20 rounded-full bg-white/5" />
                    <div className="h-5 w-16 rounded-full bg-white/5" />
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div>
                  <div className="h-3 w-12 rounded bg-white/5" />
                  <div className="mt-2 h-8 w-16 rounded bg-white/5" />
                </div>

                <div className="h-10 w-28 rounded-xl bg-white/5" />
              </div>
            </div>
          </div>
        ),
      )}
    </div>
  );
}

function ScoreBar({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  const safeValue = Math.min(
    100,
    Math.max(0, value),
  );

  return (
    <div>
      <div className="flex items-center justify-between text-xs">
        <span className="text-white/55">
          {label}
        </span>

        <span className="font-medium text-white/80">
          {Math.round(safeValue)}
        </span>
      </div>

      <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/8">
        <div
          className="h-full rounded-full bg-white transition-all duration-500"
          style={{
            width: `${safeValue}%`,
          }}
        />
      </div>
    </div>
  );
}

function SourceCard({
  source,
}: {
  source: SourceRecord;
}) {
  const sourceSalary =
    formatSourceSalary(source);

  const hasSalary =
    sourceSalary !==
    "Salary not disclosed";

  return (
    <div className="rounded-[20px] border border-white/8 bg-black/15 p-4">
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full border border-white/10 bg-white/[0.03] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.13em] text-white/65">
                {source.source}
              </span>

              {hasSalary && (
                <span className="rounded-full border border-emerald-400/15 bg-emerald-400/[0.04] px-2.5 py-1 text-[10px] text-emerald-100/70">
                  Salary available
                </span>
              )}

              {!hasSalary && (
                <span className="rounded-full border border-amber-400/15 bg-amber-400/[0.04] px-2.5 py-1 text-[10px] text-amber-100/70">
                  Salary undisclosed
                </span>
              )}
            </div>

            <div className="mt-3 text-sm font-medium text-white/85">
              {source.title}
            </div>

            <div className="mt-2 flex flex-wrap items-center gap-2 text-[11px] text-white/35">
              <span>
                {source.location.length > 0
                  ? source.location.join(", ")
                  : "Location not specified"}
              </span>

              {source.remote && (
                <>
                  <span>•</span>

                  <span className="text-emerald-200/70">
                    Remote
                  </span>
                </>
              )}

              {source.employment_type && (
                <>
                  <span>•</span>

                  <span>
                    {source.employment_type}
                  </span>
                </>
              )}
            </div>

            <div className="mt-3 text-xs text-white/45">
              {hasSalary ? (
                <>
                  <span className="text-white/70">
                    {sourceSalary}
                  </span>

                  {source.salary_confidence >
                    0 && (
                    <span className="ml-2 text-[10px] text-white/25">
                      {Math.round(
                        source.salary_confidence *
                          100,
                      )}
                      % confidence
                    </span>
                  )}
                </>
              ) : (
                "Salary not disclosed"
              )}
            </div>

            {source.salary_evidence && (
              <div className="mt-3 rounded-xl border border-white/8 bg-white/[0.02] px-3 py-2 text-[11px] text-white/45">
                Salary evidence: “
                {source.salary_evidence}
                ”
              </div>
            )}
          </div>

          <div className="shrink-0 text-[10px] uppercase tracking-[0.14em] text-white/20">
            {source.source_job_id}
          </div>
        </div>

        {/* Source-specific actions */}
        <div className="flex flex-wrap gap-2 border-t border-white/8 pt-4">
          {source.source_url && (
            <a
              href={source.source_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/[0.02] px-4 py-2.5 text-[11px] font-medium text-white/60 transition hover:bg-white/[0.06] hover:text-white"
            >
              View listing
              <ExternalLink size={13} />
            </a>
          )}

          {source.apply_url && (
            <a
              href={source.apply_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 rounded-xl bg-white px-4 py-2.5 text-[11px] font-semibold text-black transition hover:bg-white/90"
            >
              Apply through {source.source}
              <ExternalLink size={13} />
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

function IntelligencePanel({
  job,
  minimumSalary,
  onClose,
}: {
  job: JobResult;
  minimumSalary: number | undefined;
  onClose: () => void;
}) {
  const breakdown =
    job.match_breakdown;

  const score = Math.round(
    job.match_score ?? 0,
  );

  const decision =
    formatDecision(job.decision);

  const salary =
    formatSalary(job);

  const salaryVerified =
    job.salary_status ===
    "MEETS_TARGET";

  const sourceRecords =
    job.source_records.length > 0
      ? job.source_records
      : [];

  return (
    <div className="fixed inset-0 z-[70]">
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />

      <aside className="absolute inset-y-0 right-0 w-full overflow-y-auto border-l border-white/10 bg-[#0b0e14] shadow-2xl sm:max-w-[680px]">
        {/* Drawer header */}
        <div className="sticky top-0 z-20 border-b border-white/8 bg-[#0b0e14]/95 backdrop-blur-xl">
          <div className="flex items-center justify-between px-5 py-4">
            <button
              type="button"
              onClick={onClose}
              className="flex items-center gap-2 text-xs text-white/45 transition hover:text-white"
            >
              <ArrowLeft size={15} />
              Back to opportunities
            </button>

            <button
              type="button"
              onClick={onClose}
              className="rounded-xl border border-white/10 p-2 text-white/55 transition hover:bg-white/5 hover:text-white"
              aria-label="Close analysis"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        <div className="px-5 py-6 md:px-7">
          {/* Opportunity identity */}
          <section>
            <div className="flex items-start gap-4">
              <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.04] text-sm font-semibold">
                {job.company
                  .slice(0, 2)
                  .toUpperCase()}
              </div>

              <div className="min-w-0">
                <div className="text-[10px] uppercase tracking-[0.2em] text-white/30">
                  {job.company}
                </div>

                <h2 className="mt-1 text-xl font-semibold leading-7">
                  {job.title}
                </h2>

                <div className="mt-2 flex flex-wrap gap-2 text-xs text-white/35">
                  <span>
                    {job.location.join(
                      ", ",
                    ) ||
                      "Location not specified"}
                  </span>

                  {job.remote && (
                    <>
                      <span>•</span>

                      <span className="text-emerald-200/70">
                        Remote
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>
          </section>

          {/* Match hero */}
          <section className="mt-6 rounded-[24px] border border-white/10 bg-white/[0.03] p-5">
            <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <div className="text-[10px] uppercase tracking-[0.2em] text-white/30">
                  CareerPilot match
                </div>

                <div className="mt-2 flex items-baseline gap-2">
                  <span className="text-5xl font-semibold tracking-[-0.04em]">
                    {score}
                  </span>

                  <span className="text-sm text-white/30">
                    /100
                  </span>
                </div>

                {job.confidence !=
                  null && (
                  <div className="mt-2 text-xs text-white/35">
                    {Math.round(
                      job.confidence,
                    )}
                    % confidence
                  </div>
                )}
              </div>

              <div
                className={`inline-flex w-fit rounded-full border px-4 py-2 text-[10px] font-medium uppercase tracking-[0.14em] ${getDecisionClass(
                  job.decision,
                )}`}
              >
                {decision}
              </div>
            </div>

            <div className="mt-5 h-2 overflow-hidden rounded-full bg-white/8">
              <div
                className="h-full rounded-full bg-white transition-all"
                style={{
                  width: `${Math.min(
                    100,
                    Math.max(
                      0,
                      score,
                    ),
                  )}%`,
                }}
              />
            </div>
          </section>

          {/* Explanation */}
          <section className="mt-5 rounded-[24px] border border-white/8 bg-white/[0.02] p-5">
            <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.2em] text-white/30">
              <Sparkles size={13} />
              Why CareerPilot recommends this
            </div>

            <p className="mt-4 text-sm leading-7 text-white/55">
              {job.explanation ||
                "CareerPilot evaluated this opportunity using role, skill, experience, location, salary and semantic compatibility evidence."}
            </p>
          </section>

          {/* Match breakdown */}
          {breakdown && (
            <section className="mt-5 rounded-[24px] border border-white/8 bg-white/[0.02] p-5">
              <div className="text-[10px] uppercase tracking-[0.2em] text-white/30">
                Match breakdown
              </div>

              <div className="mt-5 space-y-4">
                <ScoreBar
                  label="Role fit"
                  value={
                    breakdown.role_fit
                  }
                />

                <ScoreBar
                  label="Skill fit"
                  value={
                    breakdown.skill_fit
                  }
                />

                <ScoreBar
                  label="Experience fit"
                  value={
                    breakdown.experience_fit
                  }
                />

                <ScoreBar
                  label="Location fit"
                  value={
                    breakdown.location_fit
                  }
                />

                <ScoreBar
                  label="Salary fit"
                  value={
                    breakdown.salary_fit
                  }
                />

                <ScoreBar
                  label="Career goal fit"
                  value={
                    breakdown.career_goal_fit
                  }
                />
              </div>

              <div className="mt-5 grid grid-cols-2 gap-3">
                <div className="rounded-2xl border border-white/8 bg-white/[0.02] p-4">
                  <div className="text-[10px] uppercase tracking-[0.16em] text-white/30">
                    Deterministic
                  </div>

                  <div className="mt-2 text-xl font-semibold">
                    {Math.round(
                      breakdown.deterministic_score ??
                        0,
                    )}
                  </div>
                </div>

                <div className="rounded-2xl border border-white/8 bg-white/[0.02] p-4">
                  <div className="text-[10px] uppercase tracking-[0.16em] text-white/30">
                    Semantic
                  </div>

                  <div className="mt-2 text-xl font-semibold">
                    {Math.round(
                      breakdown.semantic_score ??
                        0,
                    )}
                  </div>
                </div>
              </div>
            </section>
          )}

          {/* Skills */}
          <section className="mt-5 rounded-[24px] border border-white/8 bg-white/[0.02] p-5">
            <div className="text-[10px] uppercase tracking-[0.2em] text-white/30">
              Skill intelligence
            </div>

            <div className="mt-5">
              <div className="text-xs font-medium text-white/70">
                Matched skills
              </div>

              {job.matched_skills
                .length > 0 ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  {job.matched_skills.map(
                    (skill) => (
                      <span
                        key={skill}
                        className="inline-flex items-center gap-1.5 rounded-full border border-emerald-400/15 bg-emerald-400/[0.04] px-3 py-1.5 text-xs text-emerald-100/75"
                      >
                        <Check size={12} />
                        {skill}
                      </span>
                    ),
                  )}
                </div>
              ) : (
                <div className="mt-2 text-xs text-white/30">
                  No explicit matched skills were extracted.
                </div>
              )}
            </div>

            <div className="mt-6">
              <div className="text-xs font-medium text-white/70">
                Skill gaps
              </div>

              {job.skill_gaps
                .length > 0 ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  {job.skill_gaps.map(
                    (skill) => (
                      <span
                        key={skill}
                        className="rounded-full border border-amber-400/15 bg-amber-400/[0.04] px-3 py-1.5 text-xs text-amber-100/75"
                      >
                        △ {skill}
                      </span>
                    ),
                  )}
                </div>
              ) : (
                <div className="mt-2 text-xs text-white/30">
                  No explicit skill gaps detected.
                </div>
              )}
            </div>
          </section>

          {/* Salary */}
          <section className="mt-5 rounded-[24px] border border-white/8 bg-white/[0.02] p-5">
            <div className="text-[10px] uppercase tracking-[0.2em] text-white/30">
              Salary intelligence
            </div>

            <div className="mt-4">
              {salaryVerified ? (
                <>
                  <div className="text-2xl font-semibold">
                    {salary}
                  </div>

                  <div className="mt-2 text-xs text-emerald-200/70">
                    ✓ Meets the{" "}
                    {minimumSalary !=
                    null
                      ? `₹${minimumSalary} LPA+`
                      : "salary"}{" "}
                    target
                  </div>

                  {job.salary_evidence && (
                    <div className="mt-4 rounded-2xl border border-white/8 bg-black/15 p-4">
                      <div className="text-[10px] uppercase tracking-[0.16em] text-white/25">
                        Evidence
                      </div>

                      <div className="mt-2 text-sm text-white/60">
                        “
                        {
                          job.salary_evidence
                        }
                        ”
                      </div>

                      {job.salary_confidence >
                        0 && (
                        <div className="mt-2 text-[11px] text-white/30">
                          {Math.round(
                            job.salary_confidence *
                              100,
                          )}
                          % extraction confidence
                        </div>
                      )}
                    </div>
                  )}
                </>
              ) : (
                <>
                  <div className="text-2xl font-semibold">
                    Salary not disclosed
                  </div>

                  <p className="mt-2 text-sm leading-6 text-white/40">
                    The company has not disclosed compensation.
                    Contact the employer or recruiter directly
                    to confirm the expected salary range.
                  </p>
                </>
              )}
            </div>
          </section>

          {/* SOURCE PROVENANCE */}
          <section className="mt-5 rounded-[24px] border border-white/8 bg-white/[0.02] p-5">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <div className="text-[10px] uppercase tracking-[0.2em] text-white/30">
                  Source provenance
                </div>

                <div className="mt-1 text-lg font-semibold">
                  Found across{" "}
                  {job.source_count}{" "}
                  {job.source_count ===
                  1
                    ? "source"
                    : "sources"}
                </div>

                <div className="mt-1 text-xs leading-5 text-white/35">
                  Every listing below is a separate source representation of this canonical opportunity.
                </div>
              </div>

              <div className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 text-[10px] uppercase tracking-[0.15em] text-white/45">
                {sourceRecords.length}{" "}
                listing
                {sourceRecords.length ===
                1
                  ? ""
                  : "s"}
              </div>
            </div>

            <div className="mt-5 space-y-3">
              {sourceRecords.length >
              0 ? (
                sourceRecords.map(
                  (
                    source,
                    index,
                  ) => (
                    <SourceCard
                      key={`${source.source}-${source.source_job_id}-${index}`}
                      source={source}
                    />
                  ),
                )
              ) : (
                <div className="rounded-2xl border border-white/8 bg-black/10 p-4 text-xs text-white/35">
                  Source details are not available for this opportunity.
                </div>
              )}
            </div>
          </section>

          {/* Primary action */}
          <section className="mt-6">
            <a
              href={job.apply_url}
              target="_blank"
              rel="noreferrer"
              className="flex w-full items-center justify-center gap-2 rounded-2xl bg-white px-5 py-4 text-sm font-semibold text-black transition hover:bg-white/90"
            >
              Apply to this opportunity
              <ExternalLink size={16} />
            </a>

            <p className="mt-3 text-center text-[11px] leading-5 text-white/25">
              This opens the primary listing currently selected by CareerPilot.
              Individual source applications are available above.
            </p>
          </section>

          <div className="h-8" />
        </div>
      </aside>
    </div>
  );
}

export default function OpportunitiesPage() {
  const [
    sidebarOpen,
    setSidebarOpen,
  ] = useState(false);

  const [
    selectedJob,
    setSelectedJob,
  ] = useState<JobResult | null>(
    null,
  );

  const [
    role,
    setRole,
  ] = useState(
    "Software Engineer",
  );

  const [
    location,
    setLocation,
  ] = useState(
    "Bangalore",
  );

  const [
    minimumSalary,
    setMinimumSalary,
  ] = useState("6");

  const [
    jobs,
    setJobs,
  ] = useState<JobResult[]>([]);

  const [
    searched,
    setSearched,
  ] = useState(false);

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState("");

  const [
    salaryVerified,
    setSalaryVerified,
  ] = useState(0);

  const [
    salaryUndisclosed,
    setSalaryUndisclosed,
  ] = useState(0);

  const [
    sourceSummary,
    setSourceSummary,
  ] = useState({
    connected: 0,
    contributing: 0,
    sources: [] as string[],
  });

  async function handleSearch() {
    if (!role.trim()) {
      setError(
        "Please enter a role before searching.",
      );
      return;
    }

    const salaryValue =
      minimumSalary.trim() === ""
        ? undefined
        : Number(minimumSalary);

    if (
      salaryValue !== undefined &&
      !Number.isFinite(
        salaryValue,
      )
    ) {
      setError(
        "Please enter a valid minimum salary.",
      );
      return;
    }

    setLoading(true);
    setError("");
    setSearched(true);
    setSelectedJob(null);
    setJobs([]);

    setSalaryVerified(0);
    setSalaryUndisclosed(0);

    setSourceSummary({
      connected: 0,
      contributing: 0,
      sources: [],
    });

    try {
      const response =
        await searchJobs({
          role: role.trim(),

          location:
            location.trim() ||
            undefined,

          experience_years: 0,

          minimum_salary_lpa:
            salaryValue,

          preferred_work_modes: [
            "remote",
            "hybrid",
          ],

          skills:
            defaultSkills,

          target_industries: [
            "technology",
          ],
        });

      setJobs(
        response.results,
      );

      setSalaryVerified(
        response.salary_summary
          .salary_verified,
      );

      setSalaryUndisclosed(
        response.salary_summary
          .salary_undisclosed,
      );

      setSourceSummary(
        response.source_summary,
      );
    } catch (err) {
      setJobs([]);

      setError(
        err instanceof Error
          ? err.message
          : "CareerPilot could not complete the search.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#080a0f] text-white">
      {/* Mobile sidebar */}
      {sidebarOpen && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
            onClick={() =>
              setSidebarOpen(false)
            }
          />

          <aside className="fixed inset-y-0 left-0 z-50 w-[280px] border-r border-white/10 bg-[#0b0e14] lg:hidden">
            <div className="flex h-20 items-center justify-between border-b border-white/8 px-6">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white text-black">
                  <Sparkles size={18} />
                </div>

                <div>
                  <div className="text-[15px] font-semibold">
                    CareerPilot
                  </div>

                  <div className="text-[10px] uppercase tracking-[0.22em] text-white/35">
                    AI Career OS
                  </div>
                </div>
              </div>

              <button
                type="button"
                onClick={() =>
                  setSidebarOpen(false)
                }
                className="rounded-xl border border-white/10 p-2 text-white/60"
                aria-label="Close navigation"
              >
                <X size={17} />
              </button>
            </div>

            <div className="px-4 pt-6">
              <div className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-[0.2em] text-white/30">
                Workspace
              </div>

              <nav className="space-y-1">
                {navItems.map(
                  (item) => {
                    const Icon =
                      item.icon;

                    return (
                      <Link
                        key={
                          item.label
                        }
                        href={
                          item.href
                        }
                        onClick={() =>
                          setSidebarOpen(
                            false,
                          )
                        }
                        className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm transition ${
                          item.active
                            ? "bg-white text-black"
                            : "text-white/55 hover:bg-white/5 hover:text-white"
                        }`}
                      >
                        <Icon size={17} />

                        <span>
                          {
                            item.label
                          }
                        </span>
                      </Link>
                    );
                  },
                )}
              </nav>
            </div>
          </aside>
        </>
      )}

      <div className="flex min-h-screen">
        {/* Desktop sidebar */}
        <aside className="hidden w-[260px] shrink-0 border-r border-white/8 bg-[#0b0e14] lg:flex lg:flex-col">
          <div className="flex h-20 items-center gap-3 border-b border-white/8 px-6">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white text-black">
              <Sparkles size={18} />
            </div>

            <div>
              <div className="text-[15px] font-semibold">
                CareerPilot
              </div>

              <div className="text-[10px] uppercase tracking-[0.22em] text-white/35">
                AI Career OS
              </div>
            </div>
          </div>

          <div className="px-4 pt-6">
            <div className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-[0.2em] text-white/30">
              Workspace
            </div>

            <nav className="space-y-1">
              {navItems.map(
                (item) => {
                  const Icon =
                    item.icon;

                  return (
                    <Link
                      key={
                        item.label
                      }
                      href={
                        item.href
                      }
                      className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm transition ${
                        item.active
                          ? "bg-white text-black"
                          : "text-white/55 hover:bg-white/5 hover:text-white"
                      }`}
                    >
                      <Icon size={17} />

                      <span>
                        {
                          item.label
                        }
                      </span>
                    </Link>
                  );
                },
              )}
            </nav>
          </div>

          <div className="mt-auto border-t border-white/8 p-4">
            <Link
              href="/settings"
              className="flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm text-white/50 hover:bg-white/5 hover:text-white"
            >
              <Settings size={17} />
              Settings
            </Link>

            <div className="mt-3 flex items-center gap-3 rounded-2xl border border-white/8 bg-white/[0.03] p-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/10">
                <UserRound size={16} />
              </div>

              <div className="min-w-0">
                <div className="truncate text-sm font-medium">
                  Your Career Profile
                </div>

                <div className="text-[11px] text-white/35">
                  Python • SQL • DSA • Git
                </div>
              </div>

              <ChevronDown
                className="ml-auto text-white/30"
                size={15}
              />
            </div>
          </div>
        </aside>

        {/* Main workspace */}
        <section className="flex min-w-0 flex-1 flex-col">
          <header className="flex h-20 items-center justify-between border-b border-white/8 px-5 md:px-8">
            <div className="flex min-w-0 items-center gap-3">
              <div className="lg:hidden">
                <button
                  type="button"
                  onClick={() =>
                    setSidebarOpen(
                      true,
                    )
                  }
                  className="rounded-xl border border-white/10 p-2.5 text-white/70"
                  aria-label="Open navigation"
                >
                  <LayoutDashboard size={18} />
                </button>
              </div>

              <div>
                <div className="text-[11px] uppercase tracking-[0.2em] text-white/30">
                  Opportunities
                </div>

                <h1 className="text-xl font-semibold tracking-tight md:text-2xl">
                  Find roles worth your time.
                </h1>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                className="hidden rounded-xl border border-white/10 p-2.5 text-white/55 sm:block"
                aria-label="Toggle theme"
              >
                <Moon size={17} />
              </button>

              <button
                type="button"
                className="rounded-xl border border-white/10 p-2.5 text-white/55"
                aria-label="Profile"
              >
                <CircleUserRound size={17} />
              </button>
            </div>
          </header>

          <div className="flex-1 overflow-y-auto">
            <div className="mx-auto max-w-[1500px] px-5 py-6 md:px-8 md:py-8">
              {/* Hero */}
              <section className="overflow-hidden rounded-[28px] border border-white/10 bg-[radial-gradient(circle_at_top_right,rgba(255,255,255,0.10),transparent_35%),linear-gradient(135deg,#11151d,#0b0d12)] p-6 md:p-8">
                <div className="max-w-3xl">
                  <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[10px] uppercase tracking-[0.18em] text-white/55">
                    <Sparkles size={12} />
                    Career intelligence
                  </div>

                  <h2 className="text-3xl font-semibold leading-tight tracking-[-0.03em] md:text-5xl">
                    Search the market.
                    <br />

                    <span className="text-white/45">
                      Understand where you fit.
                    </span>
                  </h2>

                  <p className="mt-4 max-w-2xl text-sm leading-6 text-white/45 md:text-base">
                    CareerPilot combines live job discovery with candidate-specific matching, skill-gap analysis and explainable recommendations.
                  </p>
                </div>

                <form
                  onSubmit={(event) => {
                    event.preventDefault();
                    void handleSearch();
                  }}
                  className="mt-7 grid gap-3 lg:grid-cols-[1.5fr_1fr_1fr_auto]"
                >
                  <label className="flex items-center gap-3 rounded-2xl border border-white/10 bg-black/20 px-4 py-3.5">
                    <Search
                      size={18}
                      className="shrink-0 text-white/35"
                    />

                    <span className="min-w-0 flex-1">
                      <span className="block text-[10px] uppercase tracking-wider text-white/30">
                        Role
                      </span>

                      <input
                        value={role}
                        onChange={(event) =>
                          setRole(
                            event.target.value,
                          )
                        }
                        className="mt-0.5 w-full bg-transparent text-sm text-white/90 outline-none"
                        placeholder="Software Engineer"
                      />
                    </span>
                  </label>

                  <label className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3.5">
                    <span className="block text-[10px] uppercase tracking-wider text-white/30">
                      Location
                    </span>

                    <input
                      value={location}
                      onChange={(event) =>
                        setLocation(
                          event.target.value,
                        )
                      }
                      className="mt-0.5 w-full bg-transparent text-sm text-white/90 outline-none"
                      placeholder="Bangalore"
                    />
                  </label>

                  <label className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3.5">
                    <span className="block text-[10px] uppercase tracking-wider text-white/30">
                      Minimum salary
                    </span>

                    <div className="mt-0.5 flex items-center gap-1">
                      <span className="text-sm text-white/70">
                        ₹
                      </span>

                      <input
                        value={minimumSalary}
                        onChange={(event) =>
                          setMinimumSalary(
                            event.target.value.replace(
                              /[^0-9.]/g,
                              "",
                            ),
                          )
                        }
                        className="w-full bg-transparent text-sm text-white/90 outline-none"
                        inputMode="decimal"
                        placeholder="6"
                      />

                      <span className="text-xs text-white/30">
                        LPA+
                      </span>
                    </div>
                  </label>

                  <button
                    type="submit"
                    disabled={loading}
                    className="flex items-center justify-center gap-2 rounded-2xl bg-white px-6 py-3.5 text-sm font-semibold text-black transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {loading && (
                      <Loader2
                        size={16}
                        className="animate-spin"
                      />
                    )}

                    {loading
                      ? "Searching..."
                      : "Find matches"}
                  </button>
                </form>

                {error && (
                  <div className="mt-4 rounded-2xl border border-red-400/20 bg-red-400/5 px-4 py-3 text-sm text-red-200">
                    {error}
                  </div>
                )}
              </section>

              {/* Stats */}
              <section className="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                <div className="rounded-2xl border border-white/8 bg-white/[0.025] p-5">
                  <div className="text-[11px] uppercase tracking-[0.17em] text-white/30">
                    Opportunities found
                  </div>

                  <div className="mt-2 text-3xl font-semibold">
                    {searched
                      ? jobs.length
                      : "—"}
                  </div>

                  <div className="mt-1 text-xs text-white/35">
                    After deduplication and matching
                  </div>
                </div>

                <div className="rounded-2xl border border-white/8 bg-white/[0.025] p-5">
                  <div className="text-[11px] uppercase tracking-[0.17em] text-white/30">
                    Salary verified
                  </div>

                  <div className="mt-2 text-3xl font-semibold">
                    {searched
                      ? salaryVerified
                      : "—"}
                  </div>

                  <div className="mt-1 text-xs text-white/35">
                    Meets ₹
                    {minimumSalary ||
                      "—"}{" "}
                    LPA+
                  </div>
                </div>

                <div className="rounded-2xl border border-white/8 bg-white/[0.025] p-5">
                  <div className="text-[11px] uppercase tracking-[0.17em] text-white/30">
                    Salary undisclosed
                  </div>

                  <div className="mt-2 text-3xl font-semibold">
                    {searched
                      ? salaryUndisclosed
                      : "—"}
                  </div>

                  <div className="mt-1 text-xs text-white/35">
                    Contact employer to confirm
                  </div>
                </div>

                <div className="rounded-2xl border border-white/8 bg-white/[0.025] p-5">
                  <div className="text-[11px] uppercase tracking-[0.17em] text-white/30">
                    Job sources
                  </div>

                  <div className="mt-2 text-3xl font-semibold">
                    {searched
                      ? sourceSummary.connected
                      : "—"}
                  </div>

                  <div className="mt-1 text-xs text-white/35">
                    {searched
                      ? `${sourceSummary.contributing} contributing`
                      : "Connected providers"}
                  </div>
                </div>
              </section>

              {/* Results */}
              <section className="mt-8">
                <div>
                  <div className="text-[11px] uppercase tracking-[0.2em] text-white/30">
                    {loading
                      ? "Searching live sources"
                      : searched
                        ? "Live results"
                        : "Ready"}
                  </div>

                  <h3 className="mt-1 text-xl font-semibold tracking-tight">
                    {searched
                      ? "Opportunities for you"
                      : "Search the live market"}
                  </h3>
                </div>

                {loading && (
                  <div className="mt-4">
                    <ResultSkeleton />
                  </div>
                )}

                {!searched &&
                  !loading && (
                    <div className="mt-4 rounded-[24px] border border-white/8 bg-white/[0.02] p-10 text-center">
                      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.04]">
                        <Search
                          size={22}
                          className="text-white/40"
                        />
                      </div>

                      <h4 className="mt-5 text-lg font-semibold">
                        Ready to search
                      </h4>

                      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-white/35">
                        Search across CareerPilot&apos;s connected sources and inspect every source independently.
                      </p>
                    </div>
                  )}

                {searched &&
                  !loading &&
                  !error &&
                  jobs.length === 0 && (
                    <div className="mt-4 rounded-[24px] border border-white/8 bg-white/[0.02] p-10 text-center">
                      <h4 className="text-lg font-semibold">
                        No matching opportunities found
                      </h4>

                      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-white/35">
                        Try a broader role, another location, or a lower salary target.
                      </p>
                    </div>
                  )}

                {!loading &&
                  jobs.length > 0 && (
                    <div className="mt-4 space-y-3">
                      {jobs.map(
                        (job) => (
                          <article
                            key={`${job.source}-${job.source_job_id}`}
                            className="group rounded-[24px] border border-white/8 bg-white/[0.02] p-5 transition hover:border-white/15 hover:bg-white/[0.035]"
                          >
                            <div className="flex flex-col gap-5 xl:flex-row xl:items-center">
                              <div className="flex min-w-0 flex-1 items-start gap-4">
                                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.04] text-sm font-semibold">
                                  {job.company
                                    .slice(0, 2)
                                    .toUpperCase()}
                                </div>

                                <div className="min-w-0 flex-1">
                                  <div className="flex flex-wrap items-center gap-2">
                                    <span className="text-[11px] uppercase tracking-[0.16em] text-white/35">
                                      {job.company}
                                    </span>

                                    <span className="rounded-full border border-white/8 bg-white/[0.02] px-2 py-0.5 text-[9px] uppercase tracking-wider text-white/35">
                                      {job.source_count}{" "}
                                      {job.source_count ===
                                      1
                                        ? "source"
                                        : "sources"}
                                    </span>

                                    {job.sources.map(
                                      (
                                        source,
                                      ) => (
                                        <span
                                          key={
                                            source
                                          }
                                          className="rounded-full border border-white/8 px-2 py-0.5 text-[9px] uppercase tracking-wider text-white/25"
                                        >
                                          {
                                            source
                                          }
                                        </span>
                                      ),
                                    )}

                                    {job.remote && (
                                      <span className="rounded-full border border-emerald-400/15 bg-emerald-400/5 px-2 py-0.5 text-[9px] uppercase tracking-wider text-emerald-200/70">
                                        Remote
                                      </span>
                                    )}
                                  </div>

                                  <h4 className="mt-1 text-base font-semibold leading-6">
                                    {job.title}
                                  </h4>

                                  <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-white/35">
                                    <span className="inline-flex items-center gap-1.5">
                                      <MapPin size={12} />

                                      {job.location.join(
                                        ", ",
                                      ) ||
                                        "Location not specified"}
                                    </span>

                                    {job.employment_type && (
                                      <>
                                        <span>•</span>

                                        <span>
                                          {
                                            job.employment_type
                                          }
                                        </span>
                                      </>
                                    )}
                                  </div>

                                  <div className="mt-4">
                                    {job.salary_status ===
                                    "MEETS_TARGET" ? (
                                      <div className="flex flex-wrap items-center gap-2">
                                        <span className="rounded-full border border-emerald-400/15 bg-emerald-400/[0.04] px-3 py-1 text-[10px] font-medium text-emerald-100/75">
                                          ✓{" "}
                                          {formatSalary(
                                            job,
                                          )}
                                        </span>

                                        {minimumSalary && (
                                          <span className="text-[10px] text-white/30">
                                            Meets ₹
                                            {
                                              minimumSalary
                                            }{" "}
                                            LPA+
                                          </span>
                                        )}
                                      </div>
                                    ) : (
                                      <div>
                                        <span className="rounded-full border border-amber-400/15 bg-amber-400/[0.04] px-3 py-1 text-[10px] font-medium text-amber-100/75">
                                          ⚠ Salary not disclosed
                                        </span>

                                        <p className="mt-2 max-w-xl text-[11px] leading-5 text-white/35">
                                          The company has not disclosed compensation.
                                          Contact the employer or recruiter directly
                                          to confirm the expected salary range.
                                        </p>
                                      </div>
                                    )}
                                  </div>

                                  {(job.strengths.length >
                                    0 ||
                                    job.skill_gaps.length >
                                      0) && (
                                    <div className="mt-4 flex flex-wrap gap-2">
                                      {job.strengths
                                        .slice(
                                          0,
                                          3,
                                        )
                                        .map(
                                          (
                                            strength,
                                          ) => (
                                            <span
                                              key={`strength-${strength}`}
                                              className="rounded-full border border-emerald-400/10 bg-emerald-400/[0.04] px-2.5 py-1 text-[10px] text-emerald-100/60"
                                            >
                                              ✓{" "}
                                              {
                                                strength
                                              }
                                            </span>
                                          ),
                                        )}

                                      {job.skill_gaps
                                        .slice(
                                          0,
                                          3,
                                        )
                                        .map(
                                          (
                                            gap,
                                          ) => (
                                            <span
                                              key={`gap-${gap}`}
                                              className="rounded-full border border-amber-400/10 bg-amber-400/[0.04] px-2.5 py-1 text-[10px] text-amber-100/60"
                                            >
                                              △{" "}
                                              {
                                                gap
                                              }
                                            </span>
                                          ),
                                        )}
                                    </div>
                                  )}
                                </div>
                              </div>

                              <div className="flex flex-wrap items-center gap-4 xl:justify-end">
                                <div className="min-w-[100px]">
                                  <div className="text-[10px] uppercase tracking-[0.18em] text-white/30">
                                    Match
                                  </div>

                                  <div className="mt-1 flex items-baseline gap-1">
                                    <span className="text-3xl font-semibold">
                                      {Math.round(
                                        job.match_score ??
                                          0,
                                      )}
                                    </span>

                                    <span className="text-xs text-white/30">
                                      /100
                                    </span>
                                  </div>
                                </div>

                                <div>
                                  <div className="text-[10px] uppercase tracking-[0.16em] text-white/30">
                                    Recommendation
                                  </div>

                                  <div
                                    className={`mt-2 inline-flex rounded-full border px-3 py-1 text-[10px] font-medium uppercase tracking-[0.12em] ${getDecisionClass(
                                      job.decision,
                                    )}`}
                                  >
                                    {formatDecision(
                                      job.decision,
                                    )}
                                  </div>
                                </div>

                                <div className="flex gap-2">
                                  <button
                                    type="button"
                                    onClick={() =>
                                      setSelectedJob(
                                        job,
                                      )
                                    }
                                    className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2.5 text-xs font-semibold text-white transition hover:bg-white/[0.08]"
                                  >
                                    Analyze match
                                  </button>

                                  <a
                                    href={
                                      job.apply_url
                                    }
                                    target="_blank"
                                    rel="noreferrer"
                                    className="rounded-xl bg-white px-4 py-2.5 text-xs font-semibold text-black transition hover:bg-white/90"
                                  >
                                    Apply ↗
                                  </a>
                                </div>
                              </div>
                            </div>
                          </article>
                        ),
                      )}
                    </div>
                  )}
              </section>
            </div>
          </div>
        </section>
      </div>

      {/* Opportunity Intelligence drawer */}
      {selectedJob && (
        <IntelligencePanel
          job={selectedJob}
          minimumSalary={
            minimumSalary.trim()
              ? Number(
                  minimumSalary,
                )
              : undefined
          }
          onClose={() =>
            setSelectedJob(
              null,
            )
          }
        />
      )}
    </main>
  );
}