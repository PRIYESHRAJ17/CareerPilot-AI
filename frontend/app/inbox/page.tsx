"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { apiJson } from "@/lib/apiClient";

type Item = Record<string, unknown> & { id?: string };

export default function CareerInboxPage() {
  const [items, setItems] = useState<Item[]>([]);
  const [message, setMessage] = useState("");

  useEffect(() => {
    let cancelled = false;
    apiJson<{ items?: Item[] }>("/inbox/items")
      .then((result) => {
        if (!cancelled) setItems(result.items ?? []);
      })
      .catch((error) => {
        if (!cancelled) setMessage(error instanceof Error ? error.message : "Unable to load inbox.");
      });
    return () => { cancelled = true; };
  }, []);

  async function sync() {
    try {
      const result = await apiJson<{ items?: Item[]; imported?: number; errors?: Record<string, string> }>("/inbox/sync", { method: "POST" });
      setItems(result.items ?? []);
      const errors = Object.entries(result.errors ?? {});
      setMessage(errors.length ? `Imported ${result.imported ?? 0}; provider errors: ${errors.map(([name, value]) => `${name}: ${value}`).join(" | ")}` : `Imported ${result.imported ?? 0} career messages.`);
    } catch (error) { setMessage(error instanceof Error ? error.message : "Inbox sync failed."); }
  }

  return <AppShell><main className="min-h-screen p-5 text-white md:p-8"><div className="mx-auto max-w-6xl"><header className="border-b border-white/10 pb-6"><p className="text-xs uppercase tracking-[0.2em] text-white/60">Career Inbox</p><h1 className="mt-2 text-4xl font-semibold">One place for career signals</h1><p className="mt-3 max-w-3xl text-sm leading-6 text-white/65">Import career-relevant mail from connected Google or Microsoft accounts. CareerPilot classifies only the metadata needed to route interviews, recruiter activity, applications, offers and rejections into your workspace.</p><button type="button" onClick={() => void sync()} className="mt-5 rounded-xl bg-white px-4 py-2.5 text-xs font-semibold text-black">Sync inbox</button>{message && <p className="mt-3 text-xs text-white/55">{message}</p>}</header><div className="mt-6 space-y-3">{items.length ? items.map((item) => <article key={String(item.id)} className="rounded-3xl border border-white/10 bg-white/[0.025] p-5"><div className="flex flex-wrap items-center justify-between gap-3"><div><span className="rounded-full border border-white/10 px-2.5 py-1 text-[10px] uppercase tracking-[0.16em] text-white/50">{String(item.kind ?? "career")}</span><h2 className="mt-2 text-base font-semibold">{String(item.subject ?? item.title ?? "Career message")}</h2><p className="mt-1 text-xs text-white/45">{String(item.from ?? item.source ?? "Unknown source")} · {String(item.date ?? "")}</p></div>{typeof item.web_link === "string" && item.web_link && <a href={item.web_link} target="_blank" rel="noreferrer" className="rounded-xl border border-white/10 px-3 py-2 text-xs">Open source</a>}</div>{typeof item.preview === "string" && item.preview.length > 0 && <p className="mt-3 text-sm leading-6 text-white/60">{item.preview}</p>}</article>) : <div className="rounded-3xl border border-dashed border-white/10 p-8 text-sm text-white/45">Nothing imported yet. Connect Google Workspace or Microsoft 365, then sync.</div>}</div></div></main></AppShell>;
}
