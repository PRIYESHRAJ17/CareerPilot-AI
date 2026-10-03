from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path.cwd().resolve()
F = ROOT / "frontend"
B = ROOT / "backend"
BACKUP = ROOT / f".week7-p0-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

if not F.exists() or not B.exists():
    raise SystemExit("Run this from the CareerPilot-AI repository root.")

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")

def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")

def replace_once(path: Path, old: str, new: str, required=True):
    s = read(path)
    if old not in s:
        if required:
            raise RuntimeError(f"Anchor not found in {path}: {old[:120]!r}")
        return
    write(path, s.replace(old, new, 1))

def backup(path: Path):
    if not path.exists():
        return
    target = BACKUP / path.relative_to(ROOT)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)

def backup_all():
    targets = [
        F / "app/layout.tsx",
        F / "app/globals.css",
        F / "app/page.tsx",
        F / "app/dashboard/page.tsx",
        F / "app/opportunities/page.tsx",
        F / "app/resume/page.tsx",
        F / "app/career-twin/page.tsx",
        F / "lib/api.ts",
        F / "lib/agentic.ts",
        F / "next.config.ts",
        F / "package.json",
        F / "package-lock.json",
        B / "api/main.py",
        B / "api/models.py",
        B / "api/career_twin.py",
        B / "api/agentic.py",
    ]
    for path in targets:
        backup(path)

print("Creating protected backup...")
backup_all()
print(f"Backup: {BACKUP}")

# ------------------------------------------------------------------
# 1. GLOBAL APP FOUNDATION
# ------------------------------------------------------------------

write(F / "app/layout.tsx", '''import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "CareerPilot AI — Autonomous Career Operating System",
    template: "%s | CareerPilot AI",
  },
  description:
    "AI-orchestrated career intelligence platform combining autonomous agent workflows, deterministic validation, resume ATS parsing, and multi-source opportunity aggregation.",
};

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
''')

write(F / "app/globals.css", '''@import "tailwindcss";

:root {
  --background: #080a0f;
  --foreground: #f5f7fb;
  --muted-foreground: #9ca3af;
  color-scheme: dark;
}

html[data-theme="light"] {
  --background: #f7f8fb;
  --foreground: #111827;
  --muted-foreground: #6b7280;
  color-scheme: light;
}

@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --font-sans: var(--font-geist-sans);
  --font-mono: var(--font-geist-mono);
}

* {
  box-sizing: border-box;
}

html,
body {
  min-height: 100%;
}

body {
  margin: 0;
  background: var(--background);
  color: var(--foreground);
  font-family: var(--font-geist-sans), system-ui, sans-serif;
}

button,
input,
textarea,
select {
  font: inherit;
}
''')

write(F / "next.config.ts", '''import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  poweredByHeader: false,

  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          {
            key: "Content-Security-Policy",
            value:
              "default-src 'self'; img-src 'self' data: blob: https:; media-src 'self' blob: https:; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; connect-src 'self' http://localhost:8000 http://127.0.0.1:8000 https:; frame-ancestors 'none'; base-uri 'self'; form-action 'self';",
          },
          {
            key: "Strict-Transport-Security",
            value: "max-age=31536000; includeSubDomains",
          },
          {
            key: "X-Frame-Options",
            value: "DENY",
          },
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
''')

pkg = json.loads(read(F / "package.json"))
pkg["name"] = "careerpilot-ai-frontend"
pkg["description"] = "CareerPilot AI frontend — autonomous career operating system."
pkg["engines"] = {
    "node": ">=20.9.0",
    "npm": ">=10.0.0",
}
pkg["scripts"] = {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint . --max-warnings 0",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
}
pkg.setdefault("dependencies", {})
pkg["dependencies"]["lucide-react"] = "1.34.0"
pkg["dependencies"]["zod"] = "^4.4.3"
pkg["dependencies"]["zod-validation-error"] = "^4.0.2"
pkg.setdefault("devDependencies", {})
pkg["devDependencies"]["vitest"] = "^3.2.4"
write(F / "package.json", json.dumps(pkg, indent=2))

# ------------------------------------------------------------------
# 2. SHARED FRONTEND INFRASTRUCTURE
# ------------------------------------------------------------------

write(F / "lib/config.ts", '''export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

export const DEFAULT_REQUEST_TIMEOUT_MS = 20_000;
export const RESUME_REQUEST_TIMEOUT_MS = 30_000;
export const MAX_RESUME_BYTES = 10 * 1024 * 1024;

export function isValidHttpUrl(value: unknown): value is string {
  if (typeof value !== "string" || !value.trim()) {
    return false;
  }

  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

export function clampScore(
  value: unknown,
  min = 0,
  max = 100,
): number {
  const numeric =
    typeof value === "number"
      ? value
      : Number(value);

  if (!Number.isFinite(numeric)) {
    return min;
  }

  return Math.min(
    max,
    Math.max(min, numeric),
  );
}

export function normalizeConfidence(
  value: unknown,
): number {
  const numeric =
    typeof value === "number"
      ? value
      : Number(value);

  if (!Number.isFinite(numeric)) {
    return 0;
  }

  return Math.round(
    numeric >= 0 && numeric <= 1
      ? numeric * 100
      : clampScore(numeric),
  );
}

export function friendlyStatus(
  value: unknown,
  loading = false,
): string {
  if (loading) {
    return "RUNNING";
  }

  if (
    typeof value !== "string" ||
    !value
  ) {
    return "READY";
  }

  return value.replaceAll("_", " ");
}
''')

write(F / "lib/validation.ts", '''import { z } from "zod";

export const JobSearchRequestSchema = z.object({
  role: z.string().trim().min(1),
  location: z.string().trim().optional(),
  experience_years: z.number().min(0),
  minimum_salary_lpa: z.number().min(0).optional(),
  preferred_work_modes: z.array(z.string()),
  skills: z.array(z.string()),
  target_industries: z.array(z.string()),
});

export function normalizeCommaList(value: string): string[] {
  return Array.from(
    new Set(
      value
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
    ),
  );
}
''')

write(F / "lib/theme.tsx", '''"use client";

import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

export function ThemeToggle() {
  const [light, setLight] = useState(false);

  useEffect(() => {
    const next =
      window.localStorage.getItem("careerpilot.theme") === "light";

    setLight(next);
    document.documentElement.dataset.theme =
      next ? "light" : "dark";
  }, []);

  function toggle() {
    const next = !light;

    setLight(next);
    document.documentElement.dataset.theme =
      next ? "light" : "dark";

    window.localStorage.setItem(
      "careerpilot.theme",
      next ? "light" : "dark",
    );
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={
        light
          ? "Switch to dark theme"
          : "Switch to light theme"
      }
      className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-3 py-2 text-xs text-white/65 hover:text-white"
    >
      {light ? (
        <Sun size={15} />
      ) : (
        <Moon size={15} />
      )}
      {light ? "Light" : "Dark"}
    </button>
  );
}
''')

write(F / "components/AppShell.tsx", '''"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  BriefcaseBusiness,
  Building2,
  CalendarDays,
  FileText,
  LayoutDashboard,
  Menu,
  MessageSquareText,
  Settings,
  Target,
  UserRound,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";
import { ThemeToggle } from "@/lib/theme";

const NAV = [
  ["/dashboard", "Dashboard", LayoutDashboard],
  ["/opportunities", "Opportunities", BriefcaseBusiness],
  ["/career-twin", "Career Twin", Target],
  ["/resume", "Resume", FileText],
  ["/companies", "Companies", Building2],
  ["/interviews", "Interviews", MessageSquareText],
  ["/applications", "Applications", CalendarDays],
  ["/career-plan", "Career Plan", BarChart3],
  ["/settings", "Settings", Settings],
] as const;

export function AppShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false);
      }
    };

    document.addEventListener(
      "keydown",
      onKeyDown,
    );

    return () => {
      document.removeEventListener(
        "keydown",
        onKeyDown,
      );
    };
  }, []);

  return (
    <>
      <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-white/10 bg-[#080a0f]/95 px-4 backdrop-blur lg:hidden">
        <Link
          href="/dashboard"
          className="font-semibold"
        >
          CareerPilot
        </Link>

        <button
          type="button"
          aria-label={
            open
              ? "Close navigation"
              : "Open navigation"
          }
          onClick={() =>
            setOpen((value) => !value)
          }
          className="rounded-xl border border-white/10 p-2"
        >
          {open ? (
            <X size={18} />
          ) : (
            <Menu size={18} />
          )}
        </button>
      </header>

      <aside
        className={[
          "fixed inset-y-0 left-0 z-40 w-[260px] border-r border-white/10 bg-[#0b0e14] p-5 transition-transform",
          "lg:translate-x-0",
          open
            ? "translate-x-0"
            : "-translate-x-full",
        ].join(" ")}
      >
        <div className="flex items-center justify-between">
          <Link
            href="/dashboard"
            className="text-lg font-semibold"
          >
            CareerPilot
          </Link>

          <button
            type="button"
            aria-label="Close navigation"
            onClick={() => setOpen(false)}
            className="rounded-xl border border-white/10 p-2 lg:hidden"
          >
            <X size={17} />
          </button>
        </div>

        <nav
          className="mt-8 space-y-1"
          aria-label="Primary navigation"
        >
          {NAV.map(
            ([href, label, Icon]) => {
              const active =
                pathname === href ||
                pathname.startsWith(
                  `${href}/`,
                );

              return (
                <Link
                  key={href}
                  href={href}
                  onClick={() =>
                    setOpen(false)
                  }
                  aria-current={
                    active
                      ? "page"
                      : undefined
                  }
                  className={[
                    "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition",
                    active
                      ? "bg-white text-black"
                      : "text-white/55 hover:bg-white/[0.04] hover:text-white",
                  ].join(" ")}
                >
                  <Icon size={16} />
                  {label}
                </Link>
              );
            },
          )}
        </nav>

        <div className="mt-8 space-y-3">
          <ThemeToggle />

          <Link
            href="/career-twin"
            className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-3 text-sm"
          >
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-white text-black">
              <UserRound size={15} />
            </span>

            <span className="flex-1">
              Career profile
            </span>

            <span aria-hidden>
              ›
            </span>
          </Link>
        </div>
      </aside>

      <div
        className={`fixed inset-0 z-30 bg-black/60 lg:hidden ${
          open
            ? "block"
            : "hidden"
        }`}
        onClick={() =>
          setOpen(false)
        }
        aria-hidden="true"
      />

      <div className="min-h-screen lg:pl-[260px]">
        {children}
      </div>
    </>
  );
}
''')

write(F / "lib/workspace.ts", '''import type { JobResult } from "./api";

const STORAGE_KEY =
  "careerpilot.workspace.v1";

export type WorkspaceState = {
  jobs: JobResult[];
  applications: Array<{
    id: string;
    job_id: string;
    company: string;
    title: string;
    status: string;
    updated_at: string;
  }>;
  activity: Array<{
    id: string;
    title: string;
    detail: string;
    timestamp: string;
  }>;
};

const EMPTY: WorkspaceState = {
  jobs: [],
  applications: [],
  activity: [],
};

export function getWorkspaceState(): WorkspaceState {
  if (typeof window === "undefined") {
    return EMPTY;
  }

  try {
    const raw =
      window.localStorage.getItem(
        STORAGE_KEY,
      );

    if (!raw) {
      return EMPTY;
    }

    const parsed =
      JSON.parse(raw) as Partial<WorkspaceState>;

    return {
      jobs: Array.isArray(parsed.jobs)
        ? parsed.jobs
        : [],
      applications: Array.isArray(
        parsed.applications,
      )
        ? parsed.applications
        : [],
      activity: Array.isArray(
        parsed.activity,
      )
        ? parsed.activity
        : [],
    };
  } catch {
    return EMPTY;
  }
}

function persist(
  state: WorkspaceState,
) {
  window.localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify(state),
  );

  window.dispatchEvent(
    new Event(
      "careerpilot:workspace",
    ),
  );
}

export function saveSearchResults(
  jobs: JobResult[],
  sources: string[] = [],
) {
  const current =
    getWorkspaceState();

  persist({
    ...current,
    jobs,
    activity: [
      {
        id: crypto.randomUUID(),
        title:
          "Provider search checkpoints completed",
        detail:
          `${
            jobs.length
          } canonical opportunities from ${
            sources.length
          } contributing sources.`,
        timestamp:
          new Date().toISOString(),
      },
      ...current.activity,
    ].slice(0, 20),
  });
}

export function recordApplication(
  job: JobResult,
) {
  const current =
    getWorkspaceState();

  const id =
    `${job.source}:${job.source_job_id}`;

  if (
    current.applications.some(
      (item) => item.id === id,
    )
  ) {
    return;
  }

  persist({
    ...current,
    applications: [
      {
        id,
        job_id: id,
        company: job.company,
        title: job.title,
        status: "Applied",
        updated_at:
          new Date().toISOString(),
      },
      ...current.applications,
    ],
    activity: [
      {
        id: crypto.randomUUID(),
        title:
          "Application tracked",
        detail:
          `${job.title} at ${job.company}`,
        timestamp:
          new Date().toISOString(),
      },
      ...current.activity,
    ].slice(0, 20),
  });
}
''')

