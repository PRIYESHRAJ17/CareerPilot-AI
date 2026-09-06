"use client";

import type {
  ChangeEvent,
  DragEvent,
  ReactNode,
} from "react";

import {
  AlertCircle,
  ArrowRight,
  BriefcaseBusiness,
  Check,
  CheckCircle2,
  ChevronDown,
  CircleAlert,
  Copy,
  FileText,
  GraduationCap,
  Lightbulb,
  Loader2,
  Mail,
  MapPin,
  Phone,
  Search,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Target,
  Upload,
  WandSparkles,
  X,
} from "lucide-react";

import {
  useRef,
  useState,
} from "react";

import {
  analyzeResume,
  analyzeResumeForJob,
  type JobResumeRequirement,
  type LLMResumeReasoningResult,
  type LLMRewriteCandidate,
  type ResumeAnalysisResponse,
  type ResumeEducation,
  type ResumeExperience,
  type ResumeJobAnalysisResponse,
  type RewriteSuggestion,
} from "@/lib/api";

type ActiveTab = "resume" | "job";

type JobView =
  | "overview"
  | "requirements"
  | "rewrite"
  | "ai";


/* ============================================================
   HELPERS
============================================================ */

function clampScore(
  value: unknown,
): number {
  if (
    typeof value !== "number" ||
    Number.isNaN(value)
  ) {
    return 0;
  }

  return Math.max(
    0,
    Math.min(
      100,
      value,
    ),
  );
}


function scoreLabel(
  value: unknown,
): string {
  const score =
    clampScore(value);

  if (score >= 85) {
    return "Excellent";
  }

  if (score >= 70) {
    return "Strong";
  }

  if (score >= 50) {
    return "Developing";
  }

  return "Needs attention";
}


function scoreTextClass(
  value: unknown,
): string {
  const score =
    clampScore(value);

  if (score >= 85) {
    return "text-emerald-300";
  }

  if (score >= 70) {
    return "text-cyan-300";
  }

  if (score >= 50) {
    return "text-amber-300";
  }

  return "text-rose-300";
}


function scoreBarClass(
  value: unknown,
): string {
  const score =
    clampScore(value);

  if (score >= 85) {
    return "bg-emerald-400";
  }

  if (score >= 70) {
    return "bg-cyan-400";
  }

  if (score >= 50) {
    return "bg-amber-400";
  }

  return "bg-rose-400";
}


function safeNumber(
  value: unknown,
): number {
  return typeof value === "number"
    ? value
    : 0;
}


function safeString(
  value: unknown,
): string {
  return typeof value === "string"
    ? value
    : "";
}


function safeArray<T>(
  value: unknown,
): T[] {
  return Array.isArray(value)
    ? (value as T[])
    : [];
}


function uniqueStrings(
  values: string[],
): string[] {
  return Array.from(
    new Set(
      values
        .map(
          (value) =>
            value.trim(),
        )
        .filter(Boolean),
    ),
  );
}


function formatFileSize(
  bytes: number,
): string {
  return `${(
    bytes /
    1024 /
    1024
  ).toFixed(2)} MB`;
}


function sectionLabel(
  value: string,
): string {
  const labels: Record<
    string,
    string
  > = {
    contact: "Contact",
    summary: "Summary",
    experience: "Experience",
    education: "Education",
    skills: "Skills",
    projects: "Projects",
    certifications:
      "Certifications",
    achievements:
      "Achievements",
  };

  return (
    labels[value] ??
    value
      .replaceAll(
        "_",
        " ",
      )
      .replace(
        /\b\w/g,
        (char) =>
          char.toUpperCase(),
      )
  );
}


function getSectionEntries(
  value: unknown,
): {
  name: string;
  score: number;
  strengths: string[];
  issues: string[];
  recommendations: string[];
}[] {
  if (
    !value ||
    typeof value !== "object"
  ) {
    return [];
  }

  if (
    Array.isArray(value)
  ) {
    return value.map(
      (
        item,
        index,
      ) => {
        const raw =
          item &&
          typeof item ===
            "object"
            ? (
                item as Record<
                  string,
                  unknown
                >
              )
            : {};

        return {
          name:
            safeString(
              raw.section,
            ) ||
            `section_${index + 1}`,

          score:
            safeNumber(
              raw.score,
            ),

          strengths:
            safeArray<string>(
              raw.strengths,
            ),

          issues:
            safeArray<string>(
              raw.issues,
            ),

          recommendations:
            safeArray<string>(
              raw.recommendations,
            ),
        };
      },
    );
  }

  return Object.entries(
    value as Record<
      string,
      unknown
    >,
  ).map(
    ([
      name,
      item,
    ]) => {
      const raw =
        item &&
        typeof item ===
          "object"
          ? (
              item as Record<
                string,
                unknown
              >
            )
          : {};

      return {
        name,

        score:
          safeNumber(
            raw.score,
          ),

        strengths:
          safeArray<string>(
            raw.strengths,
          ),

        issues:
          safeArray<string>(
            raw.issues,
          ),

        recommendations:
          safeArray<string>(
            raw.recommendations,
          ),
      };
    },
  );
}


/* ============================================================
   PAGE
============================================================ */

