
import { API_BASE_URL, DEFAULT_REQUEST_TIMEOUT_MS } from "./config";

type ApiFetchOptions = RequestInit & {
  timeoutMs?: number;
  retries?: number;
};

export class ApiError extends Error {
  readonly status: number;
  readonly requestId: string;
  readonly details: unknown;

  constructor(message: string, status: number, requestId: string, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.requestId = requestId;
    this.details = details;
  }
}

function csrfToken(): string {
  if (typeof document === "undefined") return "";
  const match = document.cookie.match(/(?:^|; )careerpilot_csrf=([^;]+)/);
  if (match) return decodeURIComponent(match[1]);
  const token = crypto.randomUUID();
  document.cookie = `careerpilot_csrf=${encodeURIComponent(token)}; Path=/; SameSite=Lax`;
  return token;
}

function retryDelay(response: Response, attempt: number): number {
  const retryAfter = Number(response.headers.get("Retry-After"));
  if (Number.isFinite(retryAfter) && retryAfter >= 0) return Math.min(retryAfter * 1000, 10_000);
  return Math.min(500 * 2 ** attempt, 8_000);
}

async function parseBody(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text.slice(0, 1000);
  }
}

function friendlyMessage(status: number, body: unknown): string {
  if (status === 401) return "Your CareerPilot session has expired. Please refresh and try again.";
  if (status === 403) return "You are not authorized to perform this action.";
  if (status === 413) return "The submitted file or payload is too large.";
  if (status === 422 && body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail?: unknown }).detail;
    if (Array.isArray(detail)) {
      return detail
        .map((item) => {
          if (!item || typeof item !== "object") return String(item);
          const record = item as { loc?: unknown; msg?: unknown };
          const loc = Array.isArray(record.loc) ? record.loc.slice(1).join(".") : "field";
          return `${loc}: ${String(record.msg ?? "Invalid value")}`;
        })
        .join("; ");
    }
  }
  if (body && typeof body === "object") {
    const record = body as Record<string, unknown>;
    for (const key of ["detail", "message", "error"]) {
      if (typeof record[key] === "string" && record[key].trim()) return record[key] as string;
    }
  }
  if (typeof body === "string" && body.trim()) return body.trim();
  return `CareerPilot request failed (${status}).`;
}

export async function apiFetch(
  path: string,
  init: ApiFetchOptions = {},
): Promise<Response> {
  if (typeof navigator !== "undefined" && navigator.onLine === false) {
    throw new ApiError("You appear to be offline. Reconnect and try again.", 0, "offline");
  }

  const timeoutMs = init.timeoutMs ?? DEFAULT_REQUEST_TIMEOUT_MS;
  const retries = init.retries ?? 1;
  const requestId = crypto.randomUUID();
  const controller = new AbortController();
  const callerSignal = init.signal;
  const onAbort = () => controller.abort(callerSignal?.reason);
  callerSignal?.addEventListener("abort", onAbort, { once: true });

  const headers = new Headers(init.headers);
  headers.set("X-Request-ID", requestId);
  headers.set("X-Correlation-ID", requestId);
  headers.set("Cache-Control", "no-cache, no-store, must-revalidate");
  headers.set("X-CSRF-Token", csrfToken());

  const method = (init.method ?? "GET").toUpperCase();
  if (method !== "GET" && method !== "HEAD" && method !== "OPTIONS") {
    headers.set("X-Idempotency-Key", headers.get("X-Idempotency-Key") ?? requestId);
  }

  try {
    for (let attempt = 0; attempt <= retries; attempt += 1) {
      const timeout = window.setTimeout(() => controller.abort("timeout"), timeoutMs);
      try {
        const response = await fetch(`${API_BASE_URL}${path}`, {
          ...init,
          headers,
          credentials: "include",
          cache: "no-store",
          signal: controller.signal,
        });

        if (response.status === 429 && attempt < retries) {
          await new Promise((resolve) => window.setTimeout(resolve, retryDelay(response, attempt)));
          continue;
        }

        if (!response.ok) {
          const body = await parseBody(response);
          throw new ApiError(friendlyMessage(response.status, body), response.status, requestId, body);
        }

        return response;
      } finally {
        window.clearTimeout(timeout);
      }
    }
  } finally {
    callerSignal?.removeEventListener("abort", onAbort);
  }

  throw new ApiError("Request could not be completed.", 0, requestId);
}

export async function apiJson<T>(path: string, init: ApiFetchOptions = {}): Promise<T> {
  const response = await apiFetch(path, init);
  return (await response.json()) as T;
}