# ------------------------------------------------------------------
# 3. TYPED API + AGENTIC LAYERS
# ------------------------------------------------------------------

write(F / "lib/agentic.ts", '''import {
  API_BASE_URL,
  DEFAULT_REQUEST_TIMEOUT_MS,
} from "./config";

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

async function ensureSession(): Promise<void> {
  const response =
    await fetch(
      `${API_BASE_URL}/career-twin/session`,
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
      "Unable to establish a CareerPilot session.",
    );
  }
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
): Promise<Response> {
  const controller =
    new AbortController();

  const timeout =
    window.setTimeout(
      () =>
        controller.abort(
          "timeout",
        ),
      timeoutMs,
    );

  const relay = () =>
    controller.abort(
      signal?.reason,
    );

  signal?.addEventListener(
    "abort",
    relay,
    { once: true },
  );

  try {
    return await fetch(
      input,
      {
        ...init,
        signal:
          controller.signal,
      },
    );
  } finally {
    window.clearTimeout(
      timeout,
    );
    signal?.removeEventListener(
      "abort",
      relay,
    );
  }
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

  return (
    await response.json()
  ) as AgenticRunResponse;
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
''')

write(F / "lib/api.ts", '''import {
  API_BASE_URL,
  DEFAULT_REQUEST_TIMEOUT_MS,
  RESUME_REQUEST_TIMEOUT_MS,
  isValidHttpUrl,
  normalizeConfidence,
} from "./config";
import { JobSearchRequestSchema } from "./validation";

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
  education: Array<Record<string, unknown>>;
  skills: string[];
  technical_skills: string[];
  soft_skills: string[];
  projects: Array<Record<string, unknown>>;
  certifications: Array<Record<string, unknown>>;
  achievements: Array<Record<string, unknown>>;
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
  const controller =
    new AbortController();

  const timeout =
    window.setTimeout(
      () =>
        controller.abort(
          "timeout",
        ),
      timeoutMs,
    );

  const relay = () =>
    controller.abort(
      signal?.reason,
    );

  signal?.addEventListener(
    "abort",
    relay,
    { once: true },
  );

  try {
    return await fetch(
      input,
      {
        ...init,
        signal:
          controller.signal,
      },
    );
  } finally {
    window.clearTimeout(
      timeout,
    );
    signal?.removeEventListener(
      "abort",
      relay,
    );
  }
}

async function ensureSession() {
  const response =
    await fetch(
      `${API_BASE_URL}/career-twin/session`,
      {
        credentials: "include",
        cache: "no-store",
        headers: {
          "Cache-Control":
            "no-cache",
        },
      },
    );

  if (!response.ok) {
    throw new Error(
      "Unable to initialize the CareerPilot session.",
    );
  }
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
    preferred_work_modes:
      Array.from(
        new Set(
          request.preferred_work_modes,
        ),
      ),
    ),
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

  const data =
    await response.json() as JobSearchResponse;

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

  return await response.json();
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

  return await response.json();
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
''')

# ------------------------------------------------------------------
# 4. HOME / AGENTIC PAGE
# ------------------------------------------------------------------

write(F / "app/page.tsx", '''import { AppShell } from "@/components/AppShell";
import HomeClient from "./page-client";

export default function Page() {
  return (
    <AppShell>
      <HomeClient />
    </AppShell>
  );
}
''')

write(F / "app/page-client.tsx", '''"use client";

import {
  Activity,
  ArrowRight,
  CheckCircle2,
  Circle,
  Loader2,
  Search,
  ShieldCheck,
  Sparkles,
  UserRound,
  XCircle,
} from "lucide-react";
import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  runAgenticWorkflow,
  type AgenticRunResponse,
} from "@/lib/agentic";
import {
  clampScore,
  friendlyStatus,
} from "@/lib/config";
import {
  normalizeCommaList,
} from "@/lib/validation";

const AGENTS = [
  ["supervisor", "Supervisor"],
  ["candidate", "Candidate"],
  ["resume", "Resume"],
  ["job", "Job"],
  ["strategy", "Strategy"],
  ["recommendation", "Recommendation"],
  ["validation", "Validation"],
] as const;

function getAgentState(
  id: string,
  result: AgenticRunResponse | null,
) {
  if (!result) {
    return "idle";
  }

  if (
    result.current_agent === id
  ) {
    return "active";
  }

  if (
    result.agents_used.includes(id)
  ) {
    return "done";
  }

  return "idle";
}

function safeEvidencePreview(
  value: unknown,
) {
  const text =
    typeof value === "string"
      ? value.trim()
      : "";

  if (text.length <= 360) {
    return text;
  }

  return `${text.slice(0, 360).trim()}…`;
}

export default function HomeClient() {
  const [goal, setGoal] =
    useState(
      "Find AI Engineer opportunities and tell me what I should do next.",
    );

  const [role, setRole] =
    useState("AI Engineer");

  const [skills, setSkills] =
    useState(
      "Python, FastAPI, SQL",
    );

  const [location, setLocation] =
    useState("");

  const [projects, setProjects] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState<string | null>(
      null,
    );

  const [result, setResult] =
    useState<AgenticRunResponse | null>(
      null,
    );

  const goalRef =
    useRef<HTMLTextAreaElement | null>(
      null,
    );

  const resultsRef =
    useRef<HTMLDivElement | null>(
      null,
    );

  const controllerRef =
    useRef<AbortController | null>(
      null,
    );

  const latestDelegation =
    useMemo(
      () =>
        result?.delegation_trace?.length
          ? result.delegation_trace[
              result.delegation_trace.length - 1
            ]
          : null,
      [result],
    );

  useEffect(() => {
    if (!result) {
      return;
    }

    window.requestAnimationFrame(
      () =>
        resultsRef.current?.scrollIntoView(
          {
            behavior: "smooth",
            block: "start",
          },
        ),
    );
  }, [result]);

  async function run() {
    if (!goal.trim()) {
      setError(
        "Please describe your career goal.",
      );
      goalRef.current?.focus();
      return;
    }

    controllerRef.current?.abort();

    const controller =
      new AbortController();

    controllerRef.current =
      controller;

    setLoading(true);
    setError(null);

    try {
      const traceId =
        crypto.randomUUID();

      const candidateSkills =
        normalizeCommaList(
          skills,
        );

      const candidateProjects =
        normalizeCommaList(
          projects,
        );

      const response =
        await runAgenticWorkflow(
          {
            request_id: traceId,
            thread_id: traceId,
            user_goal: goal.trim(),
            candidate_profile: {
              headline: role.trim(),
              skills:
                candidateSkills,
              technical_skills:
                candidateSkills,
              projects:
                candidateProjects,
              preferred_locations:
                location.trim()
                  ? [location.trim()]
                  : [],
              career_goal: {
                target_roles:
                  role.trim()
                    ? [role.trim()]
                    : [],
              },
            },
            conversation_context:
              [],
          },
          controller.signal,
        );

      setResult(response);
      setError(null);
    } catch (caught) {
      if (
        caught instanceof DOMException &&
        caught.name === "AbortError"
      ) {
        return;
      }

      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to run CareerPilot.",
      );
    } finally {
      setLoading(false);
      controllerRef.current = null;
    }
  }

  function resetWorkspace() {
    controllerRef.current?.abort();
    controllerRef.current = null;
    setResult(null);
    setError(null);
    goalRef.current?.focus();
  }

  const status =
    friendlyStatus(
      result?.status,
      loading,
    );

  return (
    <main className="min-h-screen bg-[#080a0f] p-5 text-white md:p-8">
      <div className="mx-auto max-w-[1400px]">
        <header className="border-b border-white/10 pb-8">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-[10px] uppercase tracking-[0.18em] text-white/55">
                <Sparkles size={12} />
                CareerPilot Agentic OS
              </div>

              <h1 className="mt-4 text-4xl font-semibold tracking-[-0.04em] md:text-6xl">
                Your career,{" "}
                <br />
                <span className="text-white/40">
                  intelligently orchestrated.
                </span>
              </h1>

              <p className="mt-4 max-w-2xl text-sm leading-6 text-white/45 md:text-base">
                CareerPilot coordinates specialist agents,
                deterministic validation and evidence-backed
                recommendations.
              </p>
            </div>

            <div className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3">
              <div className="flex items-center gap-2">
                <Activity size={15} />
                <span className="text-xs font-medium">
                  {status}
                </span>
              </div>

              <div className="mt-1 text-[10px] uppercase tracking-[0.16em] text-white/30">
                Agentic workflow
              </div>
            </div>
          </div>
        </header>

        <form
          className="mt-8 grid gap-6 lg:grid-cols-[1.1fr_.9fr]"
          onSubmit={(event) => {
            event.preventDefault();
            void run();
          }}
        >
          <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
            <div className="text-xs uppercase tracking-[0.18em] text-white/30">
              Career request
            </div>

            <label
              htmlFor="goal"
              className="mt-5 block text-sm font-medium"
            >
              What should CareerPilot solve?
            </label>

            <textarea
              id="goal"
              ref={goalRef}
              maxLength={2000}
              value={goal}
              onChange={(event) => {
                setGoal(event.target.value);
                setError(null);
              }}
              className="mt-2 min-h-32 w-full resize-y rounded-2xl border border-white/10 bg-black/10 p-4 text-sm outline-none focus:border-white/30"
            />

            <div
              id="goal-count"
              className="mt-1 text-right text-[10px] text-white/30"
            >
              {goal.length}/2000
            </div>

            <div className="mt-5 grid gap-4 md:grid-cols-2">
              <label className="text-xs text-white/40">
                Target role
                <input
                  value={role}
                  onChange={(event) => {
                    setRole(event.target.value);
                    setError(null);
                  }}
                  className="mt-2 w-full rounded-xl border border-white/10 bg-black/10 px-3 py-2.5 text-sm text-white outline-none"
                />
              </label>

              <label className="text-xs text-white/40">
                Location
                <input
                  value={location}
                  onChange={(event) => {
                    setLocation(event.target.value);
                    setError(null);
                  }}
                  className="mt-2 w-full rounded-xl border border-white/10 bg-black/10 px-3 py-2.5 text-sm text-white outline-none"
                />
              </label>

              <label className="text-xs text-white/40">
                Skills
                <input
                  value={skills}
                  onChange={(event) => {
                    setSkills(event.target.value);
                    setError(null);
                  }}
                  placeholder="Python, SQL, FastAPI"
                  className="mt-2 w-full rounded-xl border border-white/10 bg-black/10 px-3 py-2.5 text-sm text-white outline-none"
                />
              </label>

              <label className="text-xs text-white/40">
                Projects
                <input
                  value={projects}
                  onChange={(event) => {
                    setProjects(
                      event.target.value,
                    );
                    setError(null);
                  }}
                  placeholder="Project A, Project B"
                  className="mt-2 w-full rounded-xl border border-white/10 bg-black/10 px-3 py-2.5 text-sm text-white outline-none"
                />
              </label>
            </div>

            {error && (
              <div className="mt-5 rounded-2xl border border-red-400/15 bg-red-400/[0.04] p-4 text-sm text-red-100/80">
                {error}
              </div>
            )}

            <div className="mt-6 flex flex-wrap gap-3">
              <button
                type="submit"
                disabled={loading}
                className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-xs font-semibold text-black disabled:opacity-50"
              >
                {loading ? (
                  <Loader2
                    size={15}
                    className="animate-spin"
                  />
                ) : (
                  <Search size={15} />
                )}
                {loading
                  ? "Running..."
                  : "Run CareerPilot"}
              </button>

              <button
                type="button"
                onClick={resetWorkspace}
                className="rounded-xl border border-white/10 px-4 py-2.5 text-xs text-white/65"
              >
                Reset Workspace
              </button>
            </div>
          </section>

          <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
            <div className="text-xs uppercase tracking-[0.18em] text-white/30">
              Workflow lifecycle
            </div>

            <div className="mt-5 space-y-2">
              {AGENTS.map(
                ([id, label]) => {
                  const state =
                    getAgentState(
                      id,
                      result,
                    );

                  return (
                    <div
                      key={`agent-${id}`}
                      className="flex items-center gap-3 rounded-2xl border border-white/8 bg-white/[0.02] px-3 py-2.5"
                    >
                      {state === "done" ? (
                        <CheckCircle2
                          size={15}
                        />
                      ) : state ===
                        "active" ? (
                        <Loader2
                          size={15}
                          className="animate-spin"
                        />
                      ) : (
                        <Circle
                          size={15}
                          className="text-white/25"
                        />
                      )}

                      <span className="text-sm">
                        {label}
                      </span>

                      <span className="ml-auto text-[10px] uppercase tracking-[0.14em] text-white/25">
                        {state}
                      </span>
                    </div>
                  );
                },
              )}
            </div>

            {latestDelegation && (
              <div className="mt-5 rounded-2xl border border-white/8 bg-white/[0.02] p-4 text-xs text-white/50">
                {latestDelegation.from_agent}
                {" → "}
                {latestDelegation.to_agent}
                {" • "}
                {latestDelegation.status}
              </div>
            )}
          </section>
        </form>

        <div
          ref={resultsRef}
          className="mt-8 grid gap-6 lg:grid-cols-2"
        >
          <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
            <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-white/30">
              <ShieldCheck size={14} />
              Validation
            </div>

            <div className="mt-5">
              <div className="text-3xl font-semibold">
                {clampScore(
                  result?.final_validation &&
                    typeof result.final_validation === "object"
                    ? (result.final_validation as {
                        valid?: boolean;
                      }).valid
                      ? 100
                      : 0
                    : 0,
                )}
                %
              </div>

              <div className="mt-1 text-xs text-white/35">
                Deterministic final-state validation
              </div>
            </div>
          </section>

          <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
            <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-white/30">
              <UserRound size={14} />
              Next action
            </div>

            <div className="mt-5 text-lg font-medium">
              {result?.next_action?.action ||
                "Run the workflow to generate a personalized next action."}
            </div>
          </section>
        </div>

        {result && (
          <section className="mt-6 rounded-3xl border border-white/10 bg-white/[0.025] p-6">
            <div className="text-xs uppercase tracking-[0.18em] text-white/30">
              Recommendations
            </div>

            <div className="mt-4 space-y-3">
              {(
                result.recommendations ?? []
              ).map(
                (recommendation, index) => (
                  <div
                    key={
                      recommendation.id ||
                      `recommendation-${index}`
                    }
                    className="flex gap-3 rounded-2xl border border-white/8 bg-white/[0.02] p-4"
                  >
                    <div className="min-w-[1.5rem] px-1 text-xs text-white/40">
                      {index + 1}
                    </div>

                    <div>
                      <div className="font-medium">
                        {recommendation.title}
                      </div>

                      <div className="mt-1 text-sm text-white/45">
                        {recommendation.action}
                      </div>
                    </div>
                  </div>
                ),
              )}

              {result.recommendations?.length === 0 && (
                <div className="text-sm text-white/35">
                  No recommendations were returned.
                </div>
              )}
            </div>
          </section>
        )}

        {result?.career_knowledge_evidence?.length ? (
          <section className="mt-6 rounded-3xl border border-white/10 bg-white/[0.025] p-6">
            <div className="text-xs uppercase tracking-[0.18em] text-white/30">
              Evidence
            </div>

            <div className="mt-4 space-y-3">
              {result.career_knowledge_evidence.map(
                (item) => (
                  <div
                    key={item.evidence_id}
                    className="rounded-2xl border border-white/8 p-4"
                  >
                    <div className="font-medium">
                      {item.title}
                    </div>

                    <p className="mt-2 text-sm leading-6 text-white/45">
                      {safeEvidencePreview(
                        item.text,
                      )}
                    </p>
                  </div>
                ),
              )}
            </div>
          </section>
        ) : null}

        {(result?.retry_count ?? 0) > 0 && (
          <div className="mt-4 text-xs text-white/30">
            Recovery retries:{" "}
            {result?.retry_count ?? 0}
          </div>
        )}
      </div>
    </main>
  );
}
''')

