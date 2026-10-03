import type { JobResult } from "./api";
import { apiJson } from "./apiClient";

const STORAGE_KEY = "careerpilot.workspace.v2";

export type WorkspaceState = {
  jobs: JobResult[];
  applications: Array<{ id: string; job_id: string; company: string; title: string; status: string; updated_at: string }>;
  activity: Array<{ id: string; title: string; detail: string; timestamp: string }>;
};

const EMPTY: WorkspaceState = { jobs: [], applications: [], activity: [] };

function readCache(): WorkspaceState {
  if (typeof window === "undefined") return EMPTY;
  try {
    const parsed = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "null") as Partial<WorkspaceState> | null;
    return {
      jobs: Array.isArray(parsed?.jobs) ? parsed!.jobs : [],
      applications: Array.isArray(parsed?.applications) ? parsed!.applications : [],
      activity: Array.isArray(parsed?.activity) ? parsed!.activity : [],
    };
  } catch { return EMPTY; }
}

function persist(state: WorkspaceState) {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  window.dispatchEvent(new Event("careerpilot:workspace"));
}

export function getWorkspaceState(): WorkspaceState { return readCache(); }

export async function refreshWorkspace(): Promise<WorkspaceState> {
  try {
    const data = await apiJson<{
      saved_jobs?: Array<Record<string, unknown>>;
      applications?: Array<Record<string, unknown>>;
      activity?: Array<{ id?: string; summary?: string; created_at?: string }>;
    }>("/workspace/state");
    const jobs = (data.saved_jobs ?? []).map((item) => item as unknown as JobResult);
    const applications = (data.applications ?? []).map((item) => ({
      id: String(item.id ?? crypto.randomUUID()),
      job_id: String(item.job_id ?? item.id ?? ""),
      company: String(item.company ?? ""),
      title: String(item.title ?? ""),
      status: String(item.status ?? "Applied"),
      updated_at: String(item.updated_at ?? item.created_at ?? new Date().toISOString()),
    }));
    const activity = (data.activity ?? []).map((item) => ({
      id: String(item.id ?? crypto.randomUUID()),
      title: "CareerPilot activity",
      detail: String(item.summary ?? "Workspace updated."),
      timestamp: String(item.created_at ?? new Date().toISOString()),
    }));
    const state = { jobs, applications, activity };
    persist(state);
    return state;
  } catch {
    return readCache();
  }
}

export function saveSearchResults(jobs: JobResult[], sources: string[] = []) {
  const current = readCache();
  persist({
    ...current,
    jobs,
    activity: [{ id: crypto.randomUUID(), title: "Provider search completed", detail: `${jobs.length} canonical opportunities from ${sources.length} contributing sources.`, timestamp: new Date().toISOString() }, ...current.activity].slice(0, 20),
  });
  void apiJson("/workspace/market", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ payload: { query: jobs[0]?.title ? String(jobs[0].title) : "opportunity search", result_count: jobs.length, sources, created_at: new Date().toISOString() } }),
  }).catch(() => undefined);
}

export function recordApplication(job: JobResult) {
  const current = readCache();
  const id = `${job.source}:${job.source_job_id}`;
  if (!current.applications.some((item) => item.id === id)) {
    persist({
      ...current,
      applications: [{ id, job_id: id, company: job.company, title: job.title, status: "Applied", updated_at: new Date().toISOString() }, ...current.applications],
      activity: [{ id: crypto.randomUUID(), title: "Application tracked", detail: `${job.title} at ${job.company}`, timestamp: new Date().toISOString() }, ...current.activity].slice(0, 20),
    });
  }
  void apiJson("/workspace/applications", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id, payload: { id, job_id: id, company: job.company, title: job.title, status: "Applied", updated_at: new Date().toISOString(), job } }),
  }).catch(() => undefined);
}

export function updateApplicationStatus(id: string, status: string) {
  const current = readCache();
  persist({ ...current, applications: current.applications.map((item) => item.id === id ? { ...item, status, updated_at: new Date().toISOString() } : item) });
  void apiJson(`/workspace/applications`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id, payload: { ...current.applications.find((item) => item.id === id), status, updated_at: new Date().toISOString() } }),
  }).catch(() => undefined);
}
