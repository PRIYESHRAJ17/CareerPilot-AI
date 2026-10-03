"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { apiJson } from "@/lib/apiClient";
import { saveWorkspace, listWorkspace } from "@/lib/productWorkspace";

interface Recommendation { id: string; skill: string; provider: string; url: string; category: string; provider_url: string; }

export default function LearningPage() {
  const [skills, setSkills] = useState("python, system design, cloud, docker");
  const [items, setItems] = useState<Recommendation[]>([]);
  const [progress, setProgress] = useState<Record<string, unknown>[]>([]);
  const [message, setMessage] = useState("");

  async function load() {
    const saved = await listWorkspace("learning").catch(() => []);
    setProgress(saved);
    await recommend();
  }

  async function recommend() {
    try {
      const result = await apiJson<{ recommendations?: Recommendation[] }>(`/learning/recommendations?skills=${encodeURIComponent(skills)}`);
      setItems(result.recommendations ?? []);
    } catch (error) { setMessage(error instanceof Error ? error.message : "Unable to load learning recommendations."); }
  }

  useEffect(() => { void load(); }, []); // intentionally once on page load

  async function markStarted(item: Recommendation) {
    await saveWorkspace("learning", { id: item.id, skill: item.skill, provider: item.provider, url: item.url, status: "in_progress", updated_at: new Date().toISOString() }, item.id);
    setProgress((current) => [{ id: item.id, skill: item.skill, provider: item.provider, status: "in_progress" }, ...current.filter((entry) => entry.id !== item.id)]);
    setMessage(`${item.skill} marked in progress.`);
  }

  return <AppShell><main className="min-h-screen p-5 text-white md:p-8"><div className="mx-auto max-w-6xl"><header className="border-b border-white/10 pb-6"><p className="text-xs uppercase tracking-[0.2em] text-white/60">Career gap → learning</p><h1 className="mt-2 text-4xl font-semibold">Learning Hub</h1><p className="mt-3 max-w-3xl text-sm leading-6 text-white/65">Turn Career Twin gaps into concrete learning actions without pretending every course provider has a private API. Official training portals remain first-class destinations and progress is stored in your CareerPilot workspace.</p><div className="mt-5 flex gap-2"><input value={skills} onChange={(event) => setSkills(event.target.value)} className="min-w-0 flex-1 rounded-xl border border-white/10 bg-black/20 px-3 py-3 text-sm" placeholder="Comma-separated skills" /><button type="button" onClick={() => void recommend()} className="rounded-xl bg-white px-4 py-2.5 text-xs font-semibold text-black">Find learning</button></div>{message && <p className="mt-3 text-xs text-white/55">{message}</p>}</header><section className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{items.map((item) => <article key={item.id} className="rounded-3xl border border-white/10 bg-white/[0.025] p-5"><p className="text-xs uppercase tracking-[0.12em] text-white/40">{item.provider}</p><h2 className="mt-2 text-base font-semibold">{item.skill}</h2><p className="mt-2 text-xs text-white/45">{item.category}</p><div className="mt-5 flex gap-2"><a href={item.url} target="_blank" rel="noreferrer" className="rounded-xl bg-white px-3 py-2 text-xs font-semibold text-black">Open learning</a><button type="button" onClick={() => void markStarted(item)} className="rounded-xl border border-white/10 px-3 py-2 text-xs text-white/70">Track</button></div></article>)}</section><section className="mt-6 rounded-3xl border border-white/10 bg-white/[0.025] p-5"><h2 className="text-base font-semibold">Your learning progress</h2><div className="mt-4 grid gap-2 md:grid-cols-2">{progress.map((item) => <div key={String(item.id)} className="rounded-2xl border border-white/8 p-3 text-xs"><span className="font-medium">{String(item.skill ?? "Skill")}</span><span className="mx-2 text-white/30">·</span><span className="text-white/50">{String(item.provider ?? "Provider")}</span><span className="ml-2 text-emerald-300">{String(item.status ?? "tracked")}</span></div>)}</div></section></div></main></AppShell>;
}
