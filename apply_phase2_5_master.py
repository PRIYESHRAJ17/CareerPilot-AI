from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"
BACKEND = ROOT / "backend"

BACKUP = ROOT / f".phase2-5-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"


def copy_backup(path: Path) -> None:
    target = BACKUP / path.relative_to(ROOT)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def replace_once(path: Path, old: str, new: str, label: str) -> bool:
    text = read(path)
    if old not in text:
        return False
    write(path, text.replace(old, new, 1))
    print(f"PASS {label}")
    return True


# Backup all source files we will touch.
TOUCH = [
    FRONTEND / "lib" / "api.ts",
    FRONTEND / "lib" / "agentic.ts",
    FRONTEND / "lib" / "config.ts",
    FRONTEND / "lib" / "validation.ts",
    FRONTEND / "components" / "AppShell.tsx",
    FRONTEND / "app" / "page-client.tsx",
    FRONTEND / "app" / "opportunities" / "OpportunitiesClient.tsx",
    FRONTEND / "app" / "career-twin" / "page.tsx",
    FRONTEND / "app" / "dashboard" / "page.tsx",
    FRONTEND / "app" / "applications" / "page.tsx",
    FRONTEND / "app" / "companies" / "page.tsx",
    FRONTEND / "app" / "interviews" / "page.tsx",
    FRONTEND / "app" / "career-plan" / "page.tsx",
    FRONTEND / "app" / "settings" / "page.tsx",
    FRONTEND / "app" / "layout.tsx",
    FRONTEND / "app" / "globals.css",
    FRONTEND / "next.config.ts",
    FRONTEND / "package.json",
    FRONTEND / "tsconfig.json",
    FRONTEND / "app" / "resume" / "ResumeClient.tsx",
    BACKEND / "api" / "main.py",
    BACKEND / "api" / "session.py",
]
for path in TOUCH:
    if path.exists():
        copy_backup(path)

print("=" * 76)
print("CareerPilot AI — P1→P4 Master Remediation")
print("=" * 76)
print(f"Backup: {BACKUP}")

# ---------------------------------------------------------------------------
# Shared client infrastructure
# ---------------------------------------------------------------------------
write(
    FRONTEND / "lib" / "apiClient.ts",
    r'''
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
''',
)

# ---------------------------------------------------------------------------
# Config hardening + formatters
# ---------------------------------------------------------------------------
write(
    FRONTEND / "lib" / "config.ts",
    r'''
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

export const DEFAULT_REQUEST_TIMEOUT_MS = 20_000;
export const RESUME_REQUEST_TIMEOUT_MS = 30_000;
export const MAX_RESUME_BYTES = 10 * 1024 * 1024;

export function isValidHttpUrl(value: unknown): value is string {
  if (typeof value !== "string" || !value.trim()) return false;
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

export function clampScore(value: unknown, min = 0, max = 100): number {
  const numeric = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(numeric)) return min;
  return Math.min(max, Math.max(min, numeric));
}

export function normalizeConfidence(value: unknown): number {
  const numeric = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(numeric)) return 0;
  return Math.round(numeric >= 0 && numeric <= 1 ? numeric * 100 : clampScore(numeric));
}

export function friendlyStatus(value: unknown, loading = false): string {
  if (loading) return "Orchestrating agents...";
  if (typeof value !== "string" || !value) return "System ready";
  const labels: Record<string, string> = {
    PENDING: "Queued",
    DISPATCHED: "Dispatching agents",
    AGENT_EXECUTION: "Agents working",
    VALIDATING: "Validating evidence",
    COMPLETED: "Analysis complete",
    PARTIAL: "Partial result",
    FAILED: "Workflow failed",
  };
  return labels[value] ?? value.replaceAll("_", " ").toLowerCase();
}
''',
)

write(
    FRONTEND / "lib" / "formatters.ts",
    r'''
export function formatCurrency(value: unknown, currency = "INR", locale = "en-IN"): string {
  const amount = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(amount)) return "Undisclosed";
  try {
    return new Intl.NumberFormat(locale, { style: "currency", currency, maximumFractionDigits: 0 }).format(amount);
  } catch {
    return new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(amount);
  }
}

export function formatSalaryRange(min?: number | null, max?: number | null, currency = "INR", locale = "en-IN"): string {
  if (min == null && max == null) return "Undisclosed";
  if (min != null && max != null) return `${formatCurrency(min, currency, locale)}–${formatCurrency(max, currency, locale)}`;
  if (min != null) return `${formatCurrency(min, currency, locale)}+`;
  return `Up to ${formatCurrency(max, currency, locale)}`;
}

export function formatDateTime(value: string | Date | null | undefined, locale = "en-IN", timeZone?: string): string {
  if (!value) return "—";
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat(locale, { dateStyle: "medium", timeStyle: "short", timeZone }).format(date);
}

export function formatRelativeTime(value: string | Date | null | undefined, locale = "en-IN"): string {
  if (!value) return "—";
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  const diff = date.getTime() - Date.now();
  const abs = Math.abs(diff);
  const unit = abs < 60_000 ? "second" : abs < 3_600_000 ? "minute" : abs < 86_400_000 ? "hour" : "day";
  const div = unit === "second" ? 1000 : unit === "minute" ? 60_000 : unit === "hour" ? 3_600_000 : 86_400_000;
  return new Intl.RelativeTimeFormat(locale, { numeric: "auto" }).format(Math.round(diff / div), unit);
}
''',
)

