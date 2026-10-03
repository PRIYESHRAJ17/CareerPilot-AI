import {
  API_BASE_URL,
  DEFAULT_REQUEST_TIMEOUT_MS,
  RESUME_REQUEST_TIMEOUT_MS,
  isValidHttpUrl,
  normalizeConfidence,
} from "./config";
import { JobSearchRequestSchema } from "./validation";
import { apiFetch } from "./apiClient";
import { JobSearchResponseSchema, ResumeAnalysisResponseSchema, JobResumeAnalysisResponseSchema } from "./schemas";

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

export interface JobSearchResponse {
  query: string;
  location?: string | null;
  result_count: number;
  results: JobResult[];
  salary_summary: SalarySummary;
  source_summary: SourceSummary;
  candidate_intelligence?: {
    normalized_skills: string[];
    readiness_score: number;
    strengths: string[];
    recommendations: string[];
  };
  career_strategy?: Record<string, unknown>;
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

export interface StructuredResume {
  contact: {
    name?: string | null;
    email?: string | null;
    phone?: string | null;
    location?: string | null;
    website?: string | null;
    linkedin?: string | null;
    github?: string | null;
  };
  headline?: string | null;
  summary: string;
  experience: ResumeExperience[];
  education: Array<{ institution?: string; degree?: string; field?: string; start_date?: string; end_date?: string; }>;
  skills: string[];
  technical_skills: string[];
  soft_skills: string[];
  projects: Array<{ title?: string; description?: string; technologies?: string[]; url?: string }>;
  certifications: Array<{ name?: string; issuer?: string; date?: string }>;
  achievements: Array<{ title?: string; description?: string }>;
  languages: string[];
  raw_text: string;
  page_count: number;
}

export interface ResumeSectionScore {
  section: string;
  score: number;
  strengths?: string[];
  issues?: string[];
}

export interface ResumeIntelligenceResponse {
  overall_score?: number;
  section_scores?: ResumeSectionScore[];
  strengths?: string[];
  issues?: string[];
  missing_sections?: string[];
  achievement_analysis?: {
    strong?: number;
    weak?: number;
    missing?: number;
  };
  keyword_quality?: {
    matched?: string[];
    missing?: string[];
  };
  recommendations?: string[];
}

export interface ResumeAnalysisResponse {
  filename: string;
  page_count: number;
  resume: StructuredResume;
  intelligence: ResumeIntelligenceResponse;
}

export interface ATSRequirement {
  requirement?: string;
  category?: string;
  importance?: string;
  status?: string;
  evidence?: string[];
}

export interface ATSAnalysisResponse {
  overall_score?: number;
  keyword_coverage_score?: number;
  skill_match_score?: number;
  experience_alignment_score?: number;
  education_alignment_score?: number;
  section_coverage_score?: number;
  requirements?: ATSRequirement[];
  matches?: ATSRequirement[];
  missing_requirements?: ATSRequirement[];
  risk_flags?: string[];
  recommendations?: string[];
}

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

export type RewriteEvidenceStatus =
  | "SUPPORTED"
  | "PARTIAL"
  | "UNSUPPORTED";

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

export type LLMValidationStatus =
  | "PENDING"
  | "ACCEPTED"
  | "REJECTED"
  | "FAILED";

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

export interface ResumeJobAnalysisResponse {
  filename: string;
  page_count: number;
  resume: StructuredResume;
  ats_analysis: ATSAnalysisResponse;
  job_resume_analysis: JobResumeAnalysis;
  rewrite_analysis: RewriteAnalysis;
  llm_reasoning: {
    provider: string;
    model: string;
    candidates: LLMRewriteCandidate[];
    accepted_count: number;
    rejected_count: number;
    summary: string;
    safety_notes: string[];
  };
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

async function parseApiError(
  response: Response,
  fallback: string,
) {
  const raw =
    await response
      .text()
      .catch(() => "");

  if (response.status === 401) {
    return "Your CareerPilot session has expired. Refresh the page and try again.";
  }

  if (response.status === 413) {
    return "The uploaded resume exceeds the 10 MB limit.";
  }

  try {
    const payload = raw
      ? JSON.parse(raw) as {
          detail?: unknown;
          message?: unknown;
        }
      : null;

    const detail =
      typeof payload?.detail === "string"
        ? payload.detail
        : typeof payload?.message === "string"
          ? payload.message
          : "";

    if (detail) {
      return detail;
    }
  } catch {
    // sanitized raw below
  }

  return (
    raw
      .replace(/\s+/g, " ")
      .trim()
      .slice(0, 400) ||
    fallback
  );
}

async function fetchWithTimeout(
  input: RequestInfo | URL,
  init: RequestInit,
  timeoutMs = DEFAULT_REQUEST_TIMEOUT_MS,
  signal?: AbortSignal,
) {
  const url = typeof input === "string" ? input.replace(API_BASE_URL, "") : input;
  return apiFetch(String(url), { ...init, signal, timeoutMs });
}

async function ensureSession() {
  await apiFetch("/career-twin/session", { timeoutMs: 10_000 });
}

export async function searchJobs(
  request: JobSearchRequest,
  signal?: AbortSignal,
): Promise<JobSearchResponse> {
  const normalized = {
    ...request,
    skills: Array.from(
      new Set(
        request.skills
          .map((item) =>
            item.trim(),
          )
          .filter(Boolean),
      ),
    ),
    preferred_work_modes: Array.from(new Set(request.preferred_work_modes)),
    target_industries:
      Array.from(
        new Set(
          request.target_industries
            .map((item) =>
              item.trim(),
            )
            .filter(Boolean),
        ),
      ),
  };

  JobSearchRequestSchema.parse(
    normalized,
  );

  await ensureSession();

  const response =
    await fetchWithTimeout(
      `${API_BASE_URL}/jobs/search`,
      {
        method: "POST",
        credentials: "include",
        cache: "no-store",
        headers: {
          "Content-Type":
            "application/json",
          "Cache-Control":
            "no-cache",
        },
        body: JSON.stringify(
          normalized,
        ),
      },
      DEFAULT_REQUEST_TIMEOUT_MS,
      signal,
    );

  if (!response.ok) {
    throw new Error(
      await parseApiError(
        response,
        `CareerPilot search failed (${response.status})`,
      ),
    );
  }

  const data = JobSearchResponseSchema.parse(await response.json()) as unknown as JobSearchResponse;

  return {
    ...data,
    results:
      Array.isArray(data.results)
        ? data.results.map(
            (job) => ({
              ...job,
              location:
                Array.isArray(job.location)
                  ? job.location.filter(Boolean)
                  : [],
              source_records:
                Array.isArray(job.source_records)
                  ? job.source_records
                  : [],
              sources:
                Array.isArray(job.sources)
                  ? job.sources
                  : [],
              source_count:
                Number.isFinite(
                  job.source_count,
                )
                  ? job.source_count
                  : job.sources.length,
              salary_status:
                job.salary_status ??
                (
                  job.salary_disclosed &&
                  typeof request.minimum_salary_lpa ===
                    "number" &&
                  typeof job.salary_min_lpa ===
                    "number" &&
                  job.salary_min_lpa <
                    request.minimum_salary_lpa
                    ? "BELOW_TARGET"
                    : job.salary_disclosed
                      ? "MEETS_TARGET"
                      : "UNDISCLOSED"
                ),
              confidence:
                normalizeConfidence(
                  job.confidence,
                ),
              apply_url:
                isValidHttpUrl(
                  job.apply_url,
                )
                  ? job.apply_url
                  : "",
            }),
          )
        : [],
  };
}

export async function analyzeResume(
  file: File,
): Promise<ResumeAnalysisResponse> {
  const form =
    new FormData();

  form.append("file", file);

  await ensureSession();

  const response =
    await fetchWithTimeout(
      `${API_BASE_URL}/resume/analyze`,
      {
        method: "POST",
        credentials: "include",
        cache: "no-store",
        headers: {
          "Cache-Control":
            "no-cache",
        },
        body: form,
      },
      RESUME_REQUEST_TIMEOUT_MS,
    );

  if (!response.ok) {
    throw new Error(
      await parseApiError(
        response,
        "Unable to analyze the uploaded resume.",
      ),
    );
  }

  return ResumeAnalysisResponseSchema.parse(await response.json()) as unknown as ResumeAnalysisResponse;
}

export async function analyzeResumeForJob(
  file: File,
  jobDescription: string,
): Promise<ResumeJobAnalysisResponse> {
  if (!jobDescription.trim()) {
    throw new Error(
      "Please enter a job description.",
    );
  }

  const form =
    new FormData();

  form.append(
    "file",
    file,
  );

  form.append(
    "job_description",
    jobDescription,
  );

  await ensureSession();

  const response =
    await fetchWithTimeout(
      `${API_BASE_URL}/resume/ats-analyze`,
      {
        method: "POST",
        credentials: "include",
        cache: "no-store",
        headers: {
          "Cache-Control":
            "no-cache",
        },
        body: form,
      },
      RESUME_REQUEST_TIMEOUT_MS,
    );

  if (!response.ok) {
    throw new Error(
      await parseApiError(
        response,
        "Unable to analyze the resume for this job.",
      ),
    );
  }

  return JobResumeAnalysisResponseSchema.parse(await response.json()) as unknown as ResumeJobAnalysisResponse;
}

export async function checkApiHealth(): Promise<boolean> {
  try {
    const response =
      await fetchWithTimeout(
        `${API_BASE_URL}/health`,
        {
          cache: "no-store",
        },
      );

    return response.ok;
  } catch {
    return false;
  }
}