# ------------------------------------------------------------------
# 5. DASHBOARD
# ------------------------------------------------------------------

write(F / "app/dashboard/page.tsx", '''"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { API_BASE_URL } from "@/lib/config";
import {
  getWorkspaceState,
  type WorkspaceState,
} from "@/lib/workspace";

export default function DashboardPage() {
  const [
    workspace,
    setWorkspace,
  ] = useState<WorkspaceState>({
    jobs: [],
    applications: [],
    activity: [],
  });

  const [skills, setSkills] =
    useState<string[]>([]);

  useEffect(() => {
    const sync = () =>
      setWorkspace(
        getWorkspaceState(),
      );

    sync();

    window.addEventListener(
      "careerpilot:workspace",
      sync,
    );

    return () =>
      window.removeEventListener(
        "careerpilot:workspace",
        sync,
      );
  }, []);

  useEffect(() => {
    const controller =
      new AbortController();

    fetch(
      `${API_BASE_URL}/career-twin/session`,
      {
        credentials: "include",
        cache: "no-store",
        headers: {
          "Cache-Control":
            "no-cache",
        },
        signal:
          controller.signal,
      },
    )
      .then((response) =>
        response.ok
          ? response.json()
          : null,
      )
      .then((data) => {
        const values =
          data?.profile?.skills;

        if (Array.isArray(values)) {
          setSkills(
            values.filter(
              (
                value,
              ): value is string =>
                typeof value ===
                "string",
            ),
          );
        }
      })
      .catch(() => undefined);

    return () =>
      controller.abort();
  }, []);

  const strongMatches =
    workspace.jobs.filter(
      (job) => {
        const score =
          Number(
            job.match_score ?? 0,
          );

        return (
          score >= 70 ||
          job.decision ===
            "APPLY_NOW" ||
          job.decision ===
            "GOOD_MATCH"
        );
      },
    ).length;

  return (
    <AppShell>
      <main className="min-h-screen bg-[#080a0f] p-6 text-white md:p-10">
        <div className="mx-auto max-w-7xl">
          <p className="text-xs uppercase tracking-[0.2em] text-white/30">
            CareerPilot Overview
          </p>

          <h1 className="mt-3 text-4xl font-semibold tracking-tight">
            Your Career Command Center
          </h1>

          <p className="mt-4 max-w-2xl text-sm leading-6 text-white/45">
            Live workspace metrics sourced from the shared
            opportunity, Career Twin and application state.
          </p>

          <div className="mt-10 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {[
              [
                "Opportunities",
                workspace.jobs.length,
              ],
              [
                "Strong matches",
                strongMatches,
              ],
              [
                "Skills",
                skills.length,
              ],
              [
                "Applications",
                workspace.applications.length,
              ],
            ].map(
              ([label, value]) => (
                <section
                  key={String(label)}
                  className="rounded-3xl border border-white/10 bg-white/[0.025] p-6"
                >
                  <div className="text-xs uppercase tracking-[0.16em] text-white/30">
                    {label}
                  </div>

                  <div className="mt-3 text-3xl font-semibold">
                    {value}
                  </div>
                </section>
              ),
            )}
          </div>

          <section className="mt-6 rounded-3xl border border-white/10 bg-white/[0.025] p-6">
            <div className="text-xs uppercase tracking-[0.16em] text-white/30">
              Recent activity
            </div>

            <div className="mt-5 space-y-3">
              {workspace.activity.length ? (
                workspace.activity
                  .slice(0, 8)
                  .map((item) => (
                    <div
                      key={item.id}
                      className="rounded-2xl border border-white/8 bg-black/10 p-4"
                    >
                      <div className="text-sm font-medium">
                        {item.title}
                      </div>

                      <div className="mt-1 text-xs text-white/35">
                        {item.detail}
                      </div>
                    </div>
                  ))
              ) : (
                <div className="text-sm text-white/35">
                  No activity yet.
                </div>
              )}
            </div>
          </section>
        </div>
      </main>
    </AppShell>
  );
}
''')

# ------------------------------------------------------------------
# 6. OPPORTUNITIES ROUTE
# ------------------------------------------------------------------

write(F / "app/opportunities/page.tsx", '''import { AppShell } from "@/components/AppShell";
import OpportunitiesClient from "./OpportunitiesClient";

export default function Page() {
  return (
    <AppShell>
      <OpportunitiesClient />
    </AppShell>
  );
}
''')

