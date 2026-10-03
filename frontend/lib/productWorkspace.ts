import { apiJson } from "./apiClient";

export type WorkspaceItem = Record<string, unknown> & { id?: string };

export async function listWorkspace(entity: string): Promise<WorkspaceItem[]> {
  const result = await apiJson<{ items?: WorkspaceItem[] }>(`/workspace/${entity}`);
  return Array.isArray(result.items) ? result.items : [];
}

export async function saveWorkspace(entity: string, payload: WorkspaceItem, id?: string) {
  return apiJson<WorkspaceItem>(`/workspace/${entity}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id, payload }),
  });
}

export async function deleteWorkspace(entity: string, id: string) {
  return apiJson<{ deleted: boolean }>(`/workspace/${entity}/${encodeURIComponent(id)}`, { method: "DELETE" });
}

export async function recordWorkspaceEvent(event_type: string, summary: string, payload: WorkspaceItem = {}) {
  return apiJson(`/workspace/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ event_type, summary, payload }),
  });
}

export async function clipExternalJob(payload: { url: string; title?: string; company?: string; notes?: string }) {
  return apiJson<WorkspaceItem>("/workspace/browser-clip", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}
