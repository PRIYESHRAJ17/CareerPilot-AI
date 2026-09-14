const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://127.0.0.1:8000";

export interface AgenticRunRequest {
  request_id?: string;
  thread_id?: string;
  user_goal: string;
  candidate_profile?: Record<string, unknown> | null;
  resume_base64?: string | null;
  job_description?: string | null;
  job_query?: string | null;
  conversation_context?: Array<Record<string, unknown>>;
}

export interface DelegationTrace {
  from_agent: string;
  to_agent: string;
  status: string;
}

export interface AgenticRunResponse {
  request_id: string;
  thread_id: string;
  status: string;
  current_agent?: string | null;

  agents_used: string[];
  tools_used: string[];

  delegation_trace: DelegationTrace[];

  candidate_intelligence?: Record<string, unknown> | null;
  resume_intelligence?: Record<string, unknown> | null;
  ats_analysis?: Record<string, unknown> | null;
  job_fit_analysis?: Record<string, unknown> | null;
  rewrite_analysis?: Record<string, unknown> | null;

  rewrite_candidates: unknown[];
  validated_rewrites: unknown[];

  job?: Record<string, unknown> | null;
  job_requirements?: Record<string, unknown> | null;

  skill_gaps: unknown[];

  career_strategy?: Record<string, unknown> | null;

  recommendations: Array<Record<string, unknown>>;

  next_action?: Record<string, unknown> | null;

  final_validation?: Record<string, unknown> | null;

  final_response?: Record<string, unknown> | null;

  retry_count: number;

  errors: unknown[];
}

export interface AgenticHealthResponse {
  status: string;
  service: string;
  orchestration: string;
  checkpointing: string;
}


async function parseError(
  response: Response,
  fallback: string,
): Promise<string> {
  try {
    const data = await response.json();

    if (
      data &&
      typeof data.detail === "string"
    ) {
      return data.detail;
    }

    if (
      data &&
      typeof data.message === "string"
    ) {
      return data.message;
    }
  } catch {
    // Keep fallback.
  }

  return fallback;
}


export async function checkAgenticHealth(): Promise<AgenticHealthResponse> {
  const response = await fetch(
    `${API_BASE_URL}/agentic/health`,
    {
      method: "GET",
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      await parseError(
        response,
        `Agentic health check failed (${response.status})`,
      ),
    );
  }

  return (
    await response.json()
  ) as AgenticHealthResponse;
}


export async function runAgenticWorkflow(
  request: AgenticRunRequest,
): Promise<AgenticRunResponse> {
  const response = await fetch(
    `${API_BASE_URL}/agentic/run`,
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
    throw new Error(
      await parseError(
        response,
        `CareerPilot agentic request failed (${response.status})`,
      ),
    );
  }

  return (
    await response.json()
  ) as AgenticRunResponse;
}