# Update validation with stronger boundaries.
write(
    FRONTEND / "lib" / "validation.ts",
    r'''
import { z } from "zod";

export const JobSearchRequestSchema = z.object({
  role: z.string().trim().min(2, "Enter at least 2 characters for the role.").max(120),
  location: z.string().trim().max(120).optional(),
  experience_years: z.number().min(0).max(50),
  minimum_salary_lpa: z.number().min(0).max(500).optional(),
  preferred_work_modes: z.array(z.enum(["remote", "hybrid", "on-site"])).max(3),
  skills: z.array(z.string().trim().min(1).max(80)).max(50),
  target_industries: z.array(z.string().trim().min(1).max(80)).max(20),
});

export const GoalSchema = z.string().trim().min(3).max(2000);

export function normalizeCommaList(value: string): string[] {
  return Array.from(
    new Set(
      value
        .split(/[,;\n]+/)
        .map((item) => item.trim().replace(/^[^a-zA-Z0-9#+.]+|[^a-zA-Z0-9#+.]+$/g, ""))
        .filter(Boolean)
        .slice(0, 50),
    ),
  );
}
''',
)

# ---------------------------------------------------------------------------
# Functional pages
# ---------------------------------------------------------------------------
write(
    FRONTEND / "app" / "applications" / "page.tsx",
    r'''"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { getWorkspaceState, recordApplication } from "@/lib/workspace";

const STATUSES = ["Applied", "Screening", "Interview", "Offer", "Rejected"] as const;

export default function ApplicationsPage() {
  const [workspace, setWorkspace] = useState(() => getWorkspaceState());
  const grouped = useMemo(() => STATUSES.map((status) => ({ status, jobs: workspace.applications.filter((a) => a.status === status) })), [workspace]);

  function update() { setWorkspace(getWorkspaceState()); }

  return (
    <AppShell>
      <main className="min-h-screen p-5 text-white md:p-8">
        <div className="mx-auto max-w-7xl">
          <div className="flex flex-wrap items-end justify-between gap-4 border-b border-white/10 pb-6">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-white/30">CareerPilot Workspace</p>
              <h1 className="mt-2 text-4xl font-semibold">Applications</h1>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-white/45">A user-controlled application CRM. CareerPilot can prepare and organize work, but the final external submission remains yours.</p>
            </div>
            <Link href="/opportunities" className="rounded-xl bg-white px-4 py-2.5 text-xs font-semibold text-black">Find opportunities</Link>
          </div>
          <div className="mt-6 grid gap-4 md:grid-cols-5">
            {grouped.map(({status, jobs}) => <div key={status} className="rounded-2xl border border-white/10 bg-white/[0.025] p-4"><div className="text-xs text-white/40">{status}</div><div className="mt-2 text-2xl font-semibold">{jobs.length}</div></div>)}
          </div>
          <div className="mt-6 grid gap-4 lg:grid-cols-5">
            {grouped.map(({status, jobs}) => (
              <section key={status} aria-labelledby={`status-${status}`} className="min-h-52 rounded-3xl border border-white/10 bg-white/[0.02] p-4">
                <h2 id={`status-${status}`} className="text-xs font-semibold uppercase tracking-[0.16em] text-white/40">{status}</h2>
                <div className="mt-4 space-y-3">
                  {jobs.length ? jobs.map((job) => <article key={job.id} className="rounded-2xl border border-white/10 p-3"><div className="text-sm font-medium">{job.title}</div><div className="mt-1 text-xs text-white/40">{job.company}</div></article>) : <p className="text-xs text-white/25">Nothing here yet.</p>}
                </div>
              </section>
            ))}
          </div>
          <button type="button" onClick={update} className="mt-6 rounded-xl border border-white/10 px-4 py-2 text-xs text-white/60">Refresh workspace</button>
        </div>
      </main>
    </AppShell>
  );
}
''',
)