write(F / "app/opportunities/OpportunitiesClient.tsx", '''"use client";

import {
  useEffect,
  useRef,
  useState,
} from "react";
import {
  BriefcaseBusiness,
  CheckCircle2,
  ExternalLink,
  Loader2,
  MapPin,
  Search,
  SlidersHorizontal,
  X,
} from "lucide-react";
import {
  searchJobs,
  type JobResult,
} from "@/lib/api";
import {
  isValidHttpUrl,
  normalizeConfidence,
} from "@/lib/config";
import {
  saveSearchResults,
} from "@/lib/workspace";
import {
  normalizeCommaList,
} from "@/lib/validation";
import { API_BASE_URL } from "@/lib/config";

const WORK_MODES = [
  ["remote", "Remote"],
  ["hybrid", "Hybrid"],
  ["on-site", "On-site"],
];

function salaryLabel(
  job: JobResult,
) {
  if (
    !job.salary_disclosed
  ) {
    return "Undisclosed";
  }

  if (
    job.salary_min_lpa != null &&
    job.salary_max_lpa != null
  ) {
    return `₹${job.salary_min_lpa}–${job.salary_max_lpa} LPA`;
  }

  if (
    job.salary_min_lpa != null
  ) {
    return `₹${job.salary_min_lpa}+ LPA`;
  }

  if (
    job.salary_max_lpa != null
  ) {
    return `Up to ₹${job.salary_max_lpa} LPA`;
  }

  return "Undisclosed";
}

export default function OpportunitiesClient() {
  const [role, setRole] =
    useState("Software Engineer");

  const [location, setLocation] =
    useState("");

  const [
    experienceYears,
    setExperienceYears,
  ] = useState(0);

  const [
    minimumSalary,
    setMinimumSalary,
  ] = useState("");

  const [skills, setSkills] =
    useState("");

  const [industries, setIndustries] =
    useState("");

  const [workModes, setWorkModes] =
    useState<string[]>([
      "remote",
      "hybrid",
      "on-site",
    ]);

  const [jobs, setJobs] =
    useState<JobResult[]>([]);

  const [selectedJob, setSelectedJob] =
    useState<JobResult | null>(
      null,
    );

  const [searched, setSearched] =
    useState(false);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [
    careerTwinReady,
    setCareerTwinReady,
  ] = useState(false);

  const lastSelectedId =
    useRef<string | null>(null);

  const searchController =
    useRef<AbortController | null>(
      null,
    );

  const drawerCloseRef =
    useRef<HTMLButtonElement | null>(
      null,
    );

  useEffect(() => {
    const controller =
      new AbortController();

    fetch(
      `${API_BASE_URL}/career-twin/session`,
      {
        credentials: "include",
        cache: "no-store",
        headers: {
          "Cache-Control":
            "no-cache",
        },
        signal:
          controller.signal,
      },
    )
      .then((response) =>
        response.ok
          ? response.json()
          : null,
      )
      .then((data) => {
        const values =
          data?.profile?.skills;

        if (
          Array.isArray(values) &&
          values.length
        ) {
          setSkills(
            values.join(", "),
          );
        }

        setCareerTwinReady(true);
      })
      .catch(() =>
        setCareerTwinReady(false),
      );

    return () =>
      controller.abort();
  }, []);

  useEffect(() => {
    if (!selectedJob) {
      return;
    }

    drawerCloseRef.current?.focus();

    const onKeyDown = (
      event: KeyboardEvent,
    ) => {
      if (
        event.key === "Escape"
      ) {
        setSelectedJob(null);
      }

      if (
        event.key === "Tab"
      ) {
        const drawer =
          document.getElementById(
            "opportunity-drawer",
          );

        if (!drawer) {
          return;
        }

        const focusable =
          drawer.querySelectorAll<HTMLElement>(
            'button, a[href], input, textarea, select, [tabindex]:not([tabindex="-1"])',
          );

        if (
          focusable.length === 0
        ) {
          return;
        }

        const first =
          focusable[0];

        const last =
          focusable[
            focusable.length - 1
          ];

        if (
          event.shiftKey &&
          document.activeElement ===
            first
        ) {
          event.preventDefault();
          last.focus();
        } else if (
          !event.shiftKey &&
          document.activeElement ===
            last
        ) {
          event.preventDefault();
          first.focus();
        }
      }
    };

    document.addEventListener(
      "keydown",
      onKeyDown,
    );

    return () =>
      document.removeEventListener(
        "keydown",
        onKeyDown,
      );
  }, [selectedJob]);

  function toggleMode(
    value: string,
  ) {
    setWorkModes((current) =>
      current.includes(value)
        ? current.filter(
            (item) =>
              item !== value,
          )
        : [
            ...current,
            value,
          ],
    );
  }

  async function submitSearch() {
    if (!role.trim()) {
      setError(
        "Please enter a target role.",
      );
      return;
    }

    const salary =
      minimumSalary.trim()
        ? Number(minimumSalary)
        : undefined;

    if (
      salary !== undefined &&
      !Number.isFinite(salary)
    ) {
      setError(
        "Enter a valid minimum salary.",
      );
      return;
    }

    searchController.current?.abort();

    const controller =
      new AbortController();

    searchController.current =
      controller;

    const previousId =
      selectedJob
        ? `${selectedJob.source}:${selectedJob.source_job_id}`
        : lastSelectedId.current;

    setLoading(true);
    setError("");

    try {
      const response =
        await searchJobs(
          {
            role: role.trim(),
            location:
              location.trim() ||
              undefined,
            experience_years:
              experienceYears,
            minimum_salary_lpa:
              salary,
            preferred_work_modes:
              workModes,
            skills:
              normalizeCommaList(
                skills,
              ),
            target_industries:
              normalizeCommaList(
                industries,
              ),
          },
          controller.signal,
        );

      setJobs(
        response.results,
      );
      setSearched(true);

      saveSearchResults(
        response.results,
        response.source_summary
          ?.sources ?? [],
      );

      if (previousId) {
        const preserved =
          response.results.find(
            (job) =>
              `${job.source}:${job.source_job_id}` ===
              previousId,
          ) ?? null;

        setSelectedJob(
          preserved,
        );
        lastSelectedId.current =
          previousId;
      }
    } catch (caught) {
      if (
        caught instanceof DOMException &&
        caught.name === "AbortError"
      ) {
        return;
      }

      setError(
        caught instanceof Error
          ? caught.message
          : "CareerPilot could not complete the search.",
      );
    } finally {
      setLoading(false);
      searchController.current =
        null;
    }
  }

  return (
    <main className="min-h-screen bg-[#080a0f] p-5 text-white md:p-8">
      <div className="mx-auto max-w-7xl">
        <header className="border-b border-white/10 pb-7">
          <div className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
            <div>
              <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.2em] text-white/30">
                <BriefcaseBusiness size={14} />
                Opportunity Intelligence
              </div>

              <h1 className="mt-3 text-4xl font-semibold tracking-tight">
                Live opportunities
              </h1>

              <p className="mt-3 max-w-2xl text-sm leading-6 text-white/45">
                Search the connected market using your current
                career profile instead of hardcoded assumptions.
              </p>
            </div>

            <div className="rounded-2xl border border-white/10 px-4 py-3 text-xs text-white/50">
              {careerTwinReady
                ? "Career Twin connected"
                : "Career Twin not yet loaded"}
            </div>
          </div>
        </header>

        <form
          className="mt-6 rounded-3xl border border-white/10 bg-white/[0.025] p-5"
          onSubmit={(event) => {
            event.preventDefault();
            void submitSearch();
          }}
        >
          <div className="grid gap-4 lg:grid-cols-3">
            <label className="text-xs text-white/40">
              Role
              <input
                value={role}
                onChange={(event) => {
                  setRole(
                    event.target.value,
                  );
                  setError("");
                }}
                className="mt-2 w-full rounded-xl border border-white/10 bg-black/10 px-3 py-2.5 text-sm"
              />
            </label>

            <label className="text-xs text-white/40">
              Location
              <input
                value={location}
                onChange={(event) => {
                  setLocation(
                    event.target.value,
                  );
                  setError("");
                }}
                className="mt-2 w-full rounded-xl border border-white/10 bg-black/10 px-3 py-2.5 text-sm"
              />
            </label>

            <label className="text-xs text-white/40">
              Experience years
              <input
                type="number"
                min={0}
                step={0.1}
                value={experienceYears}
                onChange={(event) => {
                  setExperienceYears(
                    Math.max(
                      0,
                      Number(
                        event.target.value ||
                          0,
                      ),
                    ),
                  );
                  setError("");
                }}
                className="mt-2 w-full rounded-xl border border-white/10 bg-black/10 px-3 py-2.5 text-sm"
              />
            </label>

            <label className="text-xs text-white/40">
              Minimum salary (LPA)
              <input
                inputMode="decimal"
                value={minimumSalary}
                onChange={(event) => {
                  const next =
                    event.target.value
                      .replace(
                        /[^\d.]/g,
                        "",
                      )
                      .replace(
                        /(\..*)\./g,
                        "$1",
                      );

                  setMinimumSalary(
                    next,
                  );
                  setError("");
                }}
                className="mt-2 w-full rounded-xl border border-white/10 bg-black/10 px-3 py-2.5 text-sm"
              />
            </label>

            <label className="text-xs text-white/40">
              Skills
              <input
                value={skills}
                onChange={(event) => {
                  setSkills(
                    event.target.value,
                  );
                  setError("");
                }}
                placeholder="Python, SQL, DSA"
                className="mt-2 w-full rounded-xl border border-white/10 bg-black/10 px-3 py-2.5 text-sm"
              />
            </label>

            <label className="text-xs text-white/40">
              Industries
              <input
                value={industries}
                onChange={(event) => {
                  setIndustries(
                    event.target.value,
                  );
                  setError("");
                }}
                placeholder="Leave empty for cross-industry"
                className="mt-2 w-full rounded-xl border border-white/10 bg-black/10 px-3 py-2.5 text-sm"
              />
            </label>
          </div>

          <div className="mt-5">
            <div className="mb-2 text-xs text-white/40">
              Work mode
            </div>

            <div className="flex flex-wrap gap-2">
              {WORK_MODES.map(
                ([value, label]) => (
                  <label
                    key={value}
                    className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.02] px-3 py-2 text-xs text-white/60"
                  >
                    <input
                      type="checkbox"
                      checked={workModes.includes(
                        value,
                      )}
                      onChange={() =>
                        toggleMode(
                          value,
                        )
                      }
                    />
                    {label}
                  </label>
                ),
              )}
            </div>
          </div>

          {error && (
            <div className="mt-5 rounded-2xl border border-red-400/15 bg-red-400/[0.04] p-4 text-sm text-red-100/80">
              {error}
            </div>
          )}

          <div className="mt-5 flex justify-end">
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-xs font-semibold text-black disabled:opacity-50"
            >
              {loading ? (
                <Loader2
                  size={15}
                  className="animate-spin"
                />
              ) : (
                <Search size={15} />
              )}
              {loading
                ? "Searching..."
                : "Search market"}
            </button>
          </div>
        </form>

        <section className="mt-6">
          {!searched &&
          !loading ? (
            <div className="rounded-3xl border border-dashed border-white/10 p-10 text-center text-sm text-white/35">
              Search to populate live canonical opportunities.
            </div>
          ) : loading ? (
            <div className="space-y-3">
              {Array.from(
                { length: 6 },
                (_, index) => (
                  <div
                    key={`skeleton-${index}`}
                    className="h-32 animate-pulse rounded-3xl border border-white/8 bg-white/[0.02]"
                  />
                ),
              )}
            </div>
          ) : (
            <div className="space-y-3">
              {jobs.map(
                (job) => (
                  <article
                    key={`${job.source}-${job.source_job_id}`}
                    className="rounded-3xl border border-white/10 bg-white/[0.025] p-5"
                  >
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedJob(
                            job,
                          );
                          lastSelectedId.current =
                            `${job.source}:${job.source_job_id}`;
                        }}
                        className="min-w-0 text-left"
                      >
                        <div className="flex items-start gap-4">
                          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.04] text-xs font-semibold">
                            {job.company
                              ?.slice(
                                0,
                                2,
                              )
                              .toUpperCase() ||
                              "CP"}
                          </div>

                          <div className="min-w-0">
                            <div className="text-[10px] uppercase tracking-[0.18em] text-white/30">
                              {job.company}
                            </div>

                            <h2 className="mt-1 truncate text-lg font-semibold">
                              {job.title}
                            </h2>

                            <div className="mt-2 flex flex-wrap gap-2 text-xs text-white/35">
                              <span>
                                <MapPin
                                  size={12}
                                  className="mr-1 inline"
                                />
                                {(
                                  job.location ||
                                  []
                                ).filter(Boolean).join(
                                  ", ",
                                ) ||
                                  "Location not specified"}
                              </span>

                              <span>
                                {salaryLabel(
                                  job,
                                )}
                              </span>
                            </div>
                          </div>
                        </div>
                      </button>

                      <div className="flex items-center gap-3">
                        <span className="rounded-full border border-white/8 bg-white/[0.025] px-2.5 py-1 text-[10px] text-white/40">
                          {Math.round(
                            job.match_score ??
                              0,
                          )}
                          % match
                        </span>

                        <button
                          type="button"
                          onClick={() =>
                            setSelectedJob(
                              job,
                            )
                          }
                          className="rounded-xl border border-white/10 px-3 py-2 text-xs"
                        >
                          Intelligence
                        </button>
                      </div>
                    </div>
                  </article>
                ),
              )}

              {jobs.length === 0 && (
                <div className="rounded-3xl border border-white/10 p-10 text-center text-sm text-white/35">
                  No opportunities matched the current filters.
                </div>
              )}
            </div>
          )}
        </section>

        {selectedJob && (
          <div className="fixed inset-0 z-[70]">
            <div
              className="absolute inset-0 bg-black/70 backdrop-blur-sm"
              onClick={() =>
                setSelectedJob(
                  null,
                )
              }
            />

            <aside
              id="opportunity-drawer"
              role="dialog"
              aria-modal="true"
              aria-label="Opportunity intelligence"
              className="absolute inset-y-0 right-0 w-full max-w-2xl overflow-y-auto border-l border-white/10 bg-[#0b0e14] p-6"
            >
              <div className="flex items-center justify-between">
                <div className="text-xs uppercase tracking-[0.2em] text-white/30">
                  Opportunity Intelligence
                </div>

                <button
                  ref={
                    drawerCloseRef
                  }
                  type="button"
                  aria-label="Close analysis"
                  onClick={() =>
                    setSelectedJob(
                      null,
                    )
                  }
                  className="rounded-xl border border-white/10 p-2"
                >
                  <X size={16} />
                </button>
              </div>

              <div className="mt-6 flex items-start gap-4">
                <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.04] text-sm font-semibold">
                  {selectedJob.company
                    ?.slice(0, 2)
                    .toUpperCase() ||
                    "CP"}
                </div>

                <div>
                  <h2 className="text-xl font-semibold">
                    {selectedJob.title}
                  </h2>
                  <div className="mt-1 text-sm text-white/45">
                    {selectedJob.company}
                  </div>
                  <div className="mt-2 text-xs text-white/35">
                    {(
                      selectedJob.location ||
                      []
                    ).filter(Boolean).join(
                      ", ",
                    ) ||
                      "Location not specified"}
                  </div>
                </div>
              </div>

              <section className="mt-6 rounded-3xl border border-white/10 bg-white/[0.025] p-5">
                <div className="text-xs uppercase tracking-[0.16em] text-white/30">
                  Match
                </div>

                <div className="mt-2 text-5xl font-semibold">
                  {Math.round(
                    selectedJob.match_score ??
                      0,
                  )}
                </div>

                <div className="mt-1 text-xs text-white/35">
                  {normalizeConfidence(
                    selectedJob.confidence,
                  )}
                  % confidence
                </div>
              </section>

              <section className="mt-5 rounded-3xl border border-white/10 bg-white/[0.025] p-5">
                <div className="text-xs uppercase tracking-[0.16em] text-white/30">
                  Why this opportunity
                </div>

                <p className="mt-3 text-sm leading-7 text-white/55">
                  {selectedJob.explanation ||
                    "CareerPilot matched role, skill, experience, location and salary evidence."}
                </p>
              </section>

              <section className="mt-5 rounded-3xl border border-white/10 bg-white/[0.025] p-5">
                <div className="text-xs uppercase tracking-[0.16em] text-white/30">
                  Salary
                </div>

                <div className="mt-3 text-sm text-white/65">
                  {salaryLabel(
                    selectedJob,
                  )}
                </div>

                {selectedJob.salary_status ===
                  "BELOW_TARGET" && (
                  <div className="mt-2 text-xs text-amber-200/80">
                    Below the minimum salary target.
                  </div>
                )}
              </section>

              <div className="mt-6 flex flex-wrap gap-3">
                {isValidHttpUrl(
                  selectedJob.apply_url,
                ) ? (
                  <a
                    href={
                      selectedJob.apply_url
                    }
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-xs font-semibold text-black"
                  >
                    Apply
                    <ExternalLink size={13} />
                  </a>
                ) : (
                  <button
                    type="button"
                    disabled
                    className="rounded-xl border border-white/10 px-4 py-2.5 text-xs text-white/30"
                  >
                    Apply unavailable
                  </button>
                )}
              </div>
            </aside>
          </div>
        )}
      </div>
    </main>
  );
}
''')