export default function ResumePage() {
  const [
    activeTab,
    setActiveTab,
  ] = useState<ActiveTab>(
    "resume",
  );

  const [
    selectedFile,
    setSelectedFile,
  ] = useState<File | null>(
    null,
  );

  const [
    resumeResult,
    setResumeResult,
  ] =
    useState<ResumeAnalysisResponse | null>(
      null,
    );

  const [
    jobResult,
    setJobResult,
  ] =
    useState<ResumeJobAnalysisResponse | null>(
      null,
    );

  const [
    jobDescription,
    setJobDescription,
  ] = useState("");

  const [
    resumeLoading,
    setResumeLoading,
  ] = useState(false);

  const [
    jobLoading,
    setJobLoading,
  ] = useState(false);

  const [
    resumeError,
    setResumeError,
  ] = useState("");

  const [
    jobError,
    setJobError,
  ] = useState("");

  const [
    isDragging,
    setIsDragging,
  ] = useState(false);

  const [
    expandedExperience,
    setExpandedExperience,
  ] = useState<
    number | null
  >(null);

  const fileInputRef =
    useRef<HTMLInputElement | null>(
      null,
    );


  /* ==========================================================
     FILE
  ========================================================== */

  function selectFile(
    file?: File,
  ) {
    if (!file) {
      return;
    }

    setResumeError("");
    setJobError("");

    setResumeResult(
      null,
    );

    setJobResult(
      null,
    );

    if (
      file.type !==
      "application/pdf"
    ) {
      setSelectedFile(
        null,
      );

      setResumeError(
        "Please upload a PDF resume.",
      );

      return;
    }

    const maximumSize =
      10 *
      1024 *
      1024;

    if (
      file.size >
      maximumSize
    ) {
      setSelectedFile(
        null,
      );

      setResumeError(
        "The PDF must be smaller than 10 MB.",
      );

      return;
    }

    setSelectedFile(
      file,
    );
  }


  function handleFileChange(
    event: ChangeEvent<HTMLInputElement>,
  ) {
    selectFile(
      event.target.files?.[0],
    );
  }


  function handleDrop(
    event: DragEvent<HTMLDivElement>,
  ) {
    event.preventDefault();

    setIsDragging(
      false,
    );

    selectFile(
      event.dataTransfer.files?.[0],
    );
  }


  /* ==========================================================
     RESUME ANALYSIS
  ========================================================== */

  async function handleResumeAnalysis() {
    if (!selectedFile) {
      setResumeError(
        "Please choose a PDF resume first.",
      );

      return;
    }

    setResumeLoading(
      true,
    );

    setResumeError("");

    try {
      const result =
        await analyzeResume(
          selectedFile,
        );

      setResumeResult(
        result,
      );
    } catch (error) {
      setResumeError(
        error instanceof Error
          ? error.message
          : "Unable to analyze the resume.",
      );
    } finally {
      setResumeLoading(
        false,
      );
    }
  }


  /* ==========================================================
     JOB ANALYSIS
  ========================================================== */

  async function handleJobAnalysis() {
    if (!selectedFile) {
      setJobError(
        "Please choose a PDF resume first.",
      );

      return;
    }

    if (
      !jobDescription.trim()
    ) {
      setJobError(
        "Please paste a job description first.",
      );

      return;
    }

    setJobLoading(
      true,
    );

    setJobError("");

    try {
      const result =
        await analyzeResumeForJob(
          selectedFile,
          jobDescription,
        );

      setJobResult(
        result,
      );
    } catch (error) {
      setJobError(
        error instanceof Error
          ? error.message
          : "Unable to analyze the resume for this job.",
      );
    } finally {
      setJobLoading(
        false,
      );
    }
  }


  /* ==========================================================
     RESET
  ========================================================== */

  function resetAll() {
    setSelectedFile(
      null,
    );

    setResumeResult(
      null,
    );

    setJobResult(
      null,
    );

    setJobDescription(
      "",
    );

    setResumeError(
      "",
    );

    setJobError(
      "",
    );

    setExpandedExperience(
      null,
    );

    if (
      fileInputRef.current
    ) {
      fileInputRef.current.value =
        "";
    }
  }


  /* ==========================================================
     RENDER
  ========================================================== */

  return (
    <main className="min-h-screen bg-[#080a0f] text-white">

      <div className="mx-auto max-w-7xl px-5 py-8 sm:px-8 lg:px-10">

        {/* ==================================================
            HEADER
        ================================================== */}

        <header className="border-b border-white/10 pb-8">

          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">

            <div>

              <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.2em] text-white/35">
                <Sparkles className="h-3.5 w-3.5" />
                CareerPilot Intelligence
              </div>

              <h1 className="mt-3 text-4xl font-semibold tracking-tight sm:text-5xl">
                Resume Intelligence
              </h1>

              <p className="mt-4 max-w-3xl text-sm leading-7 text-white/45">
                Turn your resume into structured career evidence,
                evaluate its quality, compare it against a real job,
                and discover exactly what should be improved.
              </p>

            </div>


            {selectedFile && (
              <button
                type="button"
                onClick={
                  resetAll
                }
                className="inline-flex items-center justify-center gap-2 self-start rounded-xl border border-white/10 bg-white/[0.04] px-4 py-2.5 text-sm text-white/65 transition hover:bg-white/[0.08] hover:text-white lg:self-auto"
              >
                <X className="h-4 w-4" />
                Start over
              </button>
            )}

          </div>

        </header>


        {/* ==================================================
            TABS
        ================================================== */}

        <div className="mt-7 inline-flex rounded-2xl border border-white/10 bg-white/[0.025] p-1">

          <button
            type="button"
            onClick={() =>
              setActiveTab(
                "resume",
              )
            }
            className={`inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-medium transition ${
              activeTab ===
              "resume"
                ? "bg-white/[0.09] text-white"
                : "text-white/40 hover:text-white/75"
            }`}
          >
            <Sparkles className="h-4 w-4" />
            Resume Analysis
          </button>


          <button
            type="button"
            onClick={() =>
              setActiveTab(
                "job",
              )
            }
            className={`inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-medium transition ${
              activeTab ===
              "job"
                ? "bg-white/[0.09] text-white"
                : "text-white/40 hover:text-white/75"
            }`}
          >
            <Target className="h-4 w-4" />
            Job Match & Rewrite
          </button>

        </div>


        {/* ==================================================
            UPLOAD
        ================================================== */}

        <section className="mt-7">

          <div
            onDragEnter={(
              event,
            ) => {
              event.preventDefault();

              setIsDragging(
                true,
              );
            }}

            onDragOver={(
              event,
            ) => {
              event.preventDefault();

              setIsDragging(
                true,
              );
            }}

            onDragLeave={(
              event,
            ) => {
              event.preventDefault();

              setIsDragging(
                false,
              );
            }}

            onDrop={
              handleDrop
            }

            className={`rounded-3xl border p-6 transition ${
              isDragging
                ? "border-cyan-300/50 bg-cyan-300/[0.04]"
                : "border-white/10 bg-white/[0.025]"
            }`}
          >

            <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">

              <div className="flex items-start gap-4">

                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-white/[0.06]">
                  <FileText className="h-5 w-5 text-cyan-300" />
                </div>

                <div className="min-w-0">

                  <p className="text-sm font-medium text-white/85">
                    {selectedFile
                      ? selectedFile.name
                      : "Upload your resume"}
                  </p>

                  <p className="mt-1 text-xs text-white/35">
                    PDF only · maximum 10 MB · drag and drop supported
                  </p>

                  {selectedFile && (
                    <p className="mt-2 text-xs text-cyan-300/70">
                      {formatFileSize(
                        selectedFile.size,
                      )}
                    </p>
                  )}

                </div>

              </div>


              <div className="flex flex-wrap gap-3">

                <input
                  ref={
                    fileInputRef
                  }
                  type="file"
                  accept=".pdf,application/pdf"
                  onChange={
                    handleFileChange
                  }
                  className="hidden"
                />


                <button
                  type="button"
                  onClick={() =>
                    fileInputRef.current?.click()
                  }
                  className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/[0.04] px-4 py-2.5 text-sm font-medium text-white/75 transition hover:bg-white/[0.08] hover:text-white"
                >
                  <Upload className="h-4 w-4" />
                  Choose PDF
                </button>


                {activeTab ===
                  "resume" && (
                  <button
                    type="button"
                    disabled={
                      !selectedFile ||
                      resumeLoading
                    }
                    onClick={
                      handleResumeAnalysis
                    }
                    className="inline-flex items-center justify-center gap-2 rounded-xl bg-white px-5 py-2.5 text-sm font-semibold text-black transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-35"
                  >
                    {resumeLoading ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        Analyze Resume
                        <ArrowRight className="h-4 w-4" />
                      </>
                    )}
                  </button>
                )}

              </div>

            </div>


            {!selectedFile && (
              <button
                type="button"
                onClick={() =>
                  fileInputRef.current?.click()
                }
                className="mt-6 flex min-h-32 w-full items-center justify-center rounded-2xl border border-dashed border-white/10 bg-black/10 px-6 text-center transition hover:border-white/20 hover:bg-white/[0.02]"
              >
                <div>

                  <Upload className="mx-auto h-5 w-5 text-white/25" />

                  <p className="mt-2 text-sm text-white/45">
                    Drop your PDF here or click to browse
                  </p>

                  <p className="mt-1 text-xs text-white/25">
                    CareerPilot will analyze the resume through the local API.
                  </p>

                </div>
              </button>
            )}

          </div>


          {resumeError && (
            <ErrorMessage
              message={
                resumeError
              }
            />
          )}

        </section>


        {/* ==================================================
            RESUME TAB
        ================================================== */}

        {activeTab ===
          "resume" && (
          <div className="mt-7">

            {!resumeResult &&
              !resumeLoading && (
                <div className="grid gap-4 md:grid-cols-3">

                  <FeatureCard
                    icon={
                      <Search className="h-4 w-4" />
                    }
                    title="Extract"
                    text="Convert the PDF into structured career information."
                  />

                  <FeatureCard
                    icon={
                      <Sparkles className="h-4 w-4" />
                    }
                    title="Understand"
                    text="Evaluate sections, skills, impact evidence and content quality."
                  />

                  <FeatureCard
                    icon={
                      <WandSparkles className="h-4 w-4" />
                    }
                    title="Optimize"
                    text="Use the same evidence foundation for job-specific resume optimization."
                  />

                </div>
              )}


            {resumeLoading && (
              <LoadingCard
                title="Analyzing your resume"
                text="CareerPilot is extracting structure and evaluating the evidence inside your resume."
              />
            )}


            {resumeResult &&
              !resumeLoading && (
                <ResumeDashboard
                  result={
                    resumeResult
                  }
                  expandedExperience={
                    expandedExperience
                  }
                  setExpandedExperience={
                    setExpandedExperience
                  }
                />
              )}

          </div>
        )}


        {/* ==================================================
            JOB TAB
        ================================================== */}

        {activeTab ===
          "job" && (
          <div className="mt-7">

            <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">

              <div className="flex items-start gap-4">

                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-cyan-300/[0.06]">
                  <BriefcaseBusiness className="h-5 w-5 text-cyan-300" />
                </div>

                <div>

                  <p className="text-[10px] uppercase tracking-[0.18em] text-white/30">
                    Job-specific intelligence
                  </p>

                  <h2 className="mt-2 text-2xl font-semibold tracking-tight">
                    Compare your resume with a real job
                  </h2>

                  <p className="mt-2 max-w-3xl text-sm leading-6 text-white/40">
                    CareerPilot compares the resume against job
                    requirements, identifies evidence gaps, and
                    produces safe rewrite recommendations.
                  </p>

                </div>

              </div>


              <textarea
                value={
                  jobDescription
                }
                onChange={(
                  event,
                ) =>
                  setJobDescription(
                    event.target.value,
                  )
                }
                placeholder={`Paste the target job description here...

Example:

Senior AI Backend Engineer

We are looking for a backend engineer with 3+ years of experience.

Required skills:
Python
FastAPI
PostgreSQL
Docker
LangChain

Experience with LLM applications and REST APIs is preferred.`}
                className="mt-6 min-h-72 w-full resize-y rounded-2xl border border-white/10 bg-black/20 p-5 text-sm leading-6 text-white outline-none placeholder:text-white/20 focus:border-cyan-300/30"
              />


              <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">

                <p className="text-xs text-white/25">
                  {jobDescription.trim()
                    ? `${jobDescription.trim().length} characters`
                    : "Paste a complete job description for better analysis."}
                </p>


                <button
                  type="button"
                  disabled={
                    !selectedFile ||
                    !jobDescription.trim() ||
                    jobLoading
                  }
                  onClick={
                    handleJobAnalysis
                  }
                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-white px-5 py-2.5 text-sm font-semibold text-black transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-35"
                >
                  {jobLoading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Building analysis...
                    </>
                  ) : (
                    <>
                      Analyze & Rewrite
                      <ArrowRight className="h-4 w-4" />
                    </>
                  )}
                </button>

              </div>


              {jobError && (
                <ErrorMessage
                  message={
                    jobError
                  }
                />
              )}

            </section>


            {jobLoading && (
              <div className="mt-6">

                <LoadingCard
                  title="Building job-specific intelligence"
                  text="Matching requirements, evaluating resume evidence, creating rewrite recommendations, and validating AI candidates."
                />

              </div>
            )}


            {jobResult &&
              !jobLoading && (
                <JobAnalysisDashboard
                  result={
                    jobResult
                  }
                />
              )}


            {!selectedFile &&
              !jobLoading && (
                <div className="mt-6 rounded-3xl border border-white/10 bg-white/[0.02] p-6 text-sm text-white/35">
                  Upload a PDF resume above before running job-specific analysis.
                </div>
              )}

          </div>
        )}

      </div>
    </main>
  );
}