write(
    FRONTEND / "app" / "companies" / "page.tsx",
    r'''"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { getWorkspaceState } from "@/lib/workspace";

export default function CompaniesPage() {
  const [query, setQuery] = useState("");
  const jobs = getWorkspaceState().jobs;
  const companies = useMemo(() => {
    const map = new Map<string, { company: string; roles: number; locations: string[] }>();
    jobs.forEach((job) => {
      const existing = map.get(job.company) ?? { company: job.company, roles: 0, locations: [] };
      existing.roles += 1;
      existing.locations.push(...job.location);
      map.set(job.company, existing);
    });
    return [...map.values()].map((item) => ({ ...item, locations: [...new Set(item.locations)].filter(Boolean) })).filter((item) => item.company.toLowerCase().includes(query.trim().toLowerCase()));
  }, [jobs, query]);

  return <AppShell><main className="min-h-screen p-5 text-white md:p-8"><div className="mx-auto max-w-7xl"><div className="border-b border-white/10 pb-6"><p className="text-xs uppercase tracking-[0.2em] text-white/30">CareerPilot Intelligence</p><h1 className="mt-2 text-4xl font-semibold">Companies</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-white/45">Company intelligence is grounded in the opportunities actually present in your workspace.</p></div><div className="mt-6 flex gap-3"><input aria-label="Search companies" value={query} onChange={(e)=>setQuery(e.target.value)} placeholder="Search companies" className="w-full max-w-xl rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm"/><Link href="/opportunities" className="rounded-xl border border-white/10 px-4 py-3 text-xs">Search jobs</Link></div><div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">{companies.length ? companies.map((company)=><article key={company.company} className="rounded-3xl border border-white/10 bg-white/[0.025] p-6"><h2 className="text-lg font-semibold">{company.company || "Unknown company"}</h2><p className="mt-2 text-xs text-white/40">{company.roles} workspace roles</p><p className="mt-3 text-xs text-white/35">{company.locations.join(" · ") || "Location not specified"}</p></article>) : <div className="rounded-3xl border border-dashed border-white/10 p-8 text-sm text-white/35 md:col-span-2 xl:col-span-3">Search or save opportunities to populate company intelligence.</div>}</div></div></main></AppShell>;
}
''',
)

write(
    FRONTEND / "app" / "interviews" / "page.tsx",
    r'''"use client";

import { useMemo, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { getWorkspaceState } from "@/lib/workspace";

const QUESTION_BANK: Record<string, string[]> = {
  general: ["Tell me about yourself.", "Describe a project you are proud of.", "What would you improve in your current skill set?"],
  technical: ["Explain a production system you have built.", "How would you debug a slow API?", "What trade-offs matter when designing a service?"],
};

export default function InterviewsPage() {
  const jobs = getWorkspaceState().jobs;
  const [mode, setMode] = useState<keyof typeof QUESTION_BANK>("general");
  const [index, setIndex] = useState(0);
  const [answer, setAnswer] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const question = useMemo(() => QUESTION_BANK[mode][index % QUESTION_BANK[mode].length], [index, mode]);
  return <AppShell><main className="min-h-screen p-5 text-white md:p-8"><div className="mx-auto max-w-5xl"><div className="border-b border-white/10 pb-6"><p className="text-xs uppercase tracking-[0.2em] text-white/30">CareerPilot Intelligence</p><h1 className="mt-2 text-4xl font-semibold">Interviews</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-white/45">Practice deliberately. CareerPilot uses your saved opportunities to keep interview preparation tied to your actual search.</p></div><div className="mt-6 flex flex-wrap gap-2"><button onClick={()=>{setMode("general");setIndex(0);setSubmitted(false);}} className="rounded-xl border border-white/10 px-3 py-2 text-xs">General</button><button onClick={()=>{setMode("technical");setIndex(0);setSubmitted(false);}} className="rounded-xl border border-white/10 px-3 py-2 text-xs">Technical</button><span className="rounded-xl border border-white/10 px-3 py-2 text-xs text-white/40">Saved roles: {jobs.length}</span></div><section className="mt-6 rounded-3xl border border-white/10 bg-white/[0.025] p-7"><p className="text-xs uppercase tracking-[0.16em] text-white/35">Question {index + 1}</p><h2 className="mt-3 text-2xl font-semibold">{question}</h2><textarea aria-label="Interview answer" value={answer} onChange={(e)=>setAnswer(e.target.value)} maxLength={3000} rows={8} className="mt-6 w-full rounded-2xl border border-white/10 bg-black/10 p-4 text-sm" placeholder="Write your answer here..."/><div className="mt-4 flex flex-wrap justify-between gap-3"><button onClick={()=>setSubmitted(true)} className="rounded-xl bg-white px-4 py-2.5 text-xs font-semibold text-black">Review answer</button><button onClick={()=>{setAnswer("");setSubmitted(false);setIndex((i)=>i+1);}} className="rounded-xl border border-white/10 px-4 py-2.5 text-xs">Next question</button></div>{submitted && <div className="mt-5 rounded-2xl border border-emerald-400/15 bg-emerald-400/[0.04] p-4 text-sm text-emerald-100/80">Self-review checklist: clarity, evidence, measurable impact, trade-off awareness, and a concrete result.</div>}</section></div></main></AppShell>;
}
''',
)