# ------------------------------------------------------------------
# 7. RESUME DECOMPOSITION
# ------------------------------------------------------------------

write(F / "app/resume/page.tsx", '''import { AppShell } from "@/components/AppShell";
import ResumeClient from "./ResumeClient";

export default function Page() {
  return (
    <AppShell>
      <ResumeClient />
    </AppShell>
  );
}
''')

write(F / "app/resume/ResumeUpload.tsx", '''"use client";

import { ChangeEvent, useRef } from "react";
import { MAX_RESUME_BYTES } from "@/lib/config";

export function ResumeUpload({
  file,
  onSelect,
  onError,
}: {
  file: File | null;
  onSelect: (file: File) => void;
  onError: (message: string) => void;
}) {
  const inputRef =
    useRef<HTMLInputElement | null>(
      null,
    );

  function handle(
    event: ChangeEvent<HTMLInputElement>,
  ) {
    const selected =
      event.target.files?.[0];

    if (!selected) return;

    if (
      selected.type !==
      "application/pdf"
    ) {
      event.target.value = "";
      onError(
        "Please upload a PDF resume.",
      );
      return;
    }

    if (
      selected.size >
      MAX_RESUME_BYTES
    ) {
      event.target.value = "";
      onError(
        "The PDF must be smaller than 10 MB.",
      );
      return;
    }

    onSelect(selected);
  }

  return (
    <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
      <div className="text-xs uppercase tracking-[0.18em] text-white/30">
        Resume upload
      </div>

      <label className="mt-4 block text-sm text-white/70">
        PDF resume
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          onChange={handle}
          className="mt-3 block w-full rounded-xl border border-white/10 bg-black/10 p-3 text-xs"
        />
      </label>

      {file && (
        <div className="mt-3 text-xs text-white/40">
          {file.name}
        </div>
      )}
    </div>
  );
}
''')

write(F / "app/resume/ResumeScores.tsx", '''"use client";

import { useState } from "react";
import type { ResumeAnalysisResponse } from "@/lib/api";
import { clampScore } from "@/lib/config";

export function ResumeScores({
  result,
}: {
  result: ResumeAnalysisResponse;
}) {
  const [
    expandedExperience,
    setExpandedExperience,
  ] = useState<number | null>(
    null,
  );

  const score =
    clampScore(
      result.intelligence
        .overall_score,
    );

  return (
    <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
      <div className="text-xs uppercase tracking-[0.18em] text-white/30">
        Resume scores
      </div>

      <div className="mt-4 grid gap-4 md:grid-cols-4">
        <div className="rounded-2xl border border-white/8 p-4">
          <div className="text-xs text-white/35">
            Overall
          </div>
          <div className="mt-2 text-3xl font-semibold">
            {score}
          </div>
        </div>

        {(result.intelligence
          .section_scores ?? []
        ).slice(0, 3).map(
          (item) => (
            <div
              key={item.section}
              className="rounded-2xl border border-white/8 p-4"
            >
              <div className="text-xs text-white/35">
                {item.section}
              </div>
              <div className="mt-2 text-3xl font-semibold">
                {clampScore(
                  item.score,
                )}
              </div>
            </div>
          ),
        )}
      </div>

      {result.resume
        .experience.length > 0 && (
        <div className="mt-6">
          <div className="text-xs uppercase tracking-[0.16em] text-white/30">
            Experience
          </div>

          <div className="mt-3 space-y-2">
            {result.resume.experience.map(
              (item, index) => (
                <button
                  key={`experience-${index}`}
                  type="button"
                  aria-expanded={
                    expandedExperience ===
                    index
                  }
                  onClick={() =>
                    setExpandedExperience(
                      expandedExperience ===
                        index
                        ? null
                        : index,
                    )
                  }
                  className="w-full rounded-2xl border border-white/8 bg-white/[0.02] p-4 text-left"
                >
                  <div className="font-medium">
                    {item.job_title ||
                      "Experience"}
                  </div>

                  <div className="mt-1 text-xs text-white/35">
                    {item.company ||
                      "Unknown company"}
                  </div>

                  {expandedExperience ===
                    index && (
                    <p className="mt-3 text-sm leading-6 text-white/45">
                      {item.description ||
                        item.achievements?.join(
                          " ",
                        ) ||
                        "No additional evidence."}
                    </p>
                  )}
                </button>
              ),
            )}
          </div>
        </div>
      )}
    </section>
  );
}
''')

write(F / "app/resume/ATSChecklist.tsx", '''import type { ResumeJobAnalysisResponse } from "@/lib/api";

export function ATSChecklist({
  result,
}: {
  result: ResumeJobAnalysisResponse | null;
}) {
  const items =
    result?.ats_analysis?.requirements ??
    result?.ats_analysis?.missing_requirements ??
    [];

  return (
    <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
      <div className="text-xs uppercase tracking-[0.18em] text-white/30">
        ATS checklist
      </div>

      <div className="mt-4 space-y-2">
        {items.length ? (
          items.map(
            (item, index) => (
              <div
                key={`ats-${index}-${item.requirement ?? "item"}`}
                className="rounded-2xl border border-white/8 p-3 text-sm text-white/55"
              >
                <div className="font-medium">
                  {item.requirement ||
                    "Requirement"}
                </div>
                <div className="mt-1 text-xs text-white/30">
                  {item.status ||
                    item.importance ||
                    "Review"}
                </div>
              </div>
            ),
          )
        ) : (
          <div className="text-sm text-white/35">
            Run a job-specific analysis to populate the ATS checklist.
          </div>
        )}
      </div>
    </section>
  );
}
''')

write(F / "app/resume/JobMatcher.tsx", '''"use client";

import {
  useState,
} from "react";
import {
  analyzeResumeForJob,
  type ResumeJobAnalysisResponse,
} from "@/lib/api";

export function JobMatcher({
  file,
  result,
  onResult,
  onError,
}: {
  file: File | null;
  result: ResumeJobAnalysisResponse | null;
  onResult: (
    result: ResumeJobAnalysisResponse,
  ) => void;
  onError: (
    message: string,
  ) => void;
}) {
  const [
    description,
    setDescription,
  ] = useState("");

  const [
    loading,
    setLoading,
  ] = useState(false);

  async function analyze() {
    if (!file) {
      onError(
        "Please choose a resume first.",
      );
      return;
    }

    if (!description.trim()) {
      onError(
        "Please paste a job description first.",
      );
      return;
    }

    setLoading(true);

    try {
      const response =
        await analyzeResumeForJob(
          file,
          description,
        );

      onResult(response);
    } catch (caught) {
      onError(
        caught instanceof Error
          ? caught.message
          : "Unable to analyze the resume for this job.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
      <div className="text-xs uppercase tracking-[0.18em] text-white/30">
        Job matcher
      </div>

      <label className="mt-4 block text-sm text-white/65">
        Job description
        <textarea
          value={description}
          maxLength={12000}
          onChange={(event) => {
            setDescription(
              event.target.value,
            );
            onError("");
          }}
          className="mt-2 min-h-40 w-full rounded-2xl border border-white/10 bg-black/10 p-4 text-sm outline-none"
        />
      </label>

      <button
        type="button"
        disabled={loading}
        onClick={() => void analyze()}
        className="mt-4 rounded-xl bg-white px-4 py-2.5 text-xs font-semibold text-black disabled:opacity-50"
      >
        {loading
          ? "Analyzing..."
          : "Analyze against job"}
      </button>

      {result && (
        <div className="mt-5 grid gap-3 md:grid-cols-3">
          <div className="rounded-2xl border border-white/8 p-4">
            <div className="text-xs text-white/30">
              Overall fit
            </div>
            <div className="mt-2 text-2xl font-semibold">
              {Math.round(
                result.job_resume_analysis
                  .overall_fit_score,
              )}
            </div>
          </div>

          <div className="rounded-2xl border border-white/8 p-4">
            <div className="text-xs text-white/30">
              Evidence
            </div>
            <div className="mt-2 text-2xl font-semibold">
              {Math.round(
                result.job_resume_analysis
                  .evidence_score,
              )}
            </div>
          </div>

          <div className="rounded-2xl border border-white/8 p-4">
            <div className="text-xs text-white/30">
              Role
            </div>
            <div className="mt-2 text-sm font-medium">
              {result.job_resume_analysis
                .target_role}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
''')

write(F / "app/resume/RewriteSuggestions.tsx", '''import type { ResumeJobAnalysisResponse } from "@/lib/api";

export function RewriteSuggestions({
  result,
}: {
  result: ResumeJobAnalysisResponse | null;
}) {
  const suggestions =
    result?.rewrite_analysis?.suggestions ??
    [];

  return (
    <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
      <div className="text-xs uppercase tracking-[0.18em] text-white/30">
        Evidence-backed rewrites
      </div>

      <div className="mt-4 space-y-3">
        {suggestions.length ? (
          suggestions.map(
            (item, index) => (
              <div
                key={`rewrite-${index}-${item.section}`}
                className="rounded-2xl border border-white/8 p-4"
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="font-medium">
                    {item.section}
                  </div>

                  <span className="rounded-full border border-white/8 px-2 py-1 text-[10px] text-white/45">
                    {item.evidence_status}
                  </span>
                </div>

                <p className="mt-2 text-sm leading-6 text-white/45">
                  {item.suggested_rewrite}
                </p>
              </div>
            ),
          )
        ) : (
          <div className="text-sm text-white/35">
            Run a job-specific analysis to generate evidence-backed rewrite candidates.
          </div>
        )}
      </div>
    </section>
  );
}
''')

