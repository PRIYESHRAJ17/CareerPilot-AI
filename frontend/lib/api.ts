const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://127.0.0.1:8000";

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
}

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
      const errorData = await response.json();

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
    location: data.location ?? null,
    result_count: data.result_count,

    results,

    salary_summary:
      data.salary_summary ?? {
        minimum_salary_lpa: null,
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
  };
}

export async function checkApiHealth(): Promise<boolean> {
  try {
    const response = await fetch(
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