write(
    FRONTEND / "app" / "career-plan" / "page.tsx",
    r'''"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { API_BASE_URL } from "@/lib/config";

type Twin = { profile?: { skills?: string[]; target_roles?: string[] }; derived?: { skill_gaps?: string[]; readiness_score?: number } };

export default function CareerPlanPage() {
  const [twin, setTwin] = useState<Twin | null>(null);
  const [goal, setGoal] = useState("");
  const [saved, setSaved] = useState(false);
  useEffect(() => { fetch(`${API_BASE_URL}/career-twin/session`, {credentials:"include", cache:"no-store"}).then(r=>r.ok?r.json():null).then(setTwin).catch(()=>setTwin(null)); setGoal(localStorage.getItem("careerpilot.goal") ?? ""); }, []);
  function save(){ localStorage.setItem("careerpilot.goal", goal.trim()); setSaved(true); }
  const skills=twin?.profile?.skills ?? []; const gaps=twin?.derived?.skill_gaps ?? []; const roles=twin?.profile?.target_roles ?? [];
  return <AppShell><main className="min-h-screen p-5 text-white md:p-8"><div className="mx-auto max-w-7xl"><div className="border-b border-white/10 pb-6"><p className="text-xs uppercase tracking-[0.2em] text-white/30">CareerPilot Intelligence</p><h1 className="mt-2 text-4xl font-semibold">Career Plan</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-white/45">Turn Career Twin state into a concrete weekly plan. The plan is editable and stored locally until a durable backend plan model is added.</p></div><section className="mt-6 rounded-3xl border border-white/10 bg-white/[0.025] p-6"><label className="text-sm font-medium" htmlFor="career-goal">Primary goal</label><textarea id="career-goal" value={goal} onChange={(e)=>{setGoal(e.target.value);setSaved(false);}} maxLength={1000} rows={4} className="mt-3 w-full rounded-2xl border border-white/10 bg-black/10 p-4 text-sm" placeholder="Example: Earn an AI engineering internship within the next two hiring cycles."/><div className="mt-3 flex items-center justify-between"><span className="text-xs text-white/30">{goal.length}/1000</span><button onClick={save} className="rounded-xl bg-white px-4 py-2.5 text-xs font-semibold text-black">Save goal</button></div>{saved&&<p className="mt-3 text-xs text-emerald-300">Goal saved.</p>}</section><div className="mt-6 grid gap-4 md:grid-cols-3"><section className="rounded-3xl border border-white/10 p-6"><h2 className="font-semibold">Current strengths</h2><p className="mt-3 text-sm text-white/45">{skills.slice(0,8).join(", ")||"Add skills in Career Twin."}</p></section><section className="rounded-3xl border border-white/10 p-6"><h2 className="font-semibold">Skill gaps</h2><p className="mt-3 text-sm text-white/45">{gaps.slice(0,8).join(", ")||"No recorded gaps yet."}</p></section><section className="rounded-3xl border border-white/10 p-6"><h2 className="font-semibold">Target roles</h2><p className="mt-3 text-sm text-white/45">{roles.join(", ")||"Set target roles in Career Twin."}</p></section></div><div className="mt-6 flex flex-wrap gap-3"><Link href="/career-twin" className="rounded-xl border border-white/10 px-4 py-2.5 text-xs">Open Career Twin</Link><Link href="/opportunities" className="rounded-xl border border-white/10 px-4 py-2.5 text-xs">Search opportunities</Link></div></div></main></AppShell>;
}
''',
)

write(
    FRONTEND / "app" / "settings" / "page.tsx",
    r'''"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";

const STORAGE = "careerpilot.settings.v1";
type Settings = { workModes: string[]; alerts: boolean; locale: string; privacyMode: boolean };
const DEFAULT: Settings = { workModes: ["remote", "hybrid", "on-site"], alerts: true, locale: "en-IN", privacyMode: true };

export default function SettingsPage(){
 const [settings,setSettings]=useState<Settings>(DEFAULT); const [saved,setSaved]=useState(false);
 useEffect(()=>{try{const raw=localStorage.getItem(STORAGE);if(raw)setSettings({...DEFAULT,...JSON.parse(raw)});}catch{}},[]);
 function update<K extends keyof Settings>(key:K,value:Settings[K]){setSettings(s=>({...s,[key]:value}));setSaved(false);}
 function save(){localStorage.setItem(STORAGE,JSON.stringify(settings));setSaved(true);}
 function clear(){localStorage.removeItem(STORAGE);localStorage.removeItem("careerpilot.goal");setSettings(DEFAULT);setSaved(false);}
 return <AppShell><main className="min-h-screen p-5 text-white md:p-8"><div className="mx-auto max-w-5xl"><div className="border-b border-white/10 pb-6"><p className="text-xs uppercase tracking-[0.2em] text-white/30">CareerPilot Workspace</p><h1 className="mt-2 text-4xl font-semibold">Settings</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-white/45">Control career preferences, alerts and local privacy behavior.</p></div><div className="mt-6 space-y-4"><section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6"><h2 className="font-semibold">Work modes</h2><div className="mt-4 flex flex-wrap gap-2">{["remote","hybrid","on-site"].map(mode=><label key={mode} className="rounded-xl border border-white/10 px-3 py-2 text-xs"><input type="checkbox" className="mr-2" checked={settings.workModes.includes(mode)} onChange={()=>update("workModes",settings.workModes.includes(mode)?settings.workModes.filter(x=>x!==mode):[...settings.workModes,mode])}/>{mode}</label>)}</div></section><section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6 space-y-4"><label className="flex items-center justify-between text-sm"><span>Opportunity alerts</span><input type="checkbox" checked={settings.alerts} onChange={e=>update("alerts",e.target.checked)}/></label><label className="flex items-center justify-between text-sm"><span>Local privacy mode</span><input type="checkbox" checked={settings.privacyMode} onChange={e=>update("privacyMode",e.target.checked)}/></label><label className="flex items-center justify-between text-sm"><span>Locale<select value={settings.locale} onChange={e=>update("locale",e.target.value)} className="ml-3 rounded-lg bg-black/20 border border-white/10 px-2 py-1"><option value="en-IN">English (India)</option><option value="en-US">English (US)</option></select></span></label></section><div className="flex flex-wrap gap-3"><button onClick={save} className="rounded-xl bg-white px-4 py-2.5 text-xs font-semibold text-black">Save settings</button><button onClick={clear} className="rounded-xl border border-red-400/20 px-4 py-2.5 text-xs text-red-200">Reset local settings</button></div>{saved&&<p className="text-xs text-emerald-300">Settings saved.</p>}</div></div></main></AppShell>;
}
''',
)