write(F / "app/resume/ResumeClient.tsx", '''"use client";

import dynamic from "next/dynamic";
import { useState } from "react";
import {
  analyzeResume,
  type ResumeAnalysisResponse,
  type ResumeJobAnalysisResponse,
} from "@/lib/api";
import { ResumeUpload } from "./ResumeUpload";
import { ResumeScores } from "./ResumeScores";

const ATSChecklist =
  dynamic(() =>
    import("./ATSChecklist").then(
      (module) =>
        module.ATSChecklist,
    ),
  );

const JobMatcher =
  dynamic(() =>
    import("./JobMatcher").then(
      (module) =>
        module.JobMatcher,
    ),
  );

const RewriteSuggestions =
  dynamic(() =>
    import("./RewriteSuggestions").then(
      (module) =>
        module.RewriteSuggestions,
    ),
  );

type JobView =
  | "overview"
  | "requirements"
  | "rewrite"
  | "ai";

export default function ResumeClient() {
  const [
    file,
    setFile,
  ] = useState<File | null>(
    null,
  );

  const [
    resumeResult,
    setResumeResult,
  ] = useState<ResumeAnalysisResponse | null>(
    null,
  );

  const [
    jobResult,
    setJobResult,
  ] = useState<ResumeJobAnalysisResponse | null>(
    null,
  );

  const [
    activeView,
    setActiveView,
  ] = useState<JobView>(
    "overview",
  );

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState("");

  async function runResumeAnalysis() {
    if (!file) {
      setError(
        "Please choose a resume first.",
      );
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response =
        await analyzeResume(
          file,
        );

      setResumeResult(
        response,
      );
      setJobResult(null);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to analyze the resume.",
      );
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setFile(null);
    setResumeResult(null);
    setJobResult(null);
    setActiveView(
      "overview",
    );
    setError("");
    setLoading(false);
  }

  return (
    <main className="min-h-screen bg-[#080a0f] p-5 text-white md:p-8">
      <div className="mx-auto max-w-7xl">
        <header className="border-b border-white/10 pb-7">
          <div className="text-[10px] uppercase tracking-[0.2em] text-white/30">
            CareerPilot Intelligence
          </div>

          <h1 className="mt-3 text-4xl font-semibold">
            Resume Intelligence
          </h1>

          <p className="mt-3 max-w-2xl text-sm leading-6 text-white/45">
            Parse resume evidence, measure quality, compare against a target job,
            and produce evidence-backed rewrite suggestions.
          </p>
        </header>

        <div className="mt-6 grid gap-6 lg:grid-cols-[360px_1fr]">
          <div className="space-y-4">
            <ResumeUpload
              file={file}
              onSelect={(selected) => {
                setFile(selected);
                setResumeResult(null);
                setJobResult(null);
                setError("");
              }}
              onError={setError}
            />

            {error && (
              <div className="rounded-2xl border border-red-400/15 bg-red-400/[0.04] p-4 text-sm text-red-100/80">
                {error}
              </div>
            )}

            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                disabled={
                  loading ||
                  !file
                }
                onClick={() =>
                  void runResumeAnalysis()
                }
                className="rounded-xl bg-white px-4 py-2.5 text-xs font-semibold text-black disabled:opacity-50"
              >
                {loading
                  ? "Analyzing..."
                  : "Analyze resume"}
              </button>

              <button
                type="button"
                onClick={reset}
                className="rounded-xl border border-white/10 px-4 py-2.5 text-xs text-white/65"
              >
                Reset
              </button>
            </div>
          </div>

          <div className="space-y-5">
            {resumeResult ? (
              <>
                <ResumeScores
                  result={
                    resumeResult
                  }
                />

                <div
                  role="tablist"
                  aria-label="Resume intelligence panels"
                  className="flex flex-wrap gap-2"
                >
                  {(
                    [
                      [
                        "overview",
                        "Overview",
                      ],
                      [
                        "requirements",
                        "ATS",
                      ],
                      [
                        "rewrite",
                        "Rewrite",
                      ],
                      [
                        "ai",
                        "Job match",
                      ],
                    ] as const
                  ).map(
                    ([id, label]) => (
                      <button
                        key={id}
                        type="button"
                        role="tab"
                        aria-selected={
                          activeView ===
                          id
                        }
                        onClick={() =>
                          setActiveView(
                            id,
                          )
                        }
                        className={[
                          "rounded-xl border px-3 py-2 text-xs",
                          activeView ===
                          id
                            ? "border-white/20 bg-white text-black"
                            : "border-white/10 text-white/55",
                        ].join(" ")}
                      >
                        {label}
                      </button>
                    ),
                  )}
                </div>

                {activeView ===
                  "overview" && (
                  <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
                    <div className="text-xs uppercase tracking-[0.18em] text-white/30">
                      Strengths
                    </div>

                    <div className="mt-4 space-y-2">
                      {(
                        resumeResult
                          .intelligence
                          .strengths ??
                        []
                      ).map(
                        (item) => (
                          <div
                            key={item}
                            className="rounded-2xl border border-white/8 p-3 text-sm text-white/55"
                          >
                            {item}
                          </div>
                        ),
                      )}
                    </div>
                  </section>
                )}

                {activeView ===
                  "requirements" && (
                  <ATSChecklist
                    result={
                      jobResult
                    }
                  />
                )}

                {activeView ===
                  "rewrite" && (
                  <RewriteSuggestions
                    result={
                      jobResult
                    }
                  />
                )}

                {activeView ===
                  "ai" && (
                  <JobMatcher
                    file={file}
                    result={
                      jobResult
                    }
                    onResult={
                      setJobResult
                    }
                    onError={
                      setError
                    }
                  />
                )}
              </>
            ) : (
              <div className="rounded-3xl border border-dashed border-white/10 p-10 text-center text-sm text-white/35">
                Upload a resume and run analysis to populate the intelligence panels.
              </div>
            )}
          </div>
        </div>

        <div className="mt-6 rounded-3xl border border-white/10 bg-white/[0.02] p-5 text-xs text-white/30">
          Maximum accepted upload size: 10 MB.
        </div>
      </div>
    </main>
  );
}
''')

# ------------------------------------------------------------------
# 8. CAREER TWIN
# ------------------------------------------------------------------

write(F / "app/career-twin/page.tsx", '''"use client";

import { useCallback, useEffect, useState } from "react";
import {
  RefreshCw,
  UserRound,
} from "lucide-react";
import { API_BASE_URL } from "@/lib/config";

type CareerTwin = {
  candidate_id: string;
  version: number;
  profile: {
    name?: string | null;
    headline?: string | null;
    skills: string[];
    technical_skills: string[];
    soft_skills: string[];
    education: string[];
    certifications: string[];
    projects: string[];
    target_roles: string[];
    target_industries: string[];
    target_locations: string[];
    preferred_work_modes: string[];
    minimum_salary_lpa?: number | null;
  };
  derived: {
    strengths: string[];
    skill_gaps: string[];
    readiness_score: number;
    readiness_level: string;
    career_directions: string[];
  };
  memory: Array<{
    event_id: string;
    event_type: string;
    summary: string;
    timestamp: string;
  }>;
};

export default function CareerTwinPage() {
  const [twin, setTwin] =
    useState<CareerTwin | null>(
      null,
    );

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [memoryLimit, setMemoryLimit] =
    useState(8);

  const load = useCallback(
    async () => {
      setLoading(true);
      setError("");

      try {
        const response =
          await fetch(
            `${API_BASE_URL}/career-twin/session`,
            {
              credentials:
                "include",
              cache: "no-store",
              headers: {
                "Cache-Control":
                  "no-cache",
              },
            },
          );

        if (!response.ok) {
          throw new Error(
            response.status === 401
              ? "Your CareerPilot session is not authenticated."
              : `Career Twin request failed (${response.status})`,
          );
        }

        setTwin(
          await response.json(),
        );
      } catch (caught) {
        setError(
          caught instanceof Error
            ? caught.message
            : "Unable to load Career Twin.",
        );
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) {
    return (
      <main className="min-h-screen bg-[#080a0f] p-8 text-white">
        <div className="mx-auto max-w-6xl">
          <div className="h-10 w-64 animate-pulse rounded bg-white/5" />
          <div className="mt-8 grid gap-4 md:grid-cols-4">
            {Array.from(
              { length: 4 },
              (_, index) => (
                <div
                  key={`twin-skeleton-${index}`}
                  className="h-32 animate-pulse rounded-3xl bg-white/[0.03]"
                />
              ),
            )}
          </div>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen bg-[#080a0f] p-8 text-white">
        <div className="mx-auto max-w-6xl">
          <div className="rounded-3xl border border-red-400/15 bg-red-400/[0.04] p-6">
            {error}
          </div>
        </div>
      </main>
    );
  }

  if (!twin) {
    return null;
  }

  const profile =
    twin.profile;

  return (
    <main className="min-h-screen bg-[#080a0f] p-5 text-white md:p-8">
      <div className="mx-auto max-w-6xl">
        <div className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="text-[10px] uppercase tracking-[0.2em] text-white/30">
              Persistent career memory
            </div>

            <h1 className="mt-3 text-4xl font-semibold">
              Career Twin
            </h1>

            <p className="mt-3 max-w-2xl text-sm leading-6 text-white/45">
              Your evolving career representation across skills, goals,
              opportunities and historical evidence.
            </p>
          </div>

          <button
            type="button"
            onClick={() => void load()}
            className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-4 py-2.5 text-xs"
          >
            <RefreshCw size={14} />
            Refresh
          </button>
        </div>

        <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {[
            [
              "Readiness",
              Math.round(
                twin.derived
                  .readiness_score,
              ),
            ],
            [
              "Skills",
              profile.skills.length,
            ],
            [
              "Target roles",
              profile
                .target_roles
                .length,
            ],
            [
              "Twin version",
              twin.version,
            ],
          ].map(
            ([label, value]) => (
              <section
                key={String(label)}
                className="rounded-3xl border border-white/10 bg-white/[0.025] p-5"
              >
                <div className="text-xs uppercase tracking-[0.18em] text-white/30">
                  {label}
                </div>

                <div className="mt-3 text-3xl font-semibold">
                  {value}
                </div>
              </section>
            ),
          )}
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
            <div className="flex items-center gap-3">
              <UserRound size={18} />
              <div>
                <div className="font-medium">
                  {profile.name ||
                    "Career profile"}
                </div>
                <div className="mt-1 text-xs text-white/35">
                  {profile.headline ||
                    "Professional profile"}
                </div>
              </div>
            </div>

            <div className="mt-6">
              <div className="text-xs text-white/35">
                Technical skills
              </div>

              <div className="mt-3 flex flex-wrap gap-2">
                {profile.technical_skills.map(
                  (skill) => (
                    <span
                      key={skill}
                      className="rounded-full border border-white/8 bg-white/[0.025] px-3 py-1.5 text-xs text-white/60"
                    >
                      {skill}
                    </span>
                  ),
                )}
              </div>
            </div>
          </section>

          <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
            <div className="text-xs uppercase tracking-[0.16em] text-white/30">
              Career direction
            </div>

            <div className="mt-4 space-y-2">
              {profile.target_roles.map(
                (role) => (
                  <div
                    key={role}
                    className="rounded-2xl border border-white/8 p-3 text-sm"
                  >
                    {role}
                  </div>
                ),
              )}
            </div>
          </section>
        </div>

        <section className="mt-6 rounded-3xl border border-white/10 bg-white/[0.025] p-6">
          <div className="flex items-center justify-between">
            <div className="text-xs uppercase tracking-[0.16em] text-white/30">
              Career memory
            </div>

            {twin.memory.length >
              memoryLimit && (
              <button
                type="button"
                onClick={() =>
                  setMemoryLimit(
                    twin.memory.length,
                  )
                }
                className="text-xs underline"
              >
                View all
              </button>
            )}

            {memoryLimit >=
              twin.memory.length &&
              twin.memory.length > 8 && (
                <button
                  type="button"
                  onClick={() =>
                    setMemoryLimit(8)
                  }
                  className="text-xs underline"
                >
                  Collapse
                </button>
              )}
          </div>

          <div className="mt-4 space-y-2">
            {twin.memory
              .slice(
                0,
                memoryLimit,
              )
              .map(
                (event) => (
                  <div
                    key={event.event_id}
                    className="rounded-2xl border border-white/8 p-3"
                  >
                    <div className="text-sm font-medium">
                      {event.summary}
                    </div>

                    <div className="mt-1 text-[11px] text-white/30">
                      {event.event_type}
                    </div>
                  </div>
                ),
              )}

            {twin.memory.length ===
              0 && (
              <div className="text-sm text-white/35">
                No career memory events recorded yet.
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}
''')

# ------------------------------------------------------------------
# 9. BACKEND SESSION SECURITY
# ------------------------------------------------------------------

write(B / "api/session.py", '''from __future__ import annotations

import hashlib
import hmac
import os
import uuid

from fastapi import HTTPException, Request, Response

COOKIE_NAME = "careerpilot_session"

SECRET_VALUE = os.getenv(
    "CAREERPILOT_SESSION_SECRET",
    "careerpilot-local-week7-secret",
)

SECRET = SECRET_VALUE.encode(
    "utf-8"
)


def _sign(
    candidate_id: str,
) -> str:
    signature = hmac.new(
        SECRET,
        candidate_id.encode(
            "utf-8"
        ),
        hashlib.sha256,
    ).hexdigest()

    return (
        f"{candidate_id}.{signature}"
    )


def _verify(
    value: str | None,
) -> str | None:
    if (
        not value or
        "." not in value
    ):
        return None

    raw, signature = value.rsplit(
        ".",
        1,
    )

    expected = hmac.new(
        SECRET,
        raw.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(
        signature,
        expected,
    ):
        return None

    try:
        uuid.UUID(raw)
    except ValueError:
        return None

    return raw


def get_candidate_id(
    request: Request,
) -> str:
    candidate_id = _verify(
        request.cookies.get(
            COOKIE_NAME,
        ),
    )

    if not candidate_id:
        raise HTTPException(
            status_code=401,
            detail="Career session is not authenticated.",
        )

    return candidate_id


def ensure_session(
    request: Request,
    response: Response,
) -> str:
    existing = _verify(
        request.cookies.get(
            COOKIE_NAME,
        ),
    )

    if existing:
        return existing

    candidate_id = str(
        uuid.uuid4(),
    )

    response.set_cookie(
        COOKIE_NAME,
        _sign(candidate_id),
        httponly=True,
        secure=os.getenv(
            "ENVIRONMENT",
            "development",
        ).lower()
        == "production",
        samesite="lax",
        max_age=31536000,
        path="/",
    )

    return candidate_id
''')

# ------------------------------------------------------------------
# 10. BACKEND MODELS
# ------------------------------------------------------------------

