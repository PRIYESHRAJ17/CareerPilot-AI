const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://127.0.0.1:8000";

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
}

export interface ResumeIntelligenceResponse {
  overall_score?: number;

  section_scores?: ResumeSectionScore[];

  strengths?: string[];

  issues?: string[];

  missing_sections?: string[];

  achievement_analysis?: Record<string, unknown>;

  keyword_quality?: Record<string, unknown>;

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

export interface ATSRequirement {
  requirement?: string;

  category?: string;

  importance?: string;

  status?: string;

  evidence?: string[];

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

  matches?: ATSRequirement[];

  missing_requirements?: ATSRequirement[];

  risk_flags?: string[];

  recommendations?: string[];

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

  // NEW: LLM reasoning + evidence validation
  llm_reasoning: LLMResumeReasoningResult;

  rewrite_pipeline: {
    requirements_used: string[];

    evidence_first: boolean;

    hallucination_protection: boolean;

    // New backend metadata
    llm_reasoning_enabled?: boolean;

    llm_provider?: string;

    llm_model?: string;

    accepted_rewrites?: number;

    rejected_rewrites?: number;
  };
}

// ============================================================
// SEARCH JOBS API
// ============================================================

export async function searchJobs(
  request: JobSearchRequest,
): Promise<JobSearchResponse> {
  const response = await fetch(
    `${API_BASE_URL}/jobs/search`,
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify(request),

      cache: "no-store",
    },
  );

  if (!response.ok) {
    let message =
      `CareerPilot API request failed (${response.status})`;

    try {
      const errorData =
        await response.json();

      if (
        errorData &&
        typeof errorData.detail === "string"
      ) {
        message = errorData.detail;
      }
    } catch {
      // Keep default error message.
    }

    throw new Error(message);
  }

  const data =
    (await response.json()) as JobSearchResponse;

  const results: JobResult[] =
    Array.isArray(data.results)
      ? data.results.map((job) => ({
          ...job,

          sources:
            Array.isArray(job.sources) &&
            job.sources.length > 0
              ? job.sources
              : job.source
                ? [job.source]
                : [],

          source_count:
            typeof job.source_count === "number"
              ? job.source_count
              : job.sources?.length || 1,

          source_records:
            Array.isArray(
              job.source_records,
            )
              ? job.source_records.map(
                  (record) => ({
                    ...record,

                    location:
                      Array.isArray(
                        record.location,
                      )
                        ? record.location
                        : [],

                    salary_min_lpa:
                      record.salary_min_lpa ??
                      null,

                    salary_max_lpa:
                      record.salary_max_lpa ??
                      null,

                    salary_currency:
                      record.salary_currency ||
                      "INR",

                    salary_status:
                      record.salary_status ||
                      "UNDISCLOSED",

                    salary_confidence:
                      typeof record.salary_confidence ===
                      "number"
                        ? record.salary_confidence
                        : 0,

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

          strengths:
            Array.isArray(job.strengths)
              ? job.strengths
              : [],

          skill_gaps:
            Array.isArray(job.skill_gaps)
              ? job.skill_gaps
              : [],

          matched_skills:
            Array.isArray(job.matched_skills)
              ? job.matched_skills
              : [],

          explanation:
            typeof job.explanation ===
            "string"
              ? job.explanation
              : "",

          salary_disclosed:
            Boolean(
              job.salary_disclosed,
            ),

          salary_status:
            job.salary_status ??
            (
              job.salary_disclosed
                ? "MEETS_TARGET"
                : "UNDISCLOSED"
            ),

          salary_confidence:
            typeof job.salary_confidence ===
            "number"
              ? job.salary_confidence
              : 0,

          salary_evidence:
            job.salary_evidence ??
            null,

          salary_min_lpa:
            job.salary_min_lpa ??
            null,

          salary_max_lpa:
            job.salary_max_lpa ??
            null,

          match_score:
            job.match_score ??
            null,

          confidence:
            job.confidence ??
            null,

          decision:
            job.decision ??
            null,

          match_breakdown:
            job.match_breakdown ??
            null,

          employment_type:
            job.employment_type ??
            null,
        }))
      : [];

  return {
    query: data.query,

    location:
      data.location ??
      null,

    result_count:
      data.result_count,

    results,

    salary_summary:
      data.salary_summary ?? {
        minimum_salary_lpa:
          null,

        opportunities_found:
          data.result_count ??
          results.length,

        salary_verified: 0,

        salary_undisclosed:
          results.length,
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
  const formData =
    new FormData();

  formData.append(
    "file",
    file,
  );

  const response =
    await fetch(
      `${API_BASE_URL}/resume/analyze`,
      {
        method: "POST",

        body: formData,
      },
    );

  if (!response.ok) {
    let message =
      "Unable to analyze the uploaded resume.";

    try {
      const errorData =
        await response.json();

      if (
        errorData &&
        typeof errorData.detail === "string"
      ) {
        message =
          errorData.detail;
      }
    } catch {
      // Keep fallback message.
    }

    throw new Error(message);
  }

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
    await fetch(
      `${API_BASE_URL}/resume/ats-analyze`,
      {
        method: "POST",

        body: formData,

        cache: "no-store",
      },
    );

  if (!response.ok) {
    let message =
      `CareerPilot resume analysis failed (${response.status})`;

    try {
      const errorData =
        await response.json();

      if (
        errorData &&
        typeof errorData.detail === "string"
      ) {
        message =
          errorData.detail;
      }
    } catch {
      // Keep default error.
    }

    throw new Error(message);
  }

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
      await fetch(
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