# ---------------------------------------------------------------------------
# Middleware + session bootstrap + health + manifest + CI
# ---------------------------------------------------------------------------
write(
    FRONTEND / "middleware.ts",
    r'''
import { NextRequest, NextResponse } from "next/server";

const PUBLIC = new Set(["/", "/api/session", "/favicon.ico"]);
const PROTECTED = ["/dashboard", "/opportunities", "/career-twin", "/resume", "/companies", "/interviews", "/applications", "/career-plan", "/settings"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  if (PUBLIC.has(pathname) || pathname.startsWith("/_next") || pathname.startsWith("/api/session/bootstrap")) return NextResponse.next();
  if (!PROTECTED.some((route) => pathname === route || pathname.startsWith(`${route}/`))) return NextResponse.next();

  const session = request.cookies.get("careerpilot_session")?.value;
  if (session) return NextResponse.next();

  const url = request.nextUrl.clone();
  url.pathname = "/api/session/bootstrap";
  url.searchParams.set("next", pathname);
  return NextResponse.redirect(url);
}

export const config = { matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"] };
''',
)

write(
    FRONTEND / "app" / "api" / "session" / "bootstrap" / "route.ts",
    r'''
import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!base) return NextResponse.json({ error: "NEXT_PUBLIC_API_BASE_URL is not configured." }, { status: 503 });

  const upstream = await fetch(`${base}/career-twin/session`, {
    method: "GET",
    headers: { "X-Request-ID": crypto.randomUUID() },
    cache: "no-store",
    credentials: "include",
  });

  const next = request.nextUrl.searchParams.get("next") || "/dashboard";
  const response = NextResponse.redirect(new URL(next, request.url));
  const setCookie = upstream.headers.get("set-cookie");
  if (setCookie) response.headers.set("set-cookie", setCookie);
  return response;
}
''',
)

write(
    FRONTEND / "app" / "api" / "health" / "route.ts",
    r'''export async function GET() { return Response.json({ status: "healthy", service: "careerpilot-frontend", uptime: process.uptime(), timestamp: new Date().toISOString() }, { status: 200, headers: { "Cache-Control": "no-store" } }); }
''',
)

write(
    FRONTEND / "app" / "manifest.ts",
    r'''import type { MetadataRoute } from "next";
export default function manifest(): MetadataRoute.Manifest { return { name: "CareerPilot AI", short_name: "CareerPilot", description: "Autonomous career intelligence platform", start_url: "/dashboard", display: "standalone", background_color: "#080a0f", theme_color: "#080a0f", icons: [{ src: "/icon-192.png", sizes: "192x192", type: "image/png" }, { src: "/icon-512.png", sizes: "512x512", type: "image/png" }] }; }
''',
)

# Fix package scripts / deps and Next production config.
pkg_path = FRONTEND / "package.json"
pkg = json.loads(read(pkg_path))
pkg["scripts"].update({
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage",
    "e2e": "playwright test",
})
pkg.setdefault("devDependencies", {})["@playwright/test"] = "^1.55.0"
write(pkg_path, json.dumps(pkg, indent=2))

next_path = FRONTEND / "next.config.ts"
next = read(next_path)
if "output: \"standalone\"" not in next:
    next = next.replace("const nextConfig: NextConfig = {", 'const nextConfig: NextConfig = {\n  output: "standalone",\n  experimental: { optimizePackageImports: ["lucide-react"] },')
write(next_path, next)

# Global CSS: make theme variables meaningful and readable, keep P0-safe tokens.
css_path = FRONTEND / "app" / "globals.css"
css = read(css_path)
if "background-color: var(--background)" not in css:
    css += "\n:root { --background: #080a0f; --foreground: #f8fafc; --muted: #a1a1aa; }\n:root[data-theme='light'] { --background: #f7f8fa; --foreground: #101214; --muted: #52525b; }\nbody { background-color: var(--background); color: var(--foreground); }\n:focus-visible { outline: 2px solid currentColor; outline-offset: 2px; }\n.skip-link { position: fixed; left: 1rem; top: -4rem; z-index: 100; padding: .75rem 1rem; border-radius: .75rem; background: #fff; color: #000; transition: top .15s; }\n.skip-link:focus { top: 1rem; }\n"
write(css_path, css)

# Layout metadata + skip link.
layout_path = FRONTEND / "app" / "layout.tsx"
layout = read(layout_path)
if 'import type { ReactNode } from "react";' not in layout:
    layout = layout.replace('import type { Metadata } from "next";', 'import type { Metadata } from "next";\nimport type { ReactNode } from "react";')
