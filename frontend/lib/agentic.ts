import {
  API_BASE_URL,
  DEFAULT_REQUEST_TIMEOUT_MS,
} from "./config";
import { apiFetch } from "./apiClient";
import { z } from "zod";

export type LifecycleState =
  | "PENDING"
  | "DISPATCHED"
  | "AGENT_EXECUTION"
  | "VALIDATING"
  | "COMPLETED"
  | "PARTIAL"
  | "FAILED";

export type LLMValidationStatus =
  | "PENDING"
  | "ACCEPTED"
  | "REJECTED"
  | "FAILED";

export type RewriteEvidenceStatus =
  | "SUPPORTED"
  | "PARTIAL"
  | "UNSUPPORTED";

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

export interface KnowledgeEvidence {
  evidence_id: string;
  source_id: string;
  publisher: string;
  title: string;
  category: string;
  topics: string[];
  url: string;
  resolved_url: string;
  retrieval_method: string;
  relevance: number;
  text: string;
}

export interface SkillGap {
  skill: string;
  category?: string;
  required?: boolean;
  evidence?: string[];
}

export interface RewriteCandidate {
  id: string;
  section: string;
  source_text: string;
  rewritten_text: string;
  target_requirement: string;
  evidence: string[];
  confidence: number;
  validation_status?: LLMValidationStatus;
  evidence_status?: RewriteEvidenceStatus;
}

export interface CareerRecommendation {
  id: string;
  title: string;
  action: string;
  priority: string | number;
  rationale: string;
  category?: string;
}

export interface NextAction {
  action: string;
  title?: string;
  reason?: string;
  priority?: string | number | null;
  type?: string;
}

export interface FinalValidation {
  valid: boolean;
  status: string;
  issues?: string[];
  warnings?: string[];
  checked_by?: string;
  evidence_grounded?: boolean;
}

export interface WorkflowError {
  agent: string;
  error_code: string;
  message: string;
  timestamp: string;
}

export interface AgenticRunResponse {
  request_id: string;
  thread_id: string;
  status: LifecycleState | string;
  current_agent?: string | null;
  agents_used: string[];
  tools_used: string[];
  delegation_trace: DelegationTrace[];
  career_knowledge_evidence: KnowledgeEvidence[];
  candidate_intelligence?: Record<string, unknown> | null;
  resume_intelligence?: Record<string, unknown> | null;
  ats_analysis?: Record<string, unknown> | null;
  job_fit_analysis?: Record<string, unknown> | null;
  rewrite_analysis?: Record<string, unknown> | null;
  rewrite_candidates: RewriteCandidate[];
  validated_rewrites: RewriteCandidate[];
  job?: Record<string, unknown> | null;
  job_requirements?: Record<string, unknown> | null;
  skill_gaps: SkillGap[];
  career_strategy?: Record<string, unknown> | null;
  recommendations: CareerRecommendation[];
  next_action?: NextAction | null;
  final_validation?: FinalValidation | null;
  final_response?: Record<string, unknown> | null;
  retry_count?: number | null;
  errors: WorkflowError[];
}


const AgenticRunResponseSchema = z.object({
  request_id: z.string(),
  thread_id: z.string(),
  status: z.string(),
  agents_used: z.array(z.string()),
  tools_used: z.array(z.string()).default([]),
  delegation_trace: z.array(z.object({ from_agent: z.string(), to_agent: z.string(), status: z.string() })).default([]),
  career_knowledge_evidence: z.array(z.unknown()).default([]),
  rewrite_candidates: z.array(z.unknown()).default([]),
  validated_rewrites: z.array(z.unknown()).default([]),
  skill_gaps: z.array(z.unknown()).default([]),
  recommendations: z.array(z.unknown()).default([]),
  errors: z.array(z.unknown()).default([]),
}).passthrough();

async function ensureSession(): Promise<void> {
  await apiFetch("/career-twin/session", { timeoutMs: 10_000 });
}

async function parseError(
  response: Response,
  fallback: string,
): Promise<string> {
  const raw =
    await response
      .text()
      .catch(() => "");

  if (
    response.status === 401
  ) {
    return "Your CareerPilot session has expired. Refresh the page and try again.";
  }

  if (
    response.status === 413
  ) {
    return "The uploaded resume is larger than the 10 MB limit.";
  }

  try {
    const data =
      raw
        ? (JSON.parse(raw) as {
            detail?: unknown;
            message?: unknown;
          })
        : null;

    const detail =
      typeof data?.detail ===
      "string"
        ? data.detail
        : typeof data?.message ===
            "string"
          ? data.message
          : "";

    if (detail) {
      return detail;
    }
  } catch {
    // Continue to sanitized raw response.
  }

  return (
    raw
      .replace(/\s+/g, " ")
      .trim()
      .slice(0, 400) ||
    fallback
  );
}

async function request(
  input: RequestInfo | URL,
  init: RequestInit,
  timeoutMs = DEFAULT_REQUEST_TIMEOUT_MS,
  signal?: AbortSignal,
) {
  const raw = String(input);
  const path = raw.startsWith(API_BASE_URL) ? raw.slice(API_BASE_URL.length) : raw;
  return apiFetch(path, { ...init, timeoutMs, signal, retries: 1 });
}

export async function runAgenticWorkflow(
  payload: AgenticRunRequest,
  signal?: AbortSignal,
): Promise<AgenticRunResponse> {
  await ensureSession();

  const response =
    await request(
      `${API_BASE_URL}/agentic/run`,
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
          payload,
        ),
      },
      30_000,
      signal,
    );

  if (!response.ok) {
    if (signal?.aborted) {
      throw new DOMException(
        "Workflow cancelled.",
        "AbortError",
      );
    }

    throw new Error(
      await parseError(
        response,
        `CareerPilot agentic request failed (${response.status})`,
      ),
    );
  }

  const parsed = AgenticRunResponseSchema.parse(await response.json());
  return parsed as AgenticRunResponse;
}

export async function checkAgenticHealth() {
  const response =
    await request(
      `${API_BASE_URL}/agentic/health`,
      {
        cache: "no-store",
        credentials: "include",
        headers: {
          "Cache-Control":
            "no-cache",
        },
      },
    );

  if (!response.ok) {
    throw new Error(
      await parseError(
        response,
        "Agentic health check failed.",
      ),
    );
  }

  return response.json();
}

export async function readRawErrorText(
  response: Response,
): Promise<string> {
  const rawText = await response.text();
  return rawText.trim().slice(0, 400);
}