/* ============================================================
   FEATURE CARD
============================================================ */

function FeatureCard({
  icon,
  title,
  text,
}: {
  icon: ReactNode;
  title: string;
  text: string;
}) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">

      <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/[0.05] text-cyan-300">
        {icon}
      </div>

      <h3 className="mt-6 text-lg font-semibold">
        {title}
      </h3>

      <p className="mt-2 text-sm leading-6 text-white/35">
        {text}
      </p>

    </div>
  );
}


/* ============================================================
   LOADING
============================================================ */

function LoadingCard({
  title,
  text,
}: {
  title: string;
  text: string;
}) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-10">

      <div className="flex flex-col items-center text-center">

        <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.04]">
          <Loader2 className="h-6 w-6 animate-spin text-cyan-300" />
        </div>

        <h3 className="mt-5 text-lg font-semibold">
          {title}
        </h3>

        <p className="mt-2 max-w-lg text-sm leading-6 text-white/35">
          {text}
        </p>

      </div>

    </div>
  );
}


/* ============================================================
   ERROR
============================================================ */

function ErrorMessage({
  message,
}: {
  message: string;
}) {
  return (
    <div className="mt-4 flex items-start gap-3 rounded-2xl border border-rose-300/15 bg-rose-300/[0.04] p-4 text-sm text-rose-200/80">

      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />

      <span>
        {message}
      </span>

    </div>
  );
}


/* ============================================================
   RESUME DASHBOARD
============================================================ */