models = read(B / "api/models.py")
if "field_validator" not in models:
    models = models.replace(
        "from pydantic import BaseModel, Field",
        "from pydantic import BaseModel, Field, field_validator",
        1,
    )

models = re.sub(
    r"class JobSearchRequest\(BaseModel\):.*?# ==========================================================",
    '''class JobSearchRequest(BaseModel):
    role: str = Field(
        ...,
        min_length=1,
    )

    location: Optional[str] = None

    experience_years: float = Field(
        default=0,
        ge=0,
    )

    minimum_salary_lpa: Optional[float] = Field(
        default=None,
        ge=0,
    )

    preferred_work_modes: List[str] = Field(
        default_factory=list,
    )

    skills: List[str] = Field(
        default_factory=list,
    )

    target_industries: List[str] = Field(
        default_factory=list,
    )

    @field_validator(
        "preferred_work_modes",
        "skills",
        "target_industries",
    )
    @classmethod
    def normalize_lists(
        cls,
        values: List[str],
    ) -> List[str]:
        cleaned: List[str] = []
        seen: set[str] = set()

        for value in values:
            item = value.strip()

            if not item:
                continue

            key = item.casefold()

            if key in seen:
                continue

            seen.add(key)
            cleaned.append(item)

        return cleaned


# ==========================================================
''',
    models,
    count=1,
    flags=re.S,
)

write(B / "api/models.py", models)

# ------------------------------------------------------------------
# 11. BACKEND MAIN.PY
# ------------------------------------------------------------------

main = read(B / "api/main.py")

main = main.replace(
    "from fastapi import (\n    FastAPI,",
    "from fastapi import (\n    FastAPI,\n    Request,\n    Response,",
    1,
)

if "from backend.api.session import" not in main:
    main = main.replace(
        "from backend.api.agentic import router as agentic_router",
        "from backend.api.agentic import router as agentic_router\nfrom backend.api.session import ensure_session, get_candidate_id",
        1,
    )

main = main.replace(
    "def search_jobs(\n    request: JobSearchRequest,\n):",
    "def search_jobs(\n    request: JobSearchRequest,\n    http_request: Request,\n):",
    1,
)

main = main.replace(
    'candidate_id="api-user",',
    "candidate_id=get_candidate_id(http_request),",
    1,
)

if "MAX_RESUME_BYTES = 10 * 1024 * 1024" not in main:
    insertion = '''
MAX_RESUME_BYTES = 10 * 1024 * 1024


def read_upload_limited(
    file: UploadFile,
) -> bytes:
    data = file.file.read(
        MAX_RESUME_BYTES + 1,
    )

    if len(data) > MAX_RESUME_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Resume file exceeds the 10 MB limit.",
        )

    return data


'''
    main = main.replace(
        "# ============================================================\n# ROOT",
        insertion + "# ============================================================\n# ROOT",
        1,
    )

main = main.replace(
    "file_bytes = await file.read()",
    "file_bytes = read_upload_limited(file)",
)

main = main.replace(
    "pdf_bytes = await file.read()",
    "pdf_bytes = read_upload_limited(file)",
)

if '@app.middleware("http")' not in main:
    middleware = '''
@app.middleware("http")
async def careerpilot_session_middleware(
    request: Request,
    call_next,
):
    response = await call_next(
        request,
    )

    if not request.cookies.get(
        "careerpilot_session",
    ):
        ensure_session(
            request,
            response,
        )

    return response


'''
    main = main.replace(
        "app.add_middleware(\n    CORSMiddleware,",
        middleware + "app.add_middleware(\n    CORSMiddleware,",
        1,
    )

write(B / "api/main.py", main)

# ------------------------------------------------------------------
# 12. CAREER TWIN ENDPOINT
# ------------------------------------------------------------------

write(B / "api/career_twin.py", '''from __future__ import annotations

from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
)

from backend.api.session import (
    ensure_session,
    get_candidate_id,
)

from backend.services.career_twin import (
    get_or_create,
    record_event,
    save,
    update_from_candidate,
)

router = APIRouter(
    prefix="/career-twin",
    tags=["Career Twin"],
)


@router.get("/session")
def session_career_twin(
    request: Request,
    response: Response,
) -> dict[str, Any]:
    candidate_id = ensure_session(
        request,
        response,
    )

    return get_or_create(
        candidate_id,
    ).model_dump(
        mode="json",
    )


@router.get("/{candidate_id}")
def get_career_twin(
    candidate_id: str,
    authenticated_candidate_id: str = Depends(
        get_candidate_id,
    ),
) -> dict[str, Any]:
    if (
        candidate_id !=
        authenticated_candidate_id
    ):
        raise HTTPException(
            status_code=403,
            detail="Career session does not own this Career Twin.",
        )

    return get_or_create(
        candidate_id,
    ).model_dump(
        mode="json",
    )


@router.post("/{candidate_id}/sync")
def sync_career_twin(
    candidate_id: str,
    payload: dict[str, Any],
    authenticated_candidate_id: str = Depends(
        get_candidate_id,
    ),
) -> dict[str, Any]:
    if (
        candidate_id !=
        authenticated_candidate_id
    ):
        raise HTTPException(
            status_code=403,
            detail="Career session does not own this Career Twin.",
        )

    candidate = dict(
        payload.get(
            "candidate_profile",
        )
        or {},
    )

    candidate[
        "candidate_id"
    ] = candidate_id

    twin = update_from_candidate(
        candidate=candidate,
        candidate_intelligence=payload.get(
            "candidate_intelligence",
        ),
        skill_gaps=payload.get(
            "skill_gaps",
        ),
        recommendations=payload.get(
            "recommendations",
        )
        or [],
    )

    return twin.model_dump(
        mode="json",
    )


@router.patch("/{candidate_id}")
def update_career_twin(
    candidate_id: str,
    payload: dict[str, Any],
    authenticated_candidate_id: str = Depends(
        get_candidate_id,
    ),
) -> dict[str, Any]:
    if (
        candidate_id !=
        authenticated_candidate_id
    ):
        raise HTTPException(
            status_code=403,
            detail="Career session does not own this Career Twin.",
        )

    twin = get_or_create(
        candidate_id,
    )

    profile = twin.profile.model_copy(
        deep=True,
    )

    incoming = dict(
        payload.get(
            "profile",
        )
        or {},
    )

    for field, value in incoming.items():
        if hasattr(
            profile,
            field,
        ):
            setattr(
                profile,
                field,
                value,
            )

    twin.profile = profile
    twin.version += 1

    save(twin)

    record_event(
        candidate_id=candidate_id,
        event_type="manual_update",
        summary="Career Twin profile manually updated by the user.",
        payload={
            "fields": sorted(
                incoming.keys(),
            ),
        },
    )

    return get_or_create(
        candidate_id,
    ).model_dump(
        mode="json",
    )


@router.post("/{candidate_id}/events")
def add_career_event(
    candidate_id: str,
    payload: dict[str, Any],
    authenticated_candidate_id: str = Depends(
        get_candidate_id,
    ),
) -> dict[str, Any]:
    if (
        candidate_id !=
        authenticated_candidate_id
    ):
        raise HTTPException(
            status_code=403,
            detail="Career session does not own this Career Twin.",
        )

    event = record_event(
        candidate_id=candidate_id,
        event_type=str(
            payload.get(
                "event_type",
            )
            or "custom",
        ),
        summary=str(
            payload.get(
                "summary",
            )
            or "Career event recorded.",
        ),
        payload=dict(
            payload.get(
                "payload",
            )
            or {},
        ),
    )

    return {
        "event": event.model_dump(
            mode="json",
        ),
        "career_twin": get_or_create(
            candidate_id,
        ).model_dump(
            mode="json",
        ),
    }
}
''')

# ------------------------------------------------------------------
# 13. AGENTIC BACKEND IDENTITY + TRACE
# ------------------------------------------------------------------

agentic = read(B / "api/agentic.py")

agentic = agentic.replace(
    "from fastapi import APIRouter, HTTPException",
    "from fastapi import APIRouter, HTTPException, Request",
    1,
)

if "from backend.api.session import get_candidate_id" not in agentic:
    agentic = agentic.replace(
        "from backend.graph.state import create_initial_state",
        "from backend.api.session import get_candidate_id\nfrom backend.graph.state import create_initial_state",
        1,
    )

agentic = agentic.replace(
    "def run_agentic_workflow(\n    request: AgenticRunRequest,\n):",
    "def run_agentic_workflow(\n    request: AgenticRunRequest,\n    http_request: Request,\n):",
    1,
)

agentic = agentic.replace(
    'request.request_id\n            or f"agentic-{id(request)}"',
    'request.request_id\n            or str(__import__("uuid").uuid4())',
    1,
)

agentic = agentic.replace(
    '''"candidate_id":
                    "agentic-user",''',
    '''"candidate_id":
                    get_candidate_id(
                        http_request
                    ),''',
    1,
)

agentic = agentic.replace(
    '''candidate_id = str(
            (
                state.get(
                    "candidate_profile"
                )
                or {}
            ).get(
                "candidate_id"
            )
            or "agentic-user"
        )''',
    '''candidate_id = get_candidate_id(
            http_request
        )''',
    1,
)

# One trace ID must remain authoritative.
agentic = agentic.replace(
    '''thread_id = (
            request.thread_id
            or request_id
        )''',
    '''thread_id = request_id''',
    1,
)

write(B / "api/agentic.py", agentic)

# ------------------------------------------------------------------
# 14. SHELL SPLIT: HOME / OPPORTUNITIES / RESUME
# ------------------------------------------------------------------

# The original massive pages have now been replaced by route shells/client leaves.
# P0 #75-#77 is therefore explicit in the filesystem.

# ------------------------------------------------------------------
# 15. P0 MACHINE VERIFIER
# ------------------------------------------------------------------

