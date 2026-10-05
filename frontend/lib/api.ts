import { apiFetch } from "./apiClient";

// ============================================================
// JOB SEARCH
// ============================================================

export interface JobSearchRequest {
  role: string;
  location?: string;
  experience_years: number;
  minimum_salary_lpa?: number;
  preferred_work_modes: string[];
  skills: string[];
  target_industries: string[];
}

export type SalaryStatus =
  | "MEETS_TARGET"
  | "UNDISCLOSED"
  | "BELOW_TARGET";

export interface MatchBreakdown {
  overall_score: number;

  role_fit: number;
  skill_fit: number;
  experience_fit: number;
  location_fit: number;
  salary_fit: number;
  career_goal_fit: number;

  semantic_score?: number | null;
  deterministic_score?: number | null;
}

export interface SourceRecord {
  source: string;
  source_job_id: string;

  company: string;
  title: string;

  location: string[];

  remote: boolean;
  employment_type?: string | null;

  apply_url: string;
  source_url: string;

  salary_min_lpa?: number | null;
  salary_max_lpa?: number | null;
  salary_currency: string;

  salary_status: SalaryStatus | string;
  salary_confidence: number;
  salary_evidence?: string | null;

  posted_at?: string | null;
}

export interface JobResult {
  source: string;
  source_job_id: string;

  sources: string[];
  source_count: number;

  source_records: SourceRecord[];

  company: string;
  title: string;
  location: string[];

  remote: boolean;
  employment_type?: string | null;

  match_score?: number | null;
  decision?: string | null;
  confidence?: number | null;

  strengths: string[];
  skill_gaps: string[];
  matched_skills: string[];

  explanation: string;

  match_breakdown?: MatchBreakdown | null;

  salary_min_lpa?: number | null;
  salary_max_lpa?: number | null;

  salary_disclosed: boolean;
  salary_status: SalaryStatus;

  salary_confidence: number;
  salary_evidence?: string | null;

  apply_url: string;
}

export interface SalarySummary {
  minimum_salary_lpa?: number | null;
  opportunities_found: number;
  salary_verified: number;
  salary_undisclosed: number;
}

export interface SourceSummary {
  connected: number;
  contributing: number;
  sources: string[];
}

// ============================================================
// CANDIDATE INTELLIGENCE
// ============================================================

export interface CandidateIntelligenceResponse {
  profile_completeness: number;

  normalized_skills: string[];

  skill_categories: Record<string, string[]>;

  strengths: string[];

  missing_information: string[];

  career_direction: string[];

  target_roles: string[];

  target_industries: string[];

  readiness_level: string;

  readiness_score: number;

  recommendations: string[];
}

// ============================================================
// CAREER STRATEGY
// ============================================================

export interface CareerStrategyResponse {
  primary_role: string;

  career_directions: string[];

  priority_skills: string[];

  improvement_areas: string[];

  recommended_actions: string[];

  strategy_summary: string;
}

// ============================================================
// JOB SEARCH RESPONSE
// ============================================================

export interface JobSearchResponse {
  query: string;

  location?: string | null;

  result_count: number;

  results: JobResult[];

  salary_summary: SalarySummary;

  source_summary: SourceSummary;

  candidate_intelligence?: CandidateIntelligenceResponse;

  career_strategy?: CareerStrategyResponse;
}

// ============================================================
// RESUME STRUCTURE
// ============================================================

export interface ResumeContact {
  name?: string | null;
  email?: string | null;
  phone?: string | null;
  location?: string | null;
  website?: string | null;
  linkedin?: string | null;
  github?: string | null;
}

export interface ResumeExperience {
  job_title?: string | null;
  company?: string | null;
  location?: string | null;

  start_date?: string | null;
  end_date?: string | null;

  description?: string;

  achievements?: string[];

  technologies?: string[];
}

export interface ResumeEducation {
  degree?: string | null;
  institution?: string | null;
  location?: string | null;

  start_date?: string | null;
  end_date?: string | null;

  field_of_study?: string | null;
  grade?: string | null;
}

export interface ResumeProject {
  name?: string | null;

  description?: string;

  technologies?: string[];

  url?: string | null;

  achievements?: string[];
}

export interface ResumeCertification {
  name: string;

  issuer?: string | null;

  issue_date?: string | null;
  expiry_date?: string | null;

  credential_id?: string | null;
  credential_url?: string | null;
}

export interface ResumeAchievement {
  title: string;

  description?: string;

  date?: string | null;
}

export interface StructuredResume {
  contact: ResumeContact;