function ResumeDashboard({
  result,
  expandedExperience,
  setExpandedExperience,
}: {
  result: ResumeAnalysisResponse;

  expandedExperience:
    | number
    | null;

  setExpandedExperience: (
    value:
      | number
      | null,
  ) => void;
}) {
  const resume =
    result.resume;

  const intelligence =
    result.intelligence;

  const allSkills =
    uniqueStrings([
      ...safeArray<string>(
        resume.skills,
      ),

      ...safeArray<string>(
        resume.technical_skills,
      ),

      ...safeArray<string>(
        resume.soft_skills,
      ),
    ]);

  const sections =
    getSectionEntries(
      intelligence.section_scores,
    );

  const keywordQuality =
    intelligence.keyword_quality;

  const achievementAnalysis =
    intelligence.achievement_analysis;

  return (
    <div className="space-y-6">

      {/* TOP SCORE */}

      <section className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">

        <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-7">

          <div className="flex flex-col gap-6 sm:flex-row sm:items-center">

            <ScoreRing
              score={
                intelligence.overall_score
              }
            />

            <div>

              <p className="text-[10px] uppercase tracking-[0.18em] text-white/25">
                Overall resume score
              </p>

              <h2
                className={`mt-2 text-2xl font-semibold ${scoreTextClass(
                  intelligence.overall_score,
                )}`}
              >
                {scoreLabel(
                  intelligence.overall_score,
                )}
              </h2>

              <p className="mt-3 max-w-2xl text-sm leading-6 text-white/40">
                {safeString(
                  intelligence.summary,
                ) ||
                  "CareerPilot evaluated the available resume evidence."}
              </p>

            </div>

          </div>

        </div>


        <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-7">

          <p className="text-[10px] uppercase tracking-[0.18em] text-white/25">
            Resume overview
          </p>

          <p className="mt-3 truncate text-sm font-medium text-white/75">
            {result.filename}
          </p>

          <p className="mt-1 text-xs text-white/30">
            {result.page_count}{" "}
            {result.page_count ===
            1
              ? "page"
              : "pages"}
          </p>

          <div className="mt-5 grid grid-cols-2 gap-3">

            <SmallStat
              label="Skills"
              value={String(
                allSkills.length,
              )}
            />

            <SmallStat
              label="Experience"
              value={String(
                resume.experience.length,
              )}
            />

            <SmallStat
              label="Projects"
              value={String(
                resume.projects.length,
              )}
            />

            <SmallStat
              label="Education"
              value={String(
                resume.education.length,
              )}
            />

          </div>

        </div>

      </section>


      {/* SECTION SCORES */}

      {sections.length >
        0 && (
        <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-7">

          <p className="text-[10px] uppercase tracking-[0.18em] text-white/25">
            Section intelligence
          </p>

          <h2 className="mt-2 text-xl font-semibold">
            Resume quality by section
          </h2>

          <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">

            {sections.map(
              (section) => (
                <div
                  key={
                    section.name
                  }
                  className="rounded-2xl border border-white/10 bg-black/10 p-4"
                >

                  <div className="flex items-center justify-between gap-3">

                    <span className="text-sm font-medium text-white/65">
                      {sectionLabel(
                        section.name,
                      )}
                    </span>

                    <span
                      className={`text-sm font-semibold ${scoreTextClass(
                        section.score,
                      )}`}
                    >
                      {Math.round(
                        section.score,
                      )}
                    </span>

                  </div>


                  <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/[0.06]">

                    <div
                      className={`h-full rounded-full ${scoreBarClass(
                        section.score,
                      )}`}
                      style={{
                        width: `${clampScore(
                          section.score,
                        )}%`,
                      }}
                    />

                  </div>


                  <p className="mt-2 text-[11px] text-white/25">
                    {scoreLabel(
                      section.score,
                    )}
                  </p>

                </div>
              ),
            )}

          </div>

        </section>
      )}


      {/* INSIGHTS */}

      <section className="grid gap-4 lg:grid-cols-3">

        <InsightCard
          title="Strengths"
          icon={
            <CheckCircle2 className="h-4 w-4" />
          }
          items={safeArray<string>(
            intelligence.strengths,
          )}
          type="success"
        />

        <InsightCard
          title="Issues"
          icon={
            <CircleAlert className="h-4 w-4" />
          }
          items={safeArray<string>(
            intelligence.issues,
          )}
          type="warning"
        />

        <InsightCard
          title="Recommendations"
          icon={
            <Lightbulb className="h-4 w-4" />
          }
          items={safeArray<string>(
            intelligence.recommendations,
          )}
          type="info"
        />

      </section>


      {/* MISSING SECTIONS */}

      {safeArray<string>(
        intelligence.missing_sections,
      ).length >
        0 && (
        <section className="rounded-3xl border border-amber-300/10 bg-amber-300/[0.025] p-7">

          <p className="text-[10px] uppercase tracking-[0.18em] text-amber-200/40">
            Content gaps
          </p>

          <h2 className="mt-2 text-xl font-semibold">
            Sections not detected
          </h2>

          <div className="mt-5 flex flex-wrap gap-2">

            {safeArray<string>(
              intelligence.missing_sections,
            ).map(
              (section) => (
                <span
                  key={
                    section
                  }
                  className="rounded-full border border-amber-300/10 bg-amber-300/[0.04] px-3 py-1.5 text-xs text-amber-100/65"
                >
                  {sectionLabel(
                    section,
                  )}
                </span>
              ),
            )}

          </div>

        </section>
      )}


      {/* PROFILE */}

      <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-7">

        <p className="text-[10px] uppercase tracking-[0.18em] text-white/25">
          Structured profile
        </p>

        <h2 className="mt-2 text-xl font-semibold">
          What CareerPilot extracted
        </h2>

        <div className="mt-6 grid gap-4 lg:grid-cols-2">

          <ProfileCard
            title="Contact"
          >
            <div className="space-y-3">

              {resume.contact.name && (
                <ProfileRow
                  icon={
                    <FileText className="h-3.5 w-3.5" />
                  }
                  text={
                    resume.contact.name
                  }
                />
              )}

              {resume.contact.email && (
                <ProfileRow
                  icon={
                    <Mail className="h-3.5 w-3.5" />
                  }
                  text={
                    resume.contact.email
                  }
                />
              )}

              {resume.contact.phone && (
                <ProfileRow
                  icon={
                    <Phone className="h-3.5 w-3.5" />
                  }
                  text={
                    resume.contact.phone
                  }
                />
              )}

              {resume.contact.location && (
                <ProfileRow
                  icon={
                    <MapPin className="h-3.5 w-3.5" />
                  }
                  text={
                    resume.contact.location
                  }
                />
              )}

            </div>
          </ProfileCard>


          <ProfileCard
            title="Professional positioning"
          >

            <p className="text-sm font-medium text-white/75">
              {resume.headline ||
                "No distinct headline detected."}
            </p>

            <p className="mt-4 whitespace-pre-line text-sm leading-6 text-white/40">
              {resume.summary ||
                "No professional summary detected."}
            </p>

          </ProfileCard>

        </div>

      </section>


      {/* SKILLS */}

      <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-7">

        <p className="text-[10px] uppercase tracking-[0.18em] text-white/25">
          Skill intelligence
        </p>

        <h2 className="mt-2 text-xl font-semibold">
          Detected capabilities
        </h2>

        {allSkills.length >
        0 ? (
          <div className="mt-5 flex flex-wrap gap-2">

            {allSkills.map(
              (
                skill,
                index,
              ) => (
                <span
                  key={`${skill}-${index}`}
                  className="rounded-full border border-white/10 bg-white/[0.035] px-3 py-1.5 text-xs text-white/60"
                >
                  {skill}
                </span>
              ),
            )}

          </div>
        ) : (
          <p className="mt-4 text-sm text-white/30">
            No skills were detected.
          </p>
        )}


        {keywordQuality && (
          <div className="mt-6 grid gap-3 sm:grid-cols-3">

            <SmallStat
              label="Recognized keywords"
              value={String(
                safeNumber(
                  keywordQuality[
                    "recognized_keyword_count"
                  ],
                ),
              )}
            />

            <SmallStat
              label="Listed skills"
              value={String(
                safeNumber(
                  keywordQuality[
                    "listed_skill_count"
                  ],
                ),
              )}
            />

            <SmallStat
              label="Keyword diversity"
              value={`${Math.round(
                safeNumber(
                  keywordQuality[
                    "keyword_diversity"
                  ],
                ),
              )}%`}
            />

          </div>
        )}

      </section>


      {/* EXPERIENCE */}

      <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-7">

        <div className="flex items-center gap-3">

          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/[0.05]">
            <BriefcaseBusiness className="h-4 w-4 text-cyan-300" />
          </div>

          <div>

            <p className="text-[10px] uppercase tracking-[0.18em] text-white/25">
              Experience
            </p>

            <h2 className="mt-1 text-xl font-semibold">
              Career history
            </h2>

          </div>

        </div>


        {resume.experience.length ===
        0 ? (
          <p className="mt-5 text-sm text-white/30">
            No experience entries were detected.
          </p>
        ) : (
          <div className="mt-6 space-y-3">

            {resume.experience.map(
              (
                experience: ResumeExperience,
                index,
              ) => {

                const expanded =
                  expandedExperience ===
                  index;

                const achievements =
                  safeArray<string>(
                    experience.achievements,
                  );

                const technologies =
                  safeArray<string>(
                    experience.technologies,
                  );

                return (
                  <div
                    key={`${experience.job_title}-${experience.company}-${index}`}
                    className="rounded-2xl border border-white/10 bg-black/10"
                  >

                    <button
                      type="button"
                      onClick={() =>
                        setExpandedExperience(
                          expanded
                            ? null
                            : index,
                        )
                      }
                      className="flex w-full items-center justify-between gap-4 p-5 text-left"
                    >

                      <div className="min-w-0">

                        <p className="text-sm font-medium text-white/80">
                          {experience.job_title ||
                            "Role not detected"}
                        </p>

                        <p className="mt-1 text-xs text-white/35">
                          {experience.company ||
                            "Company not detected"}

                          {experience.location
                            ? ` · ${experience.location}`
                            : ""}
                        </p>

                        {(experience.start_date ||
                          experience.end_date) && (
                          <p className="mt-2 text-[11px] text-white/25">
                            {experience.start_date ||
                              "Unknown"}{" "}
                            →{" "}
                            {experience.end_date ||
                              "Unknown"}
                          </p>
                        )}

                      </div>


                      <ChevronDown
                        className={`h-4 w-4 shrink-0 text-white/30 transition ${
                          expanded
                            ? "rotate-180"
                            : ""
                        }`}
                      />

                    </button>


                    {expanded && (
                      <div className="border-t border-white/10 px-5 pb-5 pt-4">

                        {experience.description && (
                          <p className="whitespace-pre-line text-sm leading-6 text-white/40">
                            {
                              experience.description
                            }
                          </p>
                        )}


                        {achievements.length >
                          0 && (
                          <div className="mt-4">

                            <p className="text-[10px] uppercase tracking-[0.14em] text-white/20">
                              Evidence
                            </p>

                            <div className="mt-2 space-y-2">

                              {achievements.map(
                                (
                                  achievement,
                                  achievementIndex,
                                ) => (
                                  <p
                                    key={`${achievement}-${achievementIndex}`}
                                    className="text-sm leading-6 text-white/40"
                                  >
                                    {
                                      achievement
                                    }
                                  </p>
                                ),
                              )}

                            </div>

                          </div>
                        )}


                        {technologies.length >
                          0 && (
                          <div className="mt-4 flex flex-wrap gap-2">

                            {technologies.map(
                              (
                                technology,
                                technologyIndex,
                              ) => (
                                <span
                                  key={`${technology}-${technologyIndex}`}
                                  className="rounded-full bg-white/[0.05] px-2.5 py-1 text-[11px] text-white/45"
                                >
                                  {
                                    technology
                                  }
                                </span>
                              ),
                            )}

                          </div>
                        )}

                      </div>
                    )}

                  </div>
                );
              },
            )}

          </div>
        )}

      </section>


      {/* EDUCATION */}

      <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-7">

        <div className="flex items-center gap-3">

          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/[0.05]">
            <GraduationCap className="h-4 w-4 text-cyan-300" />
          </div>

          <div>

            <p className="text-[10px] uppercase tracking-[0.18em] text-white/25">
              Education
            </p>

            <h2 className="mt-1 text-xl font-semibold">
              Academic background
            </h2>

          </div>

        </div>


        {resume.education.length ===
        0 ? (
          <p className="mt-5 text-sm text-white/30">
            No education entries were detected.
          </p>
        ) : (
          <div className="mt-6 grid gap-3 md:grid-cols-2">

            {resume.education.map(
              (
                education: ResumeEducation,
                index,
              ) => (
                <div
                  key={`${education.institution}-${index}`}
                  className="rounded-2xl border border-white/10 bg-black/10 p-5"
                >

                  <p className="text-sm font-medium text-white/75">
                    {education.degree ||
                      "Degree not detected"}
                  </p>

                  {education.field_of_study && (
                    <p className="mt-1 text-xs text-cyan-300/60">
                      {
                        education.field_of_study
                      }
                    </p>
                  )}

                  <p className="mt-3 text-sm text-white/45">
                    {education.institution ||
                      "Institution not detected"}
                  </p>

                  {education.location && (
                    <p className="mt-1 text-xs text-white/25">
                      {
                        education.location
                      }
                    </p>
                  )}

                  {education.grade && (
                    <p className="mt-3 text-xs text-white/30">
                      Grade:{" "}
                      {education.grade}
                    </p>
                  )}

                </div>
              ),
            )}

          </div>
        )}

      </section>


      {/* IMPACT */}

      {achievementAnalysis && (
        <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-7">

          <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">

            <div>

              <p className="text-[10px] uppercase tracking-[0.18em] text-white/25">
                Impact intelligence
              </p>

              <h2 className="mt-2 text-xl font-semibold">
                Evidence behind your bullets
              </h2>

            </div>


            <span
              className={`text-2xl font-semibold ${scoreTextClass(
                achievementAnalysis[
                  "impact_evidence_score"
                ],
              )}`}
            >
              {Math.round(
                safeNumber(
                  achievementAnalysis[
                    "impact_evidence_score"
                  ],
                ),
              )}

              <span className="text-sm text-white/20">
                /100
              </span>
            </span>

          </div>


          <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">

            <SmallStat
              label="Total bullets"
              value={String(
                safeNumber(
                  achievementAnalysis[
                    "total_bullets"
                  ],
                ),
              )}
            />

            <SmallStat
              label="Action-oriented"
              value={String(
                safeNumber(
                  achievementAnalysis[
                    "action_oriented"
                  ],
                ),
              )}
            />

            <SmallStat
              label="Quantified"
              value={String(
                safeNumber(
                  achievementAnalysis[
                    "quantified"
                  ],
                ),
              )}
            />

            <SmallStat
              label="Technology supported"
              value={String(
                safeNumber(
                  achievementAnalysis[
                    "technology_supported"
                  ],
                ),
              )}
            />

          </div>

        </section>
      )}

    </div>
  );
}


/* ============================================================
   JOB ANALYSIS DASHBOARD
============================================================ */