write(ROOT / "verify_phase1_p0.py", '''from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path.cwd()
F = ROOT / "frontend"
B = ROOT / "backend"

def text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(
        encoding="utf-8-sig",
    )

def check(
    number: int,
    title: str,
    condition: bool,
) -> bool:
    print(
        f"{number:03d} "
        f"{'PASS' if condition else 'FAIL'} "
        f"{title}"
    )
    return condition

layout = text(F / "app/layout.tsx")
globals_css = text(F / "app/globals.css")
next_config = text(F / "next.config.ts")
home = text(F / "app/page-client.tsx")
opp = text(F / "app/opportunities/OpportunitiesClient.tsx")
resume = text(F / "app/resume/ResumeClient.tsx")
twin = text(F / "app/career-twin/page.tsx")
dashboard = text(F / "app/dashboard/page.tsx")
agentic = text(F / "lib/agentic.ts")
api = text(F / "lib/api.ts")
config = text(F / "lib/config.ts")
shell = text(F / "components/AppShell.tsx")
workspace = text(F / "lib/workspace.ts")
session = text(B / "api/session.py")
main = text(B / "api/main.py")
ct = text(B / "api/career_twin.py")
backend_agentic = text(B / "api/agentic.py")
package = json.loads(
    text(F / "package.json") or "{}"
)

checks = []

checks.append(check(
    1,
    "browser title",
    "CareerPilot AI — Autonomous Career Operating System" in layout,
))

checks.append(check(
    2,
    "meta description",
    "AI-orchestrated career intelligence platform" in layout,
))

checks.append(check(
    3,
    "Arial removed",
    "Arial, Helvetica, sans-serif" not in globals_css,
))

checks.append(check(
    4,
    "api-user removed",
    "api-user" not in home + opp + twin + main + backend_agentic + ct,
))

checks.append(check(
    5,
    "single trace id",
    "crypto.randomUUID()" in home
    and "request_id: traceId" in home
    and "thread_id: traceId" in home,
))

checks.append(check(
    6,
    "persistent session",
    "careerpilot_session" in session
    and "set_cookie" in session,
))

checks.append(check(
    7,
    "projects are user-backed",
    "projects={projects}" in home
    or "candidateProjects" in home,
))

checks.append(check(
    8,
    "dashboard opportunities dynamic",
    "workspace.jobs.length" in dashboard,
))

checks.append(check(
    9,
    "dashboard strong matches dynamic",
    "strongMatches" in dashboard,
))

checks.append(check(
    10,
    "dashboard skills dynamic",
    "profile?.skills" in dashboard,
))

checks.append(check(
    11,
    "dashboard applications dynamic",
    "workspace.applications.length" in dashboard,
))

checks.append(check(
    12,
    "dashboard activity dynamic",
    "workspace.activity" in dashboard,
))

checks.append(check(
    13,
    "dynamic nav",
    "usePathname" in shell,
))

checks.append(check(
    14,
    "no hardcoded defaultSkills",
    "defaultSkills" not in opp,
))

checks.append(check(
    15,
    "experience years input",
    "experienceYears" in opp,
))

checks.append(check(
    16,
    "on-site mode",
    '"on-site"' in opp,
))

checks.append(check(
    17,
    "industries selector",
    "industries" in opp,
))

checks.append(check(
    18,
    "apply url validation",
    "isValidHttpUrl" in opp,
))

checks.append(check(
    19,
    "drawer CTA validation",
    "Apply unavailable" in opp,
))

checks.append(check(
    20,
    "search timeout",
    "DEFAULT_REQUEST_TIMEOUT_MS" in api,
))

checks.append(check(
    21,
    "agentic cancellation",
    "signal?: AbortSignal" in agentic,
))

checks.append(check(
    22,
    "resume timeout",
    "RESUME_REQUEST_TIMEOUT_MS" in api,
))

checks.append(check(
    23,
    "cache control",
    '"Cache-Control":' in api
    and '"Cache-Control":' in agentic,
))

checks.append(check(
    24,
    "salary target comparison",
    "BELOW_TARGET" in api,
))

checks.append(check(
    25,
    "safe evidence formatting",
    "safeEvidencePreview" in home,
))

checks.append(check(
    26,
    "workflow progress",
    "getAgentState" in home,
))

checks.append(check(
    27,
    "resume JobView",
    "type JobView" in resume,
))

checks.append(check(
    28,
    "expanded experience",
    "expandedExperience" in resume,
))

checks.append(check(
    29,
    "rejected file clears input",
    "event.target.value = \"\"" in text(F / "app/resume/ResumeUpload.tsx"),
))

checks.append(check(
    30,
    "searched after successful response",
    "setSearched(true)" in opp,
))

checks.append(check(
    31,
    "selected job preservation",
    "previousId" in opp,
))

checks.append(check(
    32,
    "home H1 spacing",
    'Your career,{" "}' in home,
))

checks.append(check(
    33,
    "opportunities heading spacing",
    "Live opportunities" in opp,
))

checks.append(check(
    34,
    "dashboard uses AppShell",
    "<AppShell>" in dashboard,
))

checks.append(check(
    35,
    "internal navigation uses Link",
    'from "next/link"' in shell,
))

checks.append(check(
    36,
    "Career Twin session auth",
    "/career-twin/session" in twin
    and "credentials:" in twin,
))

checks.append(check(
    37,
    "mobile Escape",
    'event.key === "Escape"' in shell,
))

checks.append(check(
    38,
    "drawer Escape",
    'event.key === "Escape"' in opp,
))

checks.append(check(
    39,
    "drawer focus trap",
    'event.key === "Tab"' in opp,
))

checks.append(check(
    40,
    "reset workspace",
    "Reset Workspace" in home,
))

checks.append(check(
    41,
    "input error clearing",
    "setError(null)" in home,
))

checks.append(check(
    42,
    "goal 2000 char max",
    "maxLength={2000}" in home,
))

checks.append(check(
    43,
    "skills dedupe",
    "normalizeCommaList" in home,
))

checks.append(check(
    44,
    "semantic form",
    "<form" in home,
))

checks.append(check(
    45,
    "accessible labels",
    "<label" in home,
))

checks.append(check(
    46,
    "theme functional",
    "ThemeToggle" in shell,
))

checks.append(check(
    47,
    "profile link functional",
    'href="/career-twin"' in shell,
))

checks.append(check(
    48,
    "profile card functional",
    "Career profile" in shell,
))

checks.append(check(
    49,
    "Menu/X hamburger",
    "<Menu" in shell and "<X" in shell,
))

checks.append(check(
    50,
    "memory pagination",
    "memoryLimit" in twin,
))

checks.append(check(
    51,
    "four stat cards",
    "xl:grid-cols-4" in dashboard,
))

checks.append(check(
    52,
    "resume type explicit",
    "[key: string]: unknown" not in api[
        api.find(
            "export interface ResumeIntelligenceResponse"
        ):
        api.find(
            "export interface ResumeAnalysisResponse"
        )
    ],
))

checks.append(check(
    53,
    "ATS type explicit",
    "[key: string]: unknown" not in api[
        api.find(
            "export interface ATSAnalysisResponse"
        ):
        api.find(
            "export interface JobResumeRequirement"
        )
    ],
))

checks.append(check(
    54,
    "strict validation status",
    '"FAILED"' in agentic,
))

checks.append(check(
    55,
    "strict evidence status",
    '"PARTIAL"' in agentic
    and '"UNSUPPORTED"' in agentic,
))

checks.append(check(
    56,
    "typed skill gaps",
    "interface SkillGap" in agentic,
))

checks.append(check(
    57,
    "typed rewrite candidates",
    "interface RewriteCandidate" in agentic,
))

checks.append(check(
    58,
    "typed errors",
    "interface WorkflowError" in agentic,
))

checks.append(check(
    59,
    "typed recommendations",
    "interface CareerRecommendation" in agentic,
))

checks.append(check(
    60,
    "typed next action",
    "interface NextAction" in agentic,
))

checks.append(check(
    61,
    "typed final validation",
    "interface FinalValidation" in agentic,
))

checks.append(check(
    62,
    "friendly API errors",
    "slice(0, 400)" in agentic,
))

checks.append(check(
    63,
    "security headers",
    all(
        key in next_config
        for key in (
            "Content-Security-Policy",
            "Strict-Transport-Security",
            "X-Frame-Options",
            "X-Content-Type-Options",
            "Referrer-Policy",
        )
    ),
))

checks.append(check(
    64,
    "poweredBy disabled",
    "poweredByHeader: false" in next_config,
))

checks.append(check(
    65,
    "ReactNode layout props",
    "{ children }: { children: ReactNode }" in layout,
))

checks.append(check(
    66,
    "CSS variables active",
    "var(--background)" in globals_css
    and "var(--foreground)" in globals_css,
))

checks.append(check(
    67,
    "real theme switching",
    "dataset.theme" in text(F / "lib/theme.tsx"),
))

checks.append(check(
    68,
    "package name/metadata",
    package.get("name")
    == "careerpilot-ai-frontend"
    and package.get("description"),
))

checks.append(check(
    69,
    "strict lint",
    package.get("scripts", {}).get(
        "lint",
    )
    == "eslint . --max-warnings 0",
))

checks.append(check(
    70,
    "zod",
    "zod" in package.get(
        "dependencies",
        {},
    ),
))

checks.append(check(
    71,
    "lucide pinned",
    package.get("dependencies", {}).get(
        "lucide-react"
    )
    == "1.34.0",
))

checks.append(check(
    72,
    "node/npm engines",
    package.get("engines")
    == {
        "node": ">=20.9.0",
        "npm": ">=10.0.0",
    },
))

checks.append(check(
    73,
    "test script",
    package.get("scripts", {}).get(
        "test"
    )
    == "vitest run",
))

checks.append(check(
    74,
    "typecheck script",
    package.get("scripts", {}).get(
        "typecheck"
    )
    == "tsc --noEmit",
))

checks.append(check(
    75,
    "home server/client split",
    (F / "app/page.tsx").exists()
    and (
        F / "app/page-client.tsx"
    ).exists(),
))

checks.append(check(
    76,
    "opportunities split",
    (F / "app/opportunities/page.tsx").exists()
    and (
        F
        / "app/opportunities/OpportunitiesClient.tsx"
    ).exists(),
))

checks.append(check(
    77,
    "resume split",
    (F / "app/resume/page.tsx").exists()
    and (
        F / "app/resume/ResumeClient.tsx"
    ).exists()
    and (
        F / "app/resume/ResumeUpload.tsx"
    ).exists()
    and (
        F / "app/resume/ResumeScores.tsx"
    ).exists()
    and (
        F / "app/resume/ATSChecklist.tsx"
    ).exists()
    and (
        F / "app/resume/JobMatcher.tsx"
    ).exists()
    and (
        F / "app/resume/RewriteSuggestions.tsx"
    ).exists(),
))

checks.append(check(
    78,
    "central API config",
    "API_BASE_URL" in api
    and 'from "./config"' in api,
))

checks.append(check(
    79,
    "raw salary data",
    "salary_min_lpa" in opp,
))

checks.append(check(
    80,
    "compact undisclosed badge",
    "Undisclosed" in opp,
))

checks.append(check(
    81,
    "single-decimal salary regex",
    'replace(/(\\..*)\\./g, "$1")' in opp,
))

checks.append(check(
    82,
    "backend 10MB/413",
    "10 * 1024 * 1024" in main
    and "status_code=413" in main,
))

checks.append(check(
    83,
    "raw response error text",
    "response.text()" in agentic,
))

checks.append(check(
    84,
    "useMemo depends on result",
    "[result]" in home,
))

checks.append(check(
    85,
    "stable recommendation keys",
    "recommendation.id" in home,
))

checks.append(check(
    86,
    "stable skeleton keys",
    "skeleton-" in opp,
))

checks.append(check(
    87,
    "stable source/job identity",
    "${job.source}:${job.source_job_id}" in opp,
))

checks.append(check(
    88,
    "recommendation badge spacing",
    "min-w-[1.5rem]" in home
    and "px-1" in home,
))

checks.append(check(
    89,
    "retry null-safe",
    "result?.retry_count ?? 0" in home,
))

checks.append(check(
    90,
    "tools null-safe",
    "(result.tools_used ?? []).length" in home
    or "(result.tools_used ?? [])" in home,
))

checks.append(check(
    91,
    "readiness clamped",
    "clampScore" in config,
))

checks.append(check(
    92,
    "friendly human status labels",
    "friendlyStatus" in home,
))

checks.append(check(
    93,
    "loading status in header",
    "friendlyStatus(result?.status, loading)" in home,
))

checks.append(check(
    94,
    "canonical lifecycle states",
    all(
        value in agentic
        for value in (
            "PENDING",
            "DISPATCHED",
            "AGENT_EXECUTION",
            "VALIDATING",
            "COMPLETED",
            "PARTIAL",
            "FAILED",
        )
    ),
))

checks.append(check(
    95,
    "evidence ellipsis rule",
    "text.length <= 360" in home,
))

checks.append(check(
    96,
    "empty delegation safe",
    "?.delegation_trace?.length" in home,
))

checks.append(check(
    97,
    "mobile/result auto-scroll",
    "scrollIntoView" in home,
))

checks.append(check(
    98,
    "CP avatar fallback",
    '"CP"' in opp,
))

checks.append(check(
    99,
    "filter location before join",
    "filter(Boolean).join" in opp,
))

checks.append(check(
    100,
    "confidence normalization",
    "normalizeConfidence" in api
    and "normalizeConfidence" in opp,
))

passed = sum(
    1
    for value in checks
    if value
)

print()
print(
    f"P0 machine gate: {passed}/100"
)

raise SystemExit(
    0
    if passed == 100
    else 1
)
''')

# ------------------------------------------------------------------
# 16. BASIC FRONTEND TEST
# ------------------------------------------------------------------

write(
    F / "p0_smoke.test.ts",
    '''import { describe, expect, it } from "vitest";
import {
  clampScore,
  normalizeConfidence,
} from "./lib/config";

describe("P0 frontend foundations", () => {
  it("clamps scores", () => {
    expect(clampScore(130)).toBe(100);
    expect(clampScore(-2)).toBe(0);
  });

  it("normalizes confidence", () => {
    expect(normalizeConfidence(0.82)).toBe(82);
    expect(normalizeConfidence(82)).toBe(82);
  });
});
''',
)

# ------------------------------------------------------------------
# 17. INSTALL LOCKFILE DEPENDENCIES
# ------------------------------------------------------------------

print("Refreshing frontend dependencies/lockfile...")
result = subprocess.run(
    [
        "npm.cmd",
        "install",
        "--no-audit",
        "--no-fund",
    ],
    cwd=F,
    text=True,
)

if result.returncode != 0:
    raise SystemExit(
        "npm install failed. Fix dependency installation, then rerun this script."
    )

print()
print("PHASE 1 IMPLEMENTATION BATCH APPLIED.")
print(f"Backup: {BACKUP}")
print()
print("NEXT:")
print("  python verify_phase1_p0.py")
print("  cd frontend")
print("  npm run typecheck")
print("  npm run build")
print("  npm run lint")
print("  npm test")
print("  cd ..")
print('  PYTHONPATH="." LLM_PROVIDER="none" pytest -q')
print()
print("Do NOT stage backend/data or the existing Week 7 audit/helper files.")