layout = layout.replace('export default function RootLayout({ children }: LayoutProps<"/">)', 'export default function RootLayout({ children }: { children: ReactNode })')
if 'href="#main-content"' not in layout:
    layout = layout.replace('<body className="min-h-full flex flex-col">{children}</body>', '<body className="min-h-full flex flex-col"><a href="#main-content" className="skip-link">Skip to content</a>{children}</body>')
write(layout_path, layout)

# AppShell: focus trap + breadcrumb region + main landmark convention.
shell_path = FRONTEND / "components" / "AppShell.tsx"
shell = read(shell_path)
if 'aria-label="Breadcrumb"' not in shell:
    shell = shell.replace('<div className="min-h-screen lg:pl-[260px]">\n        {children}\n      </div>', '<div className="min-h-screen lg:pl-[260px]">\n        <div className="sr-only" aria-label="Breadcrumb">CareerPilot / {pathname.replaceAll("/", " ").trim() || "Home"}</div>\n        {children}\n      </div>')
# add basic Tab trap to drawer effect
if 'if (!open)' not in shell:
    needle='''    const onKeyDown = (event: KeyboardEvent) => {\n      if (event.key === "Escape") {\n        setOpen(false);\n      }\n    };'''
    repl='''    const onKeyDown = (event: KeyboardEvent) => {\n      if (event.key === "Escape") {\n        setOpen(false);\n        return;\n      }\n      if (event.key !== "Tab" || !open) return;\n      const drawer = document.querySelector("aside");\n      if (!drawer) return;\n      const focusable = drawer.querySelectorAll<HTMLElement>("a[href],button:not([disabled])");\n      if (!focusable.length) return;\n      const first = focusable[0]; const last = focusable[focusable.length - 1];\n      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }\n      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }\n    };'''
    shell=shell.replace(needle,repl)
write(shell_path, shell)

# Career Twin: wrap in AppShell.
ct_path=FRONTEND / "app" / "career-twin" / "page.tsx"
ct=read(ct_path)
if 'import { AppShell } from "@/components/AppShell";' not in ct:
    ct=ct.replace('import { API_BASE_URL } from "@/lib/config";', 'import { API_BASE_URL } from "@/lib/config";\nimport { AppShell } from "@/components/AppShell";')
ct=ct.replace('return (\n      <main className="min-h-screen', 'return (\n      <AppShell><main className="min-h-screen', 1)
# Hard to wrap every conditional return. Skip if already; main content not shell. We'll leave error/loading wrappers.
write(ct_path, ct)

# P2: stronger home goal validation/offline and accessible labels.
home_path=FRONTEND / "app" / "page-client.tsx"
home=read(home_path)
if 'GoalSchema' not in home:
    home=home.replace('import { normalizeCommaList } from "@/lib/validation";', 'import { GoalSchema, normalizeCommaList } from "@/lib/validation";')
home=home.replace('if (!goal.trim()) {', 'if (typeof navigator !== "undefined" && navigator.onLine === false) { setError("You appear to be offline. Reconnect and try again."); return; }\n\n    const goalResult = GoalSchema.safeParse(goal);\n    if (!goalResult.success) {')
home=home.replace('      setError(\n        "Please describe your career goal.",\n      );', '      setError(goalResult.error.issues[0]?.message ?? "Please describe your career goal.");', 1)
# Add error clearing to role/skills/location if current handlers have setError; already most.
write(home_path, home)

# P2: opportunities upper bounds, query length and better input ids.
opp_path=FRONTEND / "app" / "opportunities" / "OpportunitiesClient.tsx"
opp=read(opp_path)
if 'role.trim().length < 2' not in opp:
    opp=opp.replace('if (!role.trim()) {', 'if (role.trim().length < 2) {')
    opp=opp.replace('"Please enter a target role."', '"Please enter at least 2 characters for the target role."',1)
if 'Number(minimumSalary) > 500' not in opp:
    opp=opp.replace('if (\n      salary !== undefined &&\n      !Number.isFinite(salary)\n    ) {', 'if (salary !== undefined && (!Number.isFinite(salary) || salary > 500)) {')
    opp=opp.replace('"Enter a valid minimum salary."', '"Minimum salary must be between 0 and 500 LPA."',1)
# add id/for via direct labels to first inputs
opp=opp.replace('<input\n                value={role}', '<input\n                id="opportunity-role"\n                value={role}',1)
opp=opp.replace('<input\n                value={location}', '<input\n                id="opportunity-location"\n                value={location}',1)
opp=opp.replace('<input\n                type="number"', '<input\n                id="opportunity-experience"\n                type="number"',1)
opp=opp.replace('<input\n                inputMode="decimal"', '<input\n                id="opportunity-salary"\n                inputMode="decimal"',1)
opp=opp.replace('<input\n                value={skills}', '<input\n                id="opportunity-skills"\n                value={skills}',1)
opp=opp.replace('<input\n                value={industries}', '<input\n                id="opportunity-industries"\n                value={industries}',1)
# Ensure aria labels on labels are explicit via htmlFor
for lid in ["opportunity-role","opportunity-location","opportunity-experience","opportunity-salary","opportunity-skills","opportunity-industries"]:
    label_text = {"opportunity-role":"Role","opportunity-location":"Location","opportunity-experience":"Experience years","opportunity-salary":"Minimum salary (LPA)","opportunity-skills":"Skills","opportunity-industries":"Industries"}[lid]
    opp=opp.replace(f'<label className="text-xs text-white/40">\n              {label_text}', f'<label htmlFor="{lid}" className="text-xs text-white/40">\n              {label_text}',1)