  headline?: string | null;

  summary: string;

  experience: ResumeExperience[];

  education: ResumeEducation[];

  skills: string[];

  technical_skills: string[];

  soft_skills: string[];

  projects: ResumeProject[];

  certifications: ResumeCertification[];

  achievements: ResumeAchievement[];

  languages: string[];

  raw_text: string;

  page_count: number;
}

// ============================================================
// BASIC RESUME ANALYSIS
// ============================================================

export interface ResumeSectionScore {
  section: string;

  score: number;

  strengths?: string[];

  issues?: string[];

  recommendations?: string[];
}

export type ResumeSectionScoreMap = Record<
  string,
  Omit<ResumeSectionScore, "section">
>;

export interface ResumeIntelligenceResponse {
  overall_score?: number;

  section_scores?:
    | ResumeSectionScore[]
    | ResumeSectionScoreMap;

  strengths?: string[];

  issues?: string[];

  missing_sections?: string[];

  achievement_analysis?: Record<
    string,
    unknown
  >;

  keyword_quality?: Record<
    string,
    unknown
  >;

  recommendations?: string[];

  [key: string]: unknown;
}

export interface ResumeAnalysisResponse {
  filename: string;

  page_count: number;

  resume: StructuredResume;

  intelligence: ResumeIntelligenceResponse;
}

// ============================================================
// ATS ANALYSIS
// ============================================================

/**
 * Raw requirement extracted from the job description.
 *
 * Backend shape:
 * {
 *   text,
 *   category,
 *   normalized,
 *   importance
 * }
 */
export interface ATSRequirement {
  text?: string;

  requirement?: string;

  category?: string;

  normalized?: string;

  importance?: string;

  [key: string]: unknown;
}

/**
 * Actual resume-vs-requirement evaluation.
 *
 * Backend shape:
 * {
 *   requirement,
 *   category,
 *   status,
 *   evidence,
 *   confidence
 * }
 */
export interface ATSMatch {
  requirement: string;

  category: string;

  status: string;

  evidence: string[];

  confidence: number;

  [key: string]: unknown;
}

export interface ATSAnalysisResponse {
  overall_score?: number;

  keyword_coverage_score?: number;

  skill_match_score?: number;

  experience_alignment_score?: number;

  education_alignment_score?: number;

  section_coverage_score?: number;

  requirements?: ATSRequirement[];

  matches?: ATSMatch[];

  matched_keywords?: string[];

  missing_keywords?: string[];

  weak_keywords?: string[];

  supported_requirements?: string[];

  mentioned_only_requirements?: string[];

  missing_requirements?: string[];

  strengths?: string[];

  issues?: string[];

  recommendations?: string[];

  keyword_stuffing_risk?: boolean;

  unsupported_claim_risk?: boolean;

  summary?: string;

  [key: string]: unknown;
}

// ============================================================
// JOB-SPECIFIC RESUME ANALYSIS
// ============================================================

export interface JobResumeRequirement {
  requirement: string;

  category: string;

  importance: string;

  status: string;

  evidence: string[];

  evidence_strength: number;
}

export interface JobResumeAnalysis {
  overall_fit_score: number;

  evidence_score: number;

  keyword_alignment_score: number;

  experience_alignment_score: number;

  section_relevance_score: number;

  strong_matches: JobResumeRequirement[];

  partial_matches: JobResumeRequirement[];

  missing_requirements: JobResumeRequirement[];

  top_priorities: string[];

  recommendations: string[];

  target_role: string;

  summary: string;
}

// ============================================================
// RESUME REWRITE ENGINE
// ============================================================

export type RewriteEvidenceStatus =
  | "SUPPORTED"
  | "LIMITED_EVIDENCE"
  | "UNSUPPORTED"
  | string;

export interface RewriteSuggestion {
  section: string;

  source_text: string;

  issue: string;

  target_requirement: string;

  available_evidence: string[];

  suggested_rewrite: string;

  confidence: number;

  evidence_status: RewriteEvidenceStatus;
}

export interface RewriteAnalysis {
  overall_readiness_score: number;

  suggestions: RewriteSuggestion[];

  priority_actions: string[];

  safety_notes: string[];

  summary: string;
}

// ============================================================
// LLM RESUME REASONER
// ============================================================

export type LLMValidationStatus =
  | "PENDING"
  | "ACCEPTED"
  | "REJECTED"
  | string;

export interface LLMRewriteCandidate {
  source_text: string;

  rewritten_text: string;

  section: string;

  target_requirement: string;

