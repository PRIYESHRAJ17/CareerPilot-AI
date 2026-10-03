"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { API_BASE_URL } from "@/lib/config";
import { apiJson } from "@/lib/apiClient";

type Integration = {
  provider: string;
  display_name: string;
  description: string;
  configured: boolean;
  connected: boolean;
  updated_at?: string | null;
  scope?: string | null;
};

type Setup = {
  job_api_credentials?: Record<string, boolean>;
  token_encryption_configured?: boolean;
};

export default function IntegrationsPage() {
  const [items, setItems] = useState<Integration[]>([]);
  const [setup, setSetup] = useState<Setup>({});
  const [message, setMessage] = useState("");
  const [parentPageId, setParentPageId] = useState(() => typeof window === "undefined" ? "" : localStorage.getItem("careerpilot.notion.parentPageId") ?? "");
  const [clipToken, setClipToken] = useState("");
  const [syncing, setSyncing] = useState<string | null>(null);

  async function load() {
    try {
      const result = await apiJson<{ integrations: Integration[]; setup: Setup }>("/integrations/status");
      setItems(result.integrations ?? []);
      setSetup(result.setup ?? {});
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to load integrations.");
    }
  }

  useEffect(() => {
    void load();
    const params = new URLSearchParams(window.location.search);
    const connected = params.get("connected");
    const error = params.get("error");
    if (connected) setMessage(`${connected} connected successfully.`);
    if (error) setMessage(`Integration error: ${error}`);
  }, []);

  async function disconnect(provider: string) {
    await apiJson(`/integrations/${provider}`, { method: "DELETE" });
    await load();
  }

  async function sync(provider: string) {
    setSyncing(provider);
    try {
      if (provider === "google") await apiJson("/integrations/google/sync", { method: "POST" });
      if (provider === "microsoft") await apiJson("/integrations/microsoft/sync", { method: "POST" });
      if (provider === "github") await apiJson("/integrations/github/sync", { method: "POST" });
      if (provider === "gitlab") await apiJson("/integrations/gitlab/sync", { method: "POST" });
      if (provider === "google") await apiJson("/integrations/google/network", { method: "POST" });
      if (provider === "microsoft") await apiJson("/integrations/microsoft/network", { method: "POST" });
      setMessage(`${provider} data synchronized into CareerPilot.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Synchronization failed.");
    } finally {
      setSyncing(null);
    }
  }

  async function createClipToken() {
    try {
      const result = await apiJson<{ token: string }>("/integrations/clipper/token", { method: "POST" });
      setClipToken(result.token);
      setMessage("Browser clipper token created. It is shown only once.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to create clipper token.");
    }
  }

  async function saveNotionSettings() {
    localStorage.setItem("careerpilot.notion.parentPageId", parentPageId.trim());
    setMessage("Notion destination saved locally for this browser.");
  }

  return (
    <AppShell>
      <main className="min-h-screen p-5 text-white md:p-8">
        <div className="mx-auto max-w-6xl">
          <header className="border-b border-white/10 pb-6">
            <p className="text-xs uppercase tracking-[0.2em] text-white/60">Connected career workspace</p>
            <h1 className="mt-2 text-4xl font-semibold">Integrations</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-white/65">Connect your own workspaces and developer accounts. CareerPilot keeps tokens user-scoped and encrypted server-side; disconnected providers never block the core app.</p>
            {message && <p className="mt-4 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-white/75">{message}</p>}
          </header>

          <section className="mt-6 grid gap-4 lg:grid-cols-2">
            {items.map((item) => (
              <article key={item.provider} className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h2 className="text-lg font-semibold">{item.display_name}</h2>
                    <p className="mt-2 text-sm leading-6 text-white/60">{item.description}</p>
                  </div>
                  <span className={`rounded-full px-3 py-1 text-[11px] ${item.connected ? "bg-emerald-400/10 text-emerald-300" : "bg-white/5 text-white/50"}`}>{item.connected ? "Connected" : "Not connected"}</span>
                </div>
                {!item.configured && !item.connected && <p className="mt-4 text-xs text-amber-200/80">Server OAuth credentials are not configured yet.</p>}
                <div className="mt-5 flex flex-wrap gap-2">
                  {!item.connected && item.configured && <a href={`${API_BASE_URL}/integrations/connect/${item.provider}`} className="rounded-xl bg-white px-4 py-2.5 text-xs font-semibold text-black">Connect</a>}
                  {item.connected && ["google", "microsoft", "github", "gitlab"].includes(item.provider) && <button type="button" disabled={syncing === item.provider} onClick={() => void sync(item.provider)} className="rounded-xl bg-white px-4 py-2.5 text-xs font-semibold text-black disabled:opacity-40">{syncing === item.provider ? "Syncing…" : "Sync career data"}</button>}
                  {item.connected && <button type="button" onClick={() => void disconnect(item.provider)} className="rounded-xl border border-white/10 px-4 py-2.5 text-xs text-white/70">Disconnect</button>}
                </div>
                {item.scope && <p className="mt-4 text-[11px] text-white/35">Granted: {item.scope}</p>}
              </article>
            ))}
          </section>

          <section className="mt-6 grid gap-4 lg:grid-cols-2">
            <article className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
              <h2 className="text-lg font-semibold">Notion destination</h2>
              <p className="mt-2 text-sm text-white/60">Connect Notion, then enter the parent page where CareerPilot should create notes, jobs, research and career-plan pages.</p>
              <input value={parentPageId} onChange={(event) => setParentPageId(event.target.value)} placeholder="Notion parent page ID" className="mt-4 w-full rounded-xl border border-white/10 bg-black/20 px-3 py-3 text-sm outline-none" />
              <div className="mt-3 flex gap-2"><button type="button" onClick={() => void saveNotionSettings()} className="rounded-xl bg-white px-4 py-2.5 text-xs font-semibold text-black">Save destination</button><a href="https://www.notion.so/my-integrations" target="_blank" rel="noreferrer" className="rounded-xl border border-white/10 px-4 py-2.5 text-xs text-white/70">Notion setup</a></div>
            </article>

            <article className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
              <h2 className="text-lg font-semibold">Browser job clipper</h2>
              <p className="mt-2 text-sm text-white/60">Generate a one-time token for the bundled Chromium extension. It captures jobs from any public career page into Saved Jobs with the original URL.</p>
              <div className="mt-4 flex flex-wrap gap-2"><button type="button" onClick={() => void createClipToken()} className="rounded-xl bg-white px-4 py-2.5 text-xs font-semibold text-black">Generate clipper token</button>{clipToken && <code className="max-w-full overflow-auto rounded-xl bg-black/30 px-3 py-2.5 text-[11px] text-emerald-200">{clipToken}</code>}</div>
              <p className="mt-3 text-[11px] text-white/35">Encryption key configured: {setup.token_encryption_configured ? "yes" : "local key fallback"}.</p>
            </article>
          </section>
        </div>
      </main>
    </AppShell>
  );
}