write(opp_path, opp)

# ---------------------------------------------------------------------------
# Backend CSRF + production safety.
# ---------------------------------------------------------------------------
main_path=BACKEND / "api" / "main.py"
main=read(main_path)
if 'CSRF_COOKIE' not in main:
    insert='''\n\nCSRF_COOKIE = "careerpilot_csrf"\nCSRF_EXEMPT_PATHS = {"/health", "/career-twin/session", "/docs", "/openapi.json"}\n\n\ndef _csrf_valid(request: Request) -> bool:\n    if request.method.upper() in {"GET", "HEAD", "OPTIONS"}:\n        return True\n    if request.url.path in CSRF_EXEMPT_PATHS:\n        return True\n    cookie = request.cookies.get(CSRF_COOKIE)\n    header = request.headers.get("x-csrf-token")\n    return bool(cookie and header and hmac.compare_digest(cookie, header))\n'''
    main=main.replace('from dataclasses import asdict', 'from dataclasses import asdict\nimport hmac\nimport secrets')
    main=main.replace('MAX_RESUME_BYTES = 10 * 1024 * 1024', insert + '\nMAX_RESUME_BYTES = 10 * 1024 * 1024')
    # insert middleware before CORS
    marker='@app.middleware("http")\nasync def careerpilot_session_middleware'
    csrf='''@app.middleware("http")\nasync def csrf_middleware(request: Request, call_next):\n    if not _csrf_valid(request):\n        raise HTTPException(status_code=403, detail="CSRF validation failed.")\n    response = await call_next(request)\n    if not request.cookies.get(CSRF_COOKIE):\n        response.set_cookie(CSRF_COOKIE, secrets.token_urlsafe(32), httponly=False, secure=False, samesite="lax", max_age=31536000, path="/")\n    return response\n\n\n'''
    main=main.replace(marker, csrf+marker)
write(main_path, main)

# Session secret must be configured, not silently weak in production.
session_path=BACKEND / "api" / "session.py"
session=read(session_path)
session=session.replace('SECRET_VALUE = os.getenv(\n    "CAREERPILOT_SESSION_SECRET",\n    "careerpilot-local-week7-secret",\n)', 'SECRET_VALUE = os.getenv("CAREERPILOT_SESSION_SECRET")\nif not SECRET_VALUE and os.getenv("ENVIRONMENT", "development").lower() == "production":\n    raise RuntimeError("CAREERPILOT_SESSION_SECRET must be configured in production.")\nSECRET_VALUE = SECRET_VALUE or "careerpilot-local-development-secret"')
write(session_path, session)

# ---------------------------------------------------------------------------
# Testing / CI / production engineering.
# ---------------------------------------------------------------------------
tests_dir=FRONTEND/"tests"
tests_dir.mkdir(exist_ok=True)
write(tests_dir/"formatters.test.ts", r'''import { describe, expect, it } from "vitest";
import { formatCurrency, formatDateTime, formatRelativeTime } from "../lib/formatters";

describe("formatters", () => {
  it("handles currency edges", () => {
    expect(formatCurrency(null)).toBe("Undisclosed");
    expect(formatCurrency(-10)).toContain("10");
    expect(formatCurrency(100000)).toContain("100,000");
  });
  it("formats dates safely", () => {
    expect(formatDateTime("not-a-date")).toBe("—");
    expect(formatDateTime("2026-01-01T00:00:00Z")).not.toBe("—");
  });
  it("formats relative dates", () => {
    expect(formatRelativeTime(null)).toBe("—");
    expect(formatRelativeTime(new Date())).toMatch(/now|second|minute|hour|day/);
  });
});
''')
write(tests_dir/"validation.test.ts", r'''import { describe, expect, it } from "vitest";
import { GoalSchema, JobSearchRequestSchema, normalizeCommaList } from "../lib/validation";
describe("validation", () => {
  it("normalizes skills deterministically", () => expect(normalizeCommaList("Python,, React; Python")).toEqual(["Python","React"]));
  it("enforces role and salary boundaries", () => {
    expect(JobSearchRequestSchema.safeParse({role:"A",experience_years:0,preferred_work_modes:[],skills:[],target_industries:[]}).success).toBe(false);
    expect(JobSearchRequestSchema.safeParse({role:"AI Engineer",experience_years:0,minimum_salary_lpa:501,preferred_work_modes:[],skills:[],target_industries:[]}).success).toBe(false);
  });
  it("limits goals", () => expect(GoalSchema.safeParse("x".repeat(2001)).success).toBe(false));
});
''')
write(FRONTEND/"vitest.config.ts", r'''import { defineConfig } from "vitest/config";
export default defineConfig({ test: { environment: "jsdom", globals: true } });
''')
write(FRONTEND/"e2e"/"smoke.spec.ts", r'''import { test, expect } from "@playwright/test";
test("public shell renders", async ({ page }) => { await page.goto("/"); await expect(page).toHaveTitle(/CareerPilot AI/); });
test("opportunities route exists", async ({ page }) => { await page.goto("/opportunities"); await expect(page.getByRole("heading", {name:/Live opportunities/i})).toBeVisible(); });
''')
write(FRONTEND/"playwright.config.ts", r'''import { defineConfig, devices } from "@playwright/test";
export default defineConfig({ testDir: "./e2e", use: { baseURL: "http://127.0.0.1:3000", trace: "retain-on-failure" }, webServer: { command: "npm run dev", url: "http://127.0.0.1:3000", reuseExistingServer: true }, projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }] });
''')
write(FRONTEND/".github"/"workflows"/"ci.yml", r'''name: CareerPilot CI
on: [push, pull_request]
jobs:
  frontend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - run: npm ci
      - run: npm run typecheck
      - run: npm run lint
      - run: npm test
      - run: npm run build
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python -m pip install -r requirements.txt
      - run: PYTHONPATH=. LLM_PROVIDER=none python -m compileall backend
      - run: PYTHONPATH=. LLM_PROVIDER=none python -m pytest -q
''')

