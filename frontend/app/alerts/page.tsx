"use client";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { listWorkspace, saveWorkspace } from "@/lib/productWorkspace";

type AlertItem = Record<string, unknown> & { id?: string };
export default function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [query, setQuery] = useState("AI engineering");
  const [frequency, setFrequency] = useState("daily");
  useEffect(() => { listWorkspace("alerts").then(setAlerts).catch(() => undefined); }, []);
  async function add() { const item = await saveWorkspace("alerts", { query, frequency, enabled: true, created_at: new Date().toISOString() }); setAlerts((current)=>[item,...current]); }
  return <AppShell><main className="min-h-screen p-5 text-white md:p-8"><div className="mx-auto max-w-6xl"><header className="border-b border-white/10 pb-6"><p className="text-xs uppercase tracking-[0.2em] text-white/60">Automation layer</p><h1 className="mt-2 text-4xl font-semibold">Alerts & Automation</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-white/70">Persist saved-search alerts, opportunity reminders and follow-up rules. Delivery wiring stays explicit and auditable.</p></header><div className="mt-6 flex flex-wrap gap-3"><input value={query} onChange={(e)=>setQuery(e.target.value)} className="min-w-[240px] flex-1 rounded-xl border border-white/10 bg-black/10 px-3 py-3 text-sm"/><select value={frequency} onChange={(e)=>setFrequency(e.target.value)} className="rounded-xl border border-white/10 bg-black/10 px-3 py-3 text-sm"><option>hourly</option><option>daily</option><option>weekly</option></select><button type="button" onClick={()=>void add()} className="rounded-xl bg-white px-4 py-3 text-xs font-semibold text-black">Save alert</button></div><div className="mt-6 space-y-3">{alerts.length ? alerts.map((item)=><article key={String(item.id)} className="rounded-2xl border border-white/10 bg-white/[0.025] p-4"><div className="flex justify-between"><span className="font-medium">{String(item.query)}</span><span className="text-xs text-white/50">{String(item.frequency)}</span></div></article>):<p className="text-sm text-white/50">No alerts configured.</p>}</div></div></main></AppShell>;
}