function JobAnalysisDashboard({
  result,
}: {
  result: ResumeJobAnalysisResponse;
}) {
  const [
    activeView,
    setActiveView,
  ] = useState<JobView>(
    "overview",
  );

  const job =
    result.job_resume_analysis;

  const ats =
    result.ats_analysis;

  const rewrite =
    result.rewrite_analysis;

  const llmReasoning =
    result.llm_reasoning;

  return (
    <div className="mt-6 space-y-6">

      {/* SCORE CARDS */}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">

        <MetricCard
          label="ATS Score"
          score={
            ats?.overall_score
          }
          description="Keyword and structural alignment"
        />

        <MetricCard
          label="Job Fit"
          score={
            job.overall_fit_score
          }
          description="Evidence-backed job suitability"
        />

        <MetricCard
          label="Rewrite Readiness"
          score={
            rewrite.overall_readiness_score
          }
          description="Quality of current resume content"
        />

        <ReasoningMetricCard
          accepted={
            llmReasoning?.accepted_count ??
            0
          }
          rejected={
            llmReasoning?.rejected_count ??
            0
          }
        />

      </section>


      {/* TARGET ROLE */}

      <section className="rounded-3xl border border-cyan-300/10 bg-cyan-300/[0.025] p-7">

        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">

          <div>

            <p className="text-[10px] uppercase tracking-[0.18em] text-cyan-200/40">
              Target role
            </p>

            <h2 className="mt-2 text-2xl font-semibold">
              {job.target_role ||
                "Target job"}
            </h2>

            <p className="mt-3 max-w-4xl text-sm leading-6 text-white/40">
              {job.summary}
            </p>

          </div>


          <div className="shrink-0 rounded-2xl border border-white/10 bg-black/10 px-5 py-4">

            <p className="text-[10px] uppercase tracking-[0.14em] text-white/25">
              Evidence strength
            </p>

            <p
              className={`mt-2 text-3xl font-semibold ${scoreTextClass(
                job.evidence_score,
              )}`}
            >
              {Math.round(
                clampScore(
                  job.evidence_score,
                ),
              )}

              <span className="text-sm text-white/20">
                /100
              </span>
            </p>

          </div>

        </div>

      </section>


      {/* ALIGNMENT BREAKDOWN */}

      <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-7">

        <p className="text-[10px] uppercase tracking-[0.18em] text-white/25">
          Job alignment breakdown
        </p>

        <div className="mt-6 grid gap-5 md:grid-cols-2">

          <ScoreRow
            label="Keyword alignment"
            score={
              job.keyword_alignment_score
            }
          />

          <ScoreRow
            label="Experience alignment"
            score={
              job.experience_alignment_score
            }
          />

          <ScoreRow
            label="Section relevance"
            score={
              job.section_relevance_score
            }
          />

          <ScoreRow
            label="ATS keyword coverage"
            score={
              ats?.keyword_coverage_score
            }
          />

        </div>

      </section>


      {/* INNER NAVIGATION */}

      <div className="inline-flex max-w-full flex-wrap rounded-2xl border border-white/10 bg-white/[0.025] p-1">

        {(
          [
            [
              "overview",
              "Overview",
            ],

            [
              "requirements",
              "Requirements",
            ],

            [
              "rewrite",
              "Rewrite",
            ],

            [
              "ai",
              "AI Reasoning",
            ],
          ] as [
            JobView,
            string,
          ][]
        ).map(
          ([
            view,
            label,
          ]) => (
            <button
              key={view}
              type="button"
              onClick={() =>
                setActiveView(
                  view,
                )
              }
              className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm transition ${
                activeView ===
                view
                  ? "bg-white/[0.09] text-white"
                  : "text-white/40 hover:text-white/75"
              }`}
            >

              {view ===
                "rewrite" && (
                <WandSparkles className="h-3.5 w-3.5" />
              )}

              {view ===
                "ai" && (
                <ShieldCheck className="h-3.5 w-3.5" />
              )}

              {label}

            </button>
          ),
        )}

      </div>


      {activeView ===
        "overview" && (
        <JobOverview
          result={
            result
          }
        />
      )}


      {activeView ===
        "requirements" && (
        <JobRequirements
          result={
            result
          }
        />
      )}


      {activeView ===
        "rewrite" && (
        <RewriteDashboard
          rewrite={
            rewrite
          }
        />
      )}


      {activeView ===
        "ai" && (
        <AIReasoningDashboard
          reasoning={
            llmReasoning
          }
        />
      )}

    </div>
  );
}


/* ============================================================
   JOB OVERVIEW
============================================================ */

function JobOverview({
  result,
}: {
  result: ResumeJobAnalysisResponse;
}) {
  const job =
    result.job_resume_analysis;

  return (
    <div className="space-y-6">

      <section className="grid gap-4 lg:grid-cols-3">

        <MatchColumn
          title="Strong matches"
          subtitle="Clear resume evidence"
          icon={
            <CheckCircle2 className="h-4 w-4 text-emerald-300" />
          }
          items={
            job.strong_matches
          }
          tone="success"
        />

        <MatchColumn
          title="Partial matches"
          subtitle="Related but not fully proven"
          icon={
            <CircleAlert className="h-4 w-4 text-amber-300" />
          }
          items={
            job.partial_matches
          }
          tone="warning"
        />

        <MatchColumn
          title="Missing"
          subtitle="Evidence not found"
          icon={
            <ShieldAlert className="h-4 w-4 text-rose-300" />
          }
          items={
            job.missing_requirements
          }
          tone="danger"
        />

      </section>


      <section className="grid gap-4 lg:grid-cols-2">

        <InsightCard
          title="Top priorities"
          icon={
            <Target className="h-4 w-4" />
          }
          items={
            job.top_priorities
          }
          type="info"
        />

        <InsightCard
          title="Recommendations"
          icon={
            <Lightbulb className="h-4 w-4" />
          }
          items={
            job.recommendations
          }
          type="success"
        />

      </section>

    </div>
  );
}


/* ============================================================
   JOB REQUIREMENTS
============================================================ */

function JobRequirements({
  result,
}: {
  result: ResumeJobAnalysisResponse;
}) {
  const job =
    result.job_resume_analysis;

  const requirements = [
    ...job.strong_matches,
    ...job.partial_matches,
    ...job.missing_requirements,
  ];

  return (
    <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-7">

      <p className="text-[10px] uppercase tracking-[0.18em] text-white/25">
        Requirement intelligence
      </p>

      <h2 className="mt-2 text-xl font-semibold">
        What your resume actually proves
      </h2>

      <p className="mt-2 max-w-3xl text-sm leading-6 text-white/35">
        Every requirement is evaluated against evidence already
        present in the structured resume.
      </p>


      <div className="mt-6 space-y-3">

        {requirements.length ===
        0 ? (
          <p className="text-sm text-white/30">
            No individual requirements were detected.
          </p>
        ) : (
          requirements.map(
            (
              requirement,
              index,
            ) => (
              <RequirementCard
                key={`${requirement.requirement}-${index}`}
                requirement={
                  requirement
                }
              />
            ),
          )
        )}

      </div>

    </section>
  );
}


/* ============================================================
   REWRITE DASHBOARD
============================================================ */

function RewriteDashboard({
  rewrite,
}: {
  rewrite: {
    overall_readiness_score: number;
    suggestions: RewriteSuggestion[];
    priority_actions: string[];
    safety_notes: string[];
    summary: string;
  };
}) {
  return (
    <div className="space-y-6">

      {/* HEADER */}

      <section className="rounded-3xl border border-violet-300/10 bg-violet-300/[0.025] p-7">

        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">

          <div>

            <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-violet-200/40">
              <WandSparkles className="h-3.5 w-3.5" />
              Evidence-based rewrite engine
            </div>

            <h2 className="mt-3 text-2xl font-semibold">
              Rewrite with evidence, not hallucinations
            </h2>

            <p className="mt-3 max-w-3xl text-sm leading-6 text-white/40">
              CareerPilot improves wording and job alignment
              using evidence that already exists in the resume.
            </p>

          </div>


          <div className="shrink-0 rounded-2xl border border-white/10 bg-black/10 p-5 text-center">

            <p className="text-[10px] uppercase tracking-[0.14em] text-white/25">
              Rewrite readiness
            </p>

            <p
              className={`mt-2 text-4xl font-semibold ${scoreTextClass(
                rewrite.overall_readiness_score,
              )}`}
            >
              {Math.round(
                clampScore(
                  rewrite.overall_readiness_score,
                ),
              )}
            </p>

            <p className="text-[10px] text-white/20">
              /100
            </p>

          </div>

        </div>


        <p className="mt-6 max-w-4xl text-sm leading-6 text-white/40">
          {rewrite.summary}
        </p>

      </section>


      {/* PRIORITIES */}

      <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-7">

        <p className="text-[10px] uppercase tracking-[0.18em] text-white/25">
          Priority actions
        </p>

        <div className="mt-5 space-y-3">

          {rewrite.priority_actions.length ===
          0 ? (
            <p className="text-sm text-white/25">
              No priority actions were identified.
            </p>
          ) : (
            rewrite.priority_actions.map(
              (
                action,
                index,
              ) => (
                <div
                  key={`${action}-${index}`}
                  className="flex items-start gap-3 rounded-2xl border border-white/10 bg-black/10 p-4"
                >

                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-cyan-300/10 text-xs text-cyan-200">
                    {index + 1}
                  </span>

                  <p className="text-sm leading-6 text-white/50">
                    {action}
                  </p>

                </div>
              ),
            )
          )}

        </div>

      </section>


      {/* REWRITE SUGGESTIONS */}

      <section>

        <div className="flex items-end justify-between gap-4">

          <div>

            <p className="text-[10px] uppercase tracking-[0.18em] text-white/25">
              Rewrite candidates
            </p>

            <h2 className="mt-2 text-xl font-semibold">
              Evidence-backed improvements
            </h2>

          </div>


          <p className="text-xs text-white/25">
            {rewrite.suggestions.length} candidate
            {rewrite.suggestions.length ===
            1
              ? ""
              : "s"}
          </p>

        </div>


        <div className="mt-5 space-y-4">

          {rewrite.suggestions.length ===
          0 ? (
            <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-7 text-sm text-white/35">
              No obvious rewrite candidates were identified.
            </div>
          ) : (
            rewrite.suggestions.map(
              (
                suggestion,
                index,
              ) => (
                <RewriteCard
                  key={`${suggestion.section}-${suggestion.source_text}-${index}`}
                  suggestion={
                    suggestion
                  }
                />
              ),
            )
          )}

        </div>

      </section>


      {/* SAFETY */}

      <section className="rounded-3xl border border-emerald-300/10 bg-emerald-300/[0.02] p-7">

        <div className="flex items-start gap-3">

          <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-emerald-300" />

          <div>

            <p className="text-sm font-medium text-white/75">
              Rewrite safety rules
            </p>

            <div className="mt-4 space-y-2">

              {rewrite.safety_notes.map(
                (
                  note,
                  index,
                ) => (
                  <p
                    key={`${note}-${index}`}
                    className="text-xs leading-5 text-white/40"
                  >
                    • {note}
                  </p>
                ),
              )}

            </div>

          </div>

        </div>

      </section>

    </div>
  );
}


/* ============================================================
   REWRITE CARD
============================================================ */

function RewriteCard({
  suggestion,
}: {
  suggestion: RewriteSuggestion;
}) {
  const [
    copied,
    setCopied,
  ] = useState(false);


  async function copyRewrite() {
    try {
      await navigator.clipboard.writeText(
        suggestion.suggested_rewrite,
      );

      setCopied(
        true,
      );

      window.setTimeout(
        () =>
          setCopied(
            false,
          ),
        1500,
      );
    } catch {
      // Clipboard unavailable.
    }
  }


  return (
    <article className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">

        <div>

          <div className="flex flex-wrap items-center gap-2">

            <span className="rounded-full border border-cyan-300/10 bg-cyan-300/[0.04] px-2.5 py-1 text-[10px] uppercase tracking-[0.12em] text-cyan-200/60">
              {suggestion.section}
            </span>

            <span className="rounded-full border border-white/10 bg-white/[0.03] px-2.5 py-1 text-[10px] uppercase tracking-[0.12em] text-white/30">
              {suggestion.evidence_status}
            </span>

          </div>

          <h3 className="mt-4 text-lg font-semibold">
            Resume rewrite recommendation
          </h3>

        </div>


        <div className="flex items-center gap-3">

          <div className="text-right">

            <p className="text-[10px] uppercase tracking-[0.12em] text-white/20">
              Confidence
            </p>

            <p
              className={`mt-1 text-lg font-semibold ${scoreTextClass(
                suggestion.confidence,
              )}`}
            >
              {Math.round(
                clampScore(
                  suggestion.confidence,
                ),
              )}
              %
            </p>

          </div>


          <button
            type="button"
            onClick={
              copyRewrite
            }
            className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2 text-xs text-white/50 transition hover:bg-white/[0.08] hover:text-white"
          >
            {copied ? (
              <>
                <Check className="h-3.5 w-3.5" />
                Copied
              </>
            ) : (
              <>
                <Copy className="h-3.5 w-3.5" />
                Copy
              </>
            )}
          </button>

        </div>

      </div>


      <div className="mt-6 grid gap-4 xl:grid-cols-2">

        <div className="rounded-2xl border border-rose-300/10 bg-rose-300/[0.025] p-5">

          <p className="text-[10px] uppercase tracking-[0.14em] text-rose-200/40">
            Original
          </p>

          <p className="mt-3 text-sm leading-6 text-white/50">
            {suggestion.source_text}
          </p>

        </div>


        <div className="rounded-2xl border border-emerald-300/10 bg-emerald-300/[0.025] p-5">

          <p className="text-[10px] uppercase tracking-[0.14em] text-emerald-200/40">
            Suggested rewrite
          </p>

          <p className="mt-3 text-sm font-medium leading-6 text-white/70">
            {suggestion.suggested_rewrite}
          </p>

        </div>

      </div>


      <div className="mt-4 grid gap-4 lg:grid-cols-2">

        <div className="rounded-2xl border border-white/10 bg-black/10 p-5">

          <p className="text-[10px] uppercase tracking-[0.14em] text-white/20">
            Why it needs improvement
          </p>

          <p className="mt-3 text-sm leading-6 text-white/45">
            {suggestion.issue}
          </p>

        </div>


        <div className="rounded-2xl border border-white/10 bg-black/10 p-5">

          <p className="text-[10px] uppercase tracking-[0.14em] text-white/20">
            Target requirement
          </p>

          <p className="mt-3 text-sm leading-6 text-white/45">
            {suggestion.target_requirement ||
              "General resume quality improvement"}
          </p>

        </div>

      </div>


      <div className="mt-4 rounded-2xl border border-white/10 bg-white/[0.018] p-5">

        <p className="text-[10px] uppercase tracking-[0.14em] text-white/20">
          Evidence used
        </p>

        <div className="mt-3 space-y-2">

          {safeArray<string>(
            suggestion.available_evidence,
          ).map(
            (
              evidence,
              index,
            ) => (
              <div
                key={`${evidence}-${index}`}
                className="flex items-start gap-2"
              >

                <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-cyan-300/60" />

                <p className="text-xs leading-5 text-white/40">
                  {evidence}
                </p>

              </div>
            ),
          )}

        </div>

      </div>

    </article>
  );
}


/* ============================================================
   AI REASONING DASHBOARD
============================================================ */

function AIReasoningDashboard({
  reasoning,
}: {
  reasoning: LLMResumeReasoningResult;
}) {
  const candidates =
    safeArray<LLMRewriteCandidate>(
      reasoning?.candidates,
    );

  const accepted =
    Math.max(
      0,
      safeNumber(
        reasoning?.accepted_count,
      ),
    );

  const rejected =
    Math.max(
      0,
      safeNumber(
        reasoning?.rejected_count,
      ),
    );

  const total =
    candidates.length ||
    accepted +
      rejected;

  const validationRate =
    total > 0
      ? Math.round(
          (accepted /
            total) *
            100,
        )
      : 0;

  return (
    <div className="space-y-6">

      {/* HEADER */}

      <section className="rounded-3xl border border-emerald-300/10 bg-emerald-300/[0.025] p-7">

        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">

          <div className="max-w-3xl">

            <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-emerald-200/45">
              <ShieldCheck className="h-3.5 w-3.5" />
              AI reasoning & validation
            </div>

            <h2 className="mt-3 text-2xl font-semibold">
              Evidence-validated resume rewrites
            </h2>

            <p className="mt-3 text-sm leading-6 text-white/40">
              CareerPilot evaluates rewrite candidates against
              the original resume evidence before they are
              marked as safe to use.
            </p>

          </div>


          <div className="grid grid-cols-3 gap-2 sm:gap-3">

            <ReasoningStat
              label="Candidates"
              value={String(
                total,
              )}
            />

            <ReasoningStat
              label="Accepted"
              value={String(
                accepted,
              )}
              tone="success"
            />

            <ReasoningStat
              label="Rejected"
              value={String(
                rejected,
              )}
              tone="danger"
            />

          </div>

        </div>


        <div className="mt-7">

          <div className="flex items-center justify-between gap-4">

            <p className="text-xs text-white/35">
              Validation pass rate
            </p>

            <p className="text-sm font-semibold text-emerald-300">
              {validationRate}%
            </p>

          </div>


          <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/[0.06]">

            <div
              className="h-full rounded-full bg-emerald-400 transition-all"
              style={{
                width: `${validationRate}%`,
              }}
            />

          </div>

        </div>

      </section>


      {/* PROVIDER STATUS */}

      <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">

        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">

          <div>

            <p className="text-[10px] uppercase tracking-[0.16em] text-white/25">
              Reasoning provider
            </p>

            <p className="mt-2 text-sm font-medium text-white/70">
              {reasoning?.provider ||
                "none"}
            </p>

          </div>


          <div>

            <p className="text-[10px] uppercase tracking-[0.16em] text-white/25">
              Model
            </p>

            <p className="mt-2 text-sm font-medium text-white/70">
              {reasoning?.model ||
                "none"}
            </p>

          </div>


          <div className="rounded-xl border border-cyan-300/10 bg-cyan-300/[0.035] px-4 py-3">

            <div className="flex items-center gap-2">

              <ShieldCheck className="h-4 w-4 text-cyan-300" />

              <p className="text-xs text-cyan-100/70">
                Evidence validation active
              </p>

            </div>

          </div>

        </div>


        {reasoning?.summary && (
          <p className="mt-5 border-t border-white/10 pt-5 text-sm leading-6 text-white/40">
            {
              reasoning.summary
            }
          </p>
        )}

      </section>


      {/* CANDIDATES */}

      <section>

        <div className="flex items-end justify-between gap-4">

          <div>

            <p className="text-[10px] uppercase tracking-[0.18em] text-white/25">
              Validation results
            </p>

            <h2 className="mt-2 text-xl font-semibold">
              AI rewrite candidates
            </h2>

          </div>


          <p className="text-xs text-white/25">
            {total} candidate
            {total === 1
              ? ""
              : "s"}
          </p>

        </div>


        <div className="mt-5 space-y-4">

          {candidates.length ===
          0 ? (
            <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-7">

              <div className="flex items-start gap-3">

                <CircleAlert className="mt-0.5 h-5 w-5 text-white/30" />

                <div>

                  <p className="text-sm font-medium text-white/60">
                    No AI rewrite candidates were produced.
                  </p>

                  <p className="mt-2 text-xs leading-5 text-white/30">
                    The deterministic rewrite layer did not
                    identify a candidate that reached this
                    validation stage.
                  </p>

                </div>

              </div>

            </div>
          ) : (
            candidates.map(
              (
                candidate,
                index,
              ) => (
                <AIReasoningCandidateCard
                  key={`${candidate.section}-${candidate.source_text}-${index}`}
                  candidate={
                    candidate
                  }
                />
              ),
            )
          )}

        </div>

      </section>


      {/* SAFETY */}

      {safeArray<string>(
        reasoning?.safety_notes,
      ).length >
        0 && (
        <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-7">

          <div className="flex items-start gap-3">

            <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-cyan-300" />

            <div className="min-w-0">

              <p className="text-sm font-medium text-white/75">
                Validation safeguards
              </p>

              <div className="mt-4 space-y-2">

                {safeArray<string>(
                  reasoning.safety_notes,
                ).map(
                  (
                    note,
                    index,
                  ) => (
                    <div
                      key={`${note}-${index}`}
                      className="flex items-start gap-2"
                    >

                      <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-300/65" />

                      <p className="text-xs leading-5 text-white/40">
                        {note}
                      </p>

                    </div>
                  ),
                )}

              </div>

            </div>

          </div>

        </section>
      )}

    </div>
  );
}


/* ============================================================
   AI REASONING CANDIDATE CARD
============================================================ */

function AIReasoningCandidateCard({
  candidate,
}: {
  candidate: LLMRewriteCandidate;
}) {
  const status =
    safeString(
      candidate.validation_status,
    ).toUpperCase();

  const isAccepted =
    status ===
    "ACCEPTED";

  const isRejected =
    status ===
    "REJECTED";

  const statusClass =
    isAccepted
      ? "border-emerald-300/10 bg-emerald-300/[0.025]"
      : isRejected
        ? "border-rose-300/10 bg-rose-300/[0.025]"
        : "border-amber-300/10 bg-amber-300/[0.025]";

  const badgeClass =
    isAccepted
      ? "border-emerald-300/10 bg-emerald-300/[0.05] text-emerald-200/75"
      : isRejected
        ? "border-rose-300/10 bg-rose-300/[0.05] text-rose-200/75"
        : "border-amber-300/10 bg-amber-300/[0.05] text-amber-200/75";

  const statusIcon =
    isAccepted ? (
      <CheckCircle2 className="h-4 w-4" />
    ) : isRejected ? (
      <ShieldAlert className="h-4 w-4" />
    ) : (
      <CircleAlert className="h-4 w-4" />
    );

  return (
    <article
      className={`rounded-3xl border p-6 ${statusClass}`}
    >

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">

        <div>

          <div className="flex flex-wrap items-center gap-2">

            <span className="rounded-full border border-cyan-300/10 bg-cyan-300/[0.04] px-2.5 py-1 text-[10px] uppercase tracking-[0.12em] text-cyan-200/60">
              {candidate.section}
            </span>

            <span className="rounded-full border border-white/10 bg-white/[0.03] px-2.5 py-1 text-[10px] uppercase tracking-[0.12em] text-white/30">
              {candidate.target_requirement ||
                "General improvement"}
            </span>

          </div>


          <h3 className="mt-4 text-lg font-semibold">
            Reasoning candidate
          </h3>

        </div>


        <div className="flex flex-wrap items-center gap-2">

          <span
            className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-[10px] font-medium uppercase tracking-[0.12em] ${badgeClass}`}
          >
            {statusIcon}
            {candidate.validation_status}
          </span>


          <span className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-white/40">
            {Math.round(
              clampScore(
                candidate.confidence,
              ),
            )}
            % confidence
          </span>

        </div>

      </div>


      <div className="mt-6 grid gap-4 xl:grid-cols-2">

        <div className="rounded-2xl border border-rose-300/10 bg-black/10 p-5">

          <p className="text-[10px] uppercase tracking-[0.14em] text-rose-200/40">
            Original evidence
          </p>

          <p className="mt-3 text-sm leading-6 text-white/50">
            {candidate.source_text}
          </p>

        </div>


        <div className="rounded-2xl border border-emerald-300/10 bg-black/10 p-5">

          <p className="text-[10px] uppercase tracking-[0.14em] text-emerald-200/40">
            Candidate rewrite
          </p>

          <p className="mt-3 text-sm font-medium leading-6 text-white/70">
            {candidate.rewritten_text}
          </p>

        </div>

      </div>


      <div className="mt-4 rounded-2xl border border-white/10 bg-black/10 p-5">

        <p className="text-[10px] uppercase tracking-[0.14em] text-white/20">
          Evidence supplied to validator
        </p>


        <div className="mt-3 space-y-2">

          {safeArray<string>(
            candidate.evidence,
          ).length >
          0 ? (
            safeArray<string>(
              candidate.evidence,
            ).map(
              (
                evidence,
                index,
              ) => (
                <div
                  key={`${evidence}-${index}`}
                  className="flex items-start gap-2"
                >

                  <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-cyan-300/60" />

                  <p className="text-xs leading-5 text-white/40">
                    {evidence}
                  </p>

                </div>
              ),
            )
          ) : (
            <p className="text-xs text-white/25">
              No explicit evidence was returned.
            </p>
          )}

        </div>

      </div>


      {safeArray<string>(
        candidate.validation_issues,
      ).length >
        0 && (
        <div className="mt-4 rounded-2xl border border-rose-300/10 bg-rose-300/[0.025] p-5">

          <div className="flex items-start gap-3">

            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-rose-300" />

            <div>

              <p className="text-sm font-medium text-rose-100/75">
                Why this candidate was rejected
              </p>

              <div className="mt-3 space-y-2">

                {safeArray<string>(
                  candidate.validation_issues,
                ).map(
                  (
                    issue,
                    index,
                  ) => (
                    <p
                      key={`${issue}-${index}`}
                      className="text-xs leading-5 text-rose-100/45"
                    >
                      • {issue}
                    </p>
                  ),
                )}

              </div>

            </div>

          </div>

        </div>
      )}


      {isAccepted && (
        <div className="mt-4 rounded-2xl border border-emerald-300/10 bg-emerald-300/[0.025] p-4">

          <div className="flex items-center gap-2">

            <ShieldCheck className="h-4 w-4 text-emerald-300" />

            <p className="text-xs font-medium text-emerald-100/70">
              Evidence validated — safe for the next resume
              optimization stage.
            </p>

          </div>

        </div>
      )}

    </article>
  );
}


/* ============================================================
   REASONING STAT
============================================================ */

function ReasoningStat({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: string;
  tone?:
    | "neutral"
    | "success"
    | "danger";
}) {
  const valueClass =
    tone ===
    "success"
      ? "text-emerald-300"
      : tone ===
          "danger"
        ? "text-rose-300"
        : "text-white/80";

  return (
    <div className="min-w-20 rounded-2xl border border-white/10 bg-black/10 px-3 py-3 text-center">

      <p className="text-[9px] uppercase tracking-[0.1em] text-white/20">
        {label}
      </p>

      <p
        className={`mt-1 text-xl font-semibold ${valueClass}`}
      >
        {value}
      </p>

    </div>
  );
}


/* ============================================================
   REASONING METRIC CARD
============================================================ */

function ReasoningMetricCard({
  accepted,
  rejected,
}: {
  accepted: number;
  rejected: number;
}) {
  const total =
    accepted +
    rejected;

  return (
    <div className="rounded-3xl border border-emerald-300/10 bg-emerald-300/[0.025] p-6">

      <p className="text-[10px] uppercase tracking-[0.18em] text-white/25">
        AI Validation
      </p>


      <div className="mt-4 flex items-end justify-between gap-4">

        <div>

          <p className="text-4xl font-semibold text-emerald-300">
            {accepted}
          </p>

          <p className="mt-1 text-xs text-white/25">
            accepted
          </p>

        </div>


        <div className="text-right">

          <p className="text-2xl font-semibold text-rose-300">
            {rejected}
          </p>

          <p className="mt-1 text-xs text-white/25">
            rejected
          </p>

        </div>

      </div>


      <p className="mt-4 text-xs leading-5 text-white/30">
        {total ===
        0
          ? "No candidates reached validation."
          : `${total} rewrite candidate${
              total ===
              1
                ? ""
                : "s"
            } checked against resume evidence.`}
      </p>

    </div>
  );
}


/* ============================================================
   REQUIREMENT CARD
============================================================ */

function RequirementCard({
  requirement,
}: {
  requirement: JobResumeRequirement;
}) {
  const status =
    requirement.status.toUpperCase();

  const isStrong =
    status ===
    "STRONG_MATCH";

  const isPartial =
    status ===
    "PARTIAL_MATCH";

  return (
    <div className="rounded-2xl border border-white/10 bg-black/10 p-5">

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">

        <div>

          <div className="flex flex-wrap gap-2">

            <span className="rounded-full border border-white/10 bg-white/[0.03] px-2.5 py-1 text-[10px] uppercase tracking-[0.08em] text-white/30">
              {
                requirement.category
              }
            </span>

            <span className="rounded-full border border-white/10 bg-white/[0.03] px-2.5 py-1 text-[10px] uppercase tracking-[0.08em] text-white/30">
              {
                requirement.importance
              }
            </span>

          </div>


          <p className="mt-3 text-sm font-medium text-white/75">
            {
              requirement.requirement
            }
          </p>

        </div>


        <span
          className={`shrink-0 rounded-full border px-3 py-1.5 text-[10px] uppercase tracking-[0.12em] ${
            isStrong
              ? "border-emerald-300/10 bg-emerald-300/[0.04] text-emerald-200/70"
              : isPartial
                ? "border-amber-300/10 bg-amber-300/[0.04] text-amber-200/70"
                : "border-rose-300/10 bg-rose-300/[0.04] text-rose-200/70"
          }`}
        >
          {status.replaceAll(
            "_",
            " ",
          )}
        </span>

      </div>


      <div className="mt-4 flex items-center gap-3">

        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/[0.06]">

          <div
            className={`h-full rounded-full ${
              isStrong
                ? "bg-emerald-400"
                : isPartial
                  ? "bg-amber-400"
                  : "bg-rose-400"
            }`}
            style={{
              width: `${clampScore(
                requirement.evidence_strength,
              )}%`,
            }}
          />

        </div>


        <span className="text-xs text-white/30">
          {Math.round(
            clampScore(
              requirement.evidence_strength,
            ),
          )}
          % evidence
        </span>

      </div>


      {requirement.evidence
        .length >
        0 && (
        <div className="mt-4 rounded-xl border border-white/10 bg-white/[0.018] p-4">

          <p className="text-[10px] uppercase tracking-[0.14em] text-white/20">
            Evidence
          </p>

          <div className="mt-2 space-y-2">

            {requirement.evidence.map(
              (
                evidence,
                index,
              ) => (
                <p
                  key={`${evidence}-${index}`}
                  className="text-xs leading-5 text-white/40"
                >
                  {evidence}
                </p>
              ),
            )}

          </div>

        </div>
      )}

    </div>
  );
}


/* ============================================================
   MATCH COLUMN
============================================================ */

function MatchColumn({
  title,
  subtitle,
  icon,
  items,
  tone,
}: {
  title: string;
  subtitle: string;
  icon: ReactNode;
  items: JobResumeRequirement[];
  tone:
    | "success"
    | "warning"
    | "danger";
}) {
  const borderClass =
    tone ===
    "success"
      ? "border-emerald-300/10"
      : tone ===
          "warning"
        ? "border-amber-300/10"
        : "border-rose-300/10";

  const dotClass =
    tone ===
    "success"
      ? "bg-emerald-300"
      : tone ===
          "warning"
        ? "bg-amber-300"
        : "bg-rose-300";

  return (
    <section
      className={`rounded-3xl border ${borderClass} bg-white/[0.025] p-6`}
    >

      <div className="flex items-start gap-3">

        <div className="mt-0.5">
          {icon}
        </div>

        <div>

          <h3 className="text-lg font-semibold">
            {title}
          </h3>

          <p className="mt-1 text-xs text-white/30">
            {subtitle}
          </p>

        </div>

      </div>


      <div className="mt-5 space-y-2">

        {items.length ===
        0 ? (
          <p className="text-sm text-white/25">
            None identified.
          </p>
        ) : (
          items
            .slice(
              0,
              8,
            )
            .map(
              (
                item,
                index,
              ) => (
                <div
                  key={`${item.requirement}-${index}`}
                  className="rounded-xl border border-white/10 bg-black/10 p-3"
                >

                  <div className="flex items-start gap-2">

                    <span
                      className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${dotClass}`}
                    />

                    <div>

                      <p className="text-xs font-medium text-white/60">
                        {
                          item.requirement
                        }
                      </p>

                      <p className="mt-1 text-[10px] uppercase tracking-[0.08em] text-white/20">
                        {
                          item.category
                        }
                      </p>

                    </div>

                  </div>

                </div>
              ),
            )
        )}

      </div>

    </section>
  );
}


/* ============================================================
   METRIC CARD
============================================================ */

function MetricCard({
  label,
  score,
  description,
}: {
  label: string;
  score: unknown;
  description: string;
}) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">

      <p className="text-[10px] uppercase tracking-[0.18em] text-white/25">
        {label}
      </p>


      <div className="mt-4 flex items-end justify-between gap-4">

        <div>

          <p
            className={`text-4xl font-semibold ${scoreTextClass(
              score,
            )}`}
          >
            {Math.round(
              clampScore(score),
            )}
          </p>

          <p className="mt-1 text-xs text-white/25">
            {scoreLabel(score)}
          </p>

        </div>


        <div className="h-12 w-12 rounded-2xl border border-white/10 bg-black/10 p-2">

          <div className="flex h-full items-end gap-1">

            {[30, 50, 70, 90].map(
              (
                height,
              ) => (
                <div
                  key={height}
                  className={`w-full rounded-sm ${
                    clampScore(
                      score,
                    ) >=
                    height
                      ? scoreBarClass(
                          score,
                        )
                      : "bg-white/[0.06]"
                  }`}
                  style={{
                    height: `${height / 2}%`,
                  }}
                />
              ),
            )}

          </div>

        </div>

      </div>


      <p className="mt-4 text-xs leading-5 text-white/30">
        {description}
      </p>

    </div>
  );
}


/* ============================================================
   SCORE RING
============================================================ */

function ScoreRing({
  score,
}: {
  score: unknown;
}) {
  const radius =
    42;

  const circumference =
    2 *
    Math.PI *
    radius;

  const normalized =
    clampScore(score);

  const offset =
    circumference -
    (normalized /
      100) *
      circumference;

  return (
    <div className="relative h-32 w-32 shrink-0">

      <svg
        viewBox="0 0 100 100"
        className="-rotate-90"
      >

        <circle
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth="7"
        />


        <circle
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          stroke="currentColor"
          className={scoreTextClass(
            normalized,
          )}
          strokeWidth="7"
          strokeLinecap="round"
          strokeDasharray={
            circumference
          }
          strokeDashoffset={
            offset
          }
        />

      </svg>


      <div className="absolute inset-0 flex flex-col items-center justify-center">

        <span
          className={`text-3xl font-semibold ${scoreTextClass(
            normalized,
          )}`}
        >
          {Math.round(
            normalized,
          )}
        </span>

        <span className="text-[10px] uppercase tracking-[0.12em] text-white/20">
          / 100
        </span>

      </div>

    </div>
  );
}


/* ============================================================
   SCORE ROW
============================================================ */

function ScoreRow({
  label,
  score,
}: {
  label: string;
  score: unknown;
}) {
  return (
    <div>

      <div className="flex items-center justify-between">

        <span className="text-sm text-white/50">
          {label}
        </span>

        <span
          className={`text-sm font-semibold ${scoreTextClass(
            score,
          )}`}
        >
          {Math.round(
            clampScore(score),
          )}
        </span>

      </div>


      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/[0.06]">

        <div
          className={`h-full rounded-full ${scoreBarClass(
            score,
          )}`}
          style={{
            width: `${clampScore(
              score,
            )}%`,
          }}
        />

      </div>

    </div>
  );
}


/* ============================================================
   SMALL STAT
============================================================ */

function SmallStat({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/10 p-4">

      <p className="text-[10px] uppercase tracking-[0.12em] text-white/20">
        {label}
      </p>

      <p className="mt-2 text-xl font-semibold text-white/75">
        {value}
      </p>

    </div>
  );
}


/* ============================================================
   PROFILE CARD
============================================================ */

function ProfileCard({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/10 p-5">

      <p className="text-[10px] uppercase tracking-[0.14em] text-white/20">
        {title}
      </p>

      <div className="mt-4">
        {children}
      </div>

    </div>
  );
}


/* ============================================================
   PROFILE ROW
============================================================ */

function ProfileRow({
  icon,
  text,
}: {
  icon: ReactNode;
  text: string;
}) {
  return (
    <div className="flex items-center gap-3">

      <span className="text-white/25">
        {icon}
      </span>

      <span className="truncate text-xs text-white/45">
        {text}
      </span>

    </div>
  );
}


/* ============================================================
   INSIGHT CARD
============================================================ */

function InsightCard({
  title,
  icon,
  items,
  type,
}: {
  title: string;
  icon: ReactNode;
  items: string[];
  type:
    | "success"
    | "warning"
    | "info";
}) {
  const iconClass =
    type ===
    "success"
      ? "text-emerald-300"
      : type ===
          "warning"
        ? "text-amber-300"
        : "text-cyan-300";

  const dotClass =
    type ===
    "success"
      ? "bg-emerald-300"
      : type ===
          "warning"
        ? "bg-amber-300"
        : "bg-cyan-300";

  return (
    <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">

      <div className="flex items-center gap-3">

        <span
          className={
            iconClass
          }
        >
          {icon}
        </span>

        <h3 className="text-sm font-semibold">
          {title}
        </h3>

      </div>


      <div className="mt-5 space-y-3">

        {items.length ===
        0 ? (
          <p className="text-xs text-white/25">
            Nothing significant detected.
          </p>
        ) : (
          items
            .slice(
              0,
              8,
            )
            .map(
              (
                item,
                index,
              ) => (
                <div
                  key={`${item}-${index}`}
                  className="flex items-start gap-2.5"
                >

                  <span
                    className={`mt-2 h-1.5 w-1.5 shrink-0 rounded-full ${dotClass}`}
                  />

                  <p className="text-xs leading-5 text-white/40">
                    {item}
                  </p>

                </div>
              ),
            )
        )}

      </div>

    </div>
  );
}