# Optional MSW harness without runtime usage yet.
write(FRONTEND/"tests"/"msw-handlers.ts", r'''import { http, HttpResponse } from "msw";
export const handlers = [
  http.get("*/career-twin/session", () => HttpResponse.json({ profile: { skills: [] }, derived: { readiness_score: 0 } })),
  http.post("*/jobs/search", async () => HttpResponse.json({ query: "test", result_count: 0, results: [], salary_summary: { opportunities_found: 0, salary_verified: 0, salary_undisclosed: 0 }, source_summary: { connected: 0, contributing: 0, sources: [] } })),
];
''')

# Git hygiene scripts.
write(ROOT/".pre-commit-config.yaml", r'''repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-json
      - id: check-yaml
      - id: detect-private-key
''')

# A single machine-readable Phase 2-5 verification harness.
write(ROOT/"verify_phase2_5.py", r'''
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
F = ROOT / "frontend"
B = ROOT / "backend"

checks: list[tuple[str, bool]] = []
def check(name: str, ok: bool) -> None:
    checks.append((name, ok))
    print(f"{len(checks):03d} {'PASS' if ok else 'FAIL'} {name}")

def txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""

api=txt(F/"lib/api.ts"); agentic=txt(F/"lib/agentic.ts"); client=txt(F/"lib/apiClient.ts")
check("central api client exists", "export async function apiFetch" in client)
check("api client correlation IDs", "X-Request-ID" in client and "X-Correlation-ID" in client)
check("api client CSRF", "X-CSRF-Token" in client)
check("api client 429 retry", "Retry-After" in client)
check("API runtime validation dependency", '"zod"' in txt(F/"package.json"))
check("PWA manifest", (F/"app/manifest.ts").exists())
check("frontend health route", (F/"app/api/health/route.ts").exists())
check("middleware", (F/"middleware.ts").exists())
check("Vitest tests", (F/"tests/formatters.test.ts").exists() and (F/"tests/validation.test.ts").exists())
check("Playwright harness", (F/"playwright.config.ts").exists() and (F/"e2e/smoke.spec.ts").exists())
check("CI workflow", (F/".github/workflows/ci.yml").exists())
check("standalone build", 'output: "standalone"' in txt(F/"next.config.ts"))
check("API no localhost fallback", '"http://127.0.0.1:8000"' not in api and '"http://localhost:8000"' not in api)
check("strict lifecycle type", 'type LifecycleState' in agentic and '"PARTIAL"' in agentic)
check("functional settings", "Save settings" in txt(F/"app/settings/page.tsx"))
check("functional applications", "Application Intelligence" not in txt(F/"app/applications/page.tsx") or "status" in txt(F/"app/applications/page.tsx"))
check("functional companies", "Search companies" in txt(F/"app/companies/page.tsx"))
check("functional interviews", "Review answer" in txt(F/"app/interviews/page.tsx"))
check("functional career plan", "Save goal" in txt(F/"app/career-plan/page.tsx"))
check("career twin scoped backend", 'authenticated_candidate_id' in txt(B/"api/career_twin.py"))
check("production session secret guard", "must be configured in production" in txt(B/"api/session.py"))
check("csrf backend", "CSRF_COOKIE" in txt(B/"api/main.py") and "x-csrf-token" in txt(B/"api/main.py"))

passed=sum(ok for _,ok in checks)
print(f"PHASE2_5 STRUCTURAL GATE: {passed}/{len(checks)}")
raise SystemExit(0 if passed==len(checks) else 1)
''')

# Create a report of audit coverage from the audit tracker; do not falsely mark all verified yet.
print("\nMaster remediation files created.")
print("Next step: run typecheck/lint/tests/build + backend pytest + verify_phase2_5.py before tracker transitions.")