  evidence: string[];

  confidence: number;

  validation_status: LLMValidationStatus;

  validation_issues: string[];
}

export interface LLMResumeReasoningResult {
  provider: string;

  model: string;

  candidates: LLMRewriteCandidate[];

  accepted_count: number;

  rejected_count: number;

  summary: string;

  safety_notes: string[];
}

// ============================================================
// COMPLETE RESUME JOB ANALYSIS RESPONSE
// ============================================================

export interface ResumeJobAnalysisResponse {
  filename: string;

  page_count: number;

  resume: StructuredResume;

  ats_analysis: ATSAnalysisResponse;

  job_resume_analysis: JobResumeAnalysis;

  rewrite_analysis: RewriteAnalysis;

  llm_reasoning: LLMResumeReasoningResult;

  rewrite_pipeline: {
    requirements_used: string[];

    evidence_first: boolean;

    hallucination_protection: boolean;

    llm_reasoning_enabled?: boolean;

    llm_provider?: string;

    llm_model?: string;

    accepted_rewrites?: number;

    rejected_rewrites?: number;
  };
}

// ============================================================
// INTERNAL HELPERS
// ============================================================

function normalizeStringArray(
  value: unknown,
): string[] {
  return Array.isArray(value)
    ? value.filter(
        (item): item is string =>
          typeof item === "string",
      )
    : [];
}

function normalizeLocationArray(
  value: unknown,
): string[] {
  return normalizeStringArray(value);
}

function normalizeNumber(
  value: unknown,
  fallback = 0,
): number {
  return typeof value === "number" &&
    Number.isFinite(value)
    ? value
    : fallback;
}

function normalizeNullableNumber(
  value: unknown,
): number | null {
  return typeof value === "number" &&
    Number.isFinite(value)
    ? value
    : null;
}

function normalizeSalaryStatus(
  job: JobResult,
  targetSalary?: number,
): SalaryStatus {
  if (!job.salary_disclosed) {
    return "UNDISCLOSED";
  }

  if (
    !targetSalary ||
    targetSalary <= 0
  ) {
    return job.salary_status ??
      "MEETS_TARGET";
  }

  const maximum =
    job.salary_max_lpa ??
    job.salary_min_lpa ??
    null;

  if (
    maximum !== null &&
    Number.isFinite(maximum)
  ) {
    return maximum >= targetSalary
      ? "MEETS_TARGET"
      : "BELOW_TARGET";
  }

  return "UNDISCLOSED";
}

function normalizeJobResult(
  job: JobResult,
  targetSalary?: number,
): JobResult {
  const normalized: JobResult = {
    ...job,

    sources:
      Array.isArray(job.sources) &&
      job.sources.length > 0
        ? normalizeStringArray(
            job.sources,
          )
        : job.source
          ? [job.source]
          : [],

    source_count:
      typeof job.source_count ===
      "number"
        ? job.source_count
        : Array.isArray(
              job.sources,
            )
          ? job.sources.length
          : job.source
            ? 1
            : 0,

    source_records:
      Array.isArray(
        job.source_records,
      )
        ? job.source_records.map(
            (record) => ({
              ...record,

              location:
                normalizeLocationArray(
                  record.location,
                ),

              salary_min_lpa:
                normalizeNullableNumber(
                  record.salary_min_lpa,
                ),

              salary_max_lpa:
                normalizeNullableNumber(
                  record.salary_max_lpa,
                ),

              salary_currency:
                record.salary_currency ||
                "INR",

              salary_status:
                record.salary_status ||
                "UNDISCLOSED",

              salary_confidence:
                normalizeNumber(
                  record.salary_confidence,
                ),

              salary_evidence:
                record.salary_evidence ??
                null,

              employment_type:
                record.employment_type ??
                null,

              posted_at:
                record.posted_at ??
                null,
            }),
          )
        : [],

    location:
      normalizeLocationArray(
        job.location,
      ),

    strengths:
      normalizeStringArray(
        job.strengths,
      ),

    skill_gaps:
      normalizeStringArray(
        job.skill_gaps,
      ),

    matched_skills:
      normalizeStringArray(
        job.matched_skills,
      ),

    explanation:
      typeof job.explanation ===
      "string"
        ? job.explanation
        : "",

    salary_disclosed:
      Boolean(
        job.salary_disclosed,
      ),

    salary_min_lpa:
      normalizeNullableNumber(
        job.salary_min_lpa,
      ),

    salary_max_lpa:
      normalizeNullableNumber(
        job.salary_max_lpa,
      ),

    salary_confidence:
      normalizeNumber(
        job.salary_confidence,
      ),

    salary_evidence:
      job.salary_evidence ?? null,

    match_score:
      normalizeNullableNumber(
        job.match_score,
      ),

    confidence:
      normalizeNullableNumber(
        job.confidence,
      ),

    decision:
      job.decision ?? null,

    match_breakdown:
      job.match_breakdown ?? null,

    employment_type:
      job.employment_type ?? null,

    salary_status:
      job.salary_status ??
      (job.salary_disclosed
        ? "MEETS_TARGET"
        : "UNDISCLOSED"),
  };

  normalized.salary_status =
    normalizeSalaryStatus(
      normalized,
      targetSalary,
    );

  return normalized;
}

// ============================================================
// SEARCH JOBS API
// ============================================================

export async function searchJobs(
  request: JobSearchRequest,
  signal?: AbortSignal,
): Promise<JobSearchResponse> {
  const response =
    await apiFetch(
      "/jobs/search",
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",
        },

        body: JSON.stringify(
          request,
        ),

        cache: "no-store",

        signal,

        timeoutMs: 120_000,

        retries: 1,
      },
    );

  const data =
    (await response.json()) as JobSearchResponse;

  const results: JobResult[] =
    Array.isArray(data.results)
      ? data.results.map(
          (job) =>
            normalizeJobResult(
              job,
              request.minimum_salary_lpa,
            ),
        )
      : [];

  return {
    query:
      typeof data.query ===
      "string"
        ? data.query
        : request.role,

    location:
      data.location ??
      request.location ??
      null,

    result_count:
      typeof data.result_count ===
      "number"
        ? data.result_count
        : results.length,

    results,

    salary_summary:
      data.salary_summary ?? {
        minimum_salary_lpa:
          request.minimum_salary_lpa ??
          null,

        opportunities_found:
          results.length,

        salary_verified: 0,

        salary_undisclosed:
          results.filter(
            (job) =>
              job.salary_status ===
              "UNDISCLOSED",
          ).length,
      },

    source_summary:
      data.source_summary ?? {
        connected: 0,

        contributing: 0,

        sources: [],
      },

    candidate_intelligence:
      data.candidate_intelligence,

    career_strategy:
      data.career_strategy,
  };
}

// ============================================================
// BASIC RESUME ANALYSIS API
// ============================================================

export async function analyzeResume(
  file: File,
): Promise<ResumeAnalysisResponse> {
  if (!file) {
    throw new Error(
      "Please select a resume file.",
    );
  }

  if (
    !file.name
      .toLowerCase()
      .endsWith(".pdf")
  ) {
    throw new Error(
      "Only PDF resumes are currently supported.",
    );
  }

  const formData =
    new FormData();

  formData.append(
    "file",
    file,
  );

  const response =
    await apiFetch(
      "/resume/analyze",
      {
        method: "POST",

        body: formData,

        cache: "no-store",

        timeoutMs: 180_000,

        retries: 0,
      },
    );

  return (
    await response.json()
  ) as ResumeAnalysisResponse;
}

// ============================================================
// COMPLETE JOB-SPECIFIC RESUME ANALYSIS API
// ============================================================

export async function analyzeResumeForJob(
  file: File,
  jobDescription: string,
): Promise<ResumeJobAnalysisResponse> {
  if (!file) {
    throw new Error(
      "Please select a resume file.",
    );
  }

  if (
    !file.name
      .toLowerCase()
      .endsWith(".pdf")
  ) {
    throw new Error(
      "Only PDF resumes are currently supported.",
    );
  }

  if (
    !jobDescription ||
    !jobDescription.trim()
  ) {
    throw new Error(
      "Please enter a job description.",
    );
  }

  const formData =
    new FormData();

  formData.append(
    "file",
    file,
  );

  formData.append(
    "job_description",
    jobDescription,
  );

  const response =
    await apiFetch(
      "/resume/ats-analyze",
      {
        method: "POST",

        body: formData,

        cache: "no-store",

        timeoutMs: 180_000,

        retries: 0,
      },
    );

  return (
    await response.json()
  ) as ResumeJobAnalysisResponse;
}

// ============================================================
// API HEALTH
// ============================================================

export async function checkApiHealth(): Promise<boolean> {
  try {
    const response =
      await apiFetch(
        "/health",
        {
          method: "GET",

          cache: "no-store",

          timeoutMs: 5_000,

          retries: 0,
        },
      );

    return response.ok;
  } catch {
    return false;
  }
}