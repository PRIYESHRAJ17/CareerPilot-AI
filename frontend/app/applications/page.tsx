"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { listWorkspace, saveWorkspace } from "@/lib/productWorkspace";

const STATUSES = ["Applied", "Screening", "Interview", "Offer", "Rejected"] as const;
type Application = Record<string, unknown> & { id?: string };

export default function ApplicationsPage() {
  const [items, setItems] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const grouped = useMemo(() => STATUSES.map((status) => ({ status, jobs: items.filter((a) => String(a.status) === status) })), [items]);
  useEffect(() => { listWorkspace("applications").then(setItems).catch(() => undefined).finally(() => setLoading(false)); }, []);
  async function move(item: Application, status: string) {
    const updated = await saveWorkspace("applications", { ...item, status, updated_at: new Date().toISOString() }, item.id);
    setItems((current) => current.map((entry) => entry.id === item.id ? updated : entry));
  }
  async function makePacket(item: Application) {
    const packet = await saveWorkspace("packets", {
      application_id: item.id,
      title: `${String(item.title)} — application packet`,
      resume_version: "latest",
      cover_letter_status: "draft",
      evidence_status: "requires-user-review",
      artifacts: [],
      created_at: new Date().toISOString(),
      human_submission_required: true,
    });
    alert(`Packet created: ${String(packet.id)}. External submission remains manual.`);
  }
  return (
    <AppShell>
      <main className="min-h-screen p-5 text-white md:p-8"><div className="mx-auto max-w-7xl">
        <header className="flex flex-wrap items-end justify-between gap-4 border-b border-white/10 pb-6"><div><p className="text-xs uppercase tracking-[0.2em] text-white/60">CareerPilot Workspace</p><h1 className="mt-2 text-4xl font-semibold">Applications CRM</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-white/70">Persistent application lifecycle, notes and packet generation. CareerPilot never silently submits an external application.</p></div><Link href="/opportunities" className="rounded-xl bg-white px-4 py-2.5 text-xs font-semibold text-black">Find opportunities</Link></header>
        {loading ? <p className="mt-8 text-sm text-white/50">Loading applications…</p> : <>
          <div className="mt-6 grid gap-4 md:grid-cols-5">{grouped.map(({status,jobs})=><div key={status} className="rounded-2xl border border-white/10 bg-white/[0.025] p-4"><div className="text-xs text-white/60">{status}</div><div className="mt-2 text-2xl font-semibold">{jobs.length}</div></div>)}</div>
          <div className="mt-6 grid gap-4 xl:grid-cols-5">{grouped.map(({status,jobs})=><section key={status} aria-labelledby={`status-${status}`} className="min-h-52 rounded-3xl border border-white/10 bg-white/[0.02] p-4"><h2 id={`status-${status}`} className="text-xs font-semibold uppercase tracking-[0.16em] text-white/60">{status}</h2><div className="mt-4 space-y-3">{jobs.length ? jobs.map((item)=><article key={String(item.id)} className="rounded-2xl border border-white/10 p-3"><div className="text-sm font-medium text-white/90">{String(item.title)}</div><div className="mt-1 text-xs text-white/60">{String(item.company)}</div><div className="mt-3 flex flex-wrap gap-2"><select aria-label={`Move ${String(item.title)}`} value={String(item.status)} onChange={(e)=>void move(item,e.target.value)} className="rounded-lg border border-white/10 bg-black/10 px-2 py-1.5 text-[11px]"><option value="Applied">Applied</option><option value="Screening">Screening</option><option value="Interview">Interview</option><option value="Offer">Offer</option><option value="Rejected">Rejected</option></select><button type="button" onClick={()=>void makePacket(item)} className="rounded-lg border border-cyan-400/20 px-2 py-1.5 text-[11px] text-cyan-200">Build packet</button></div></article>) : <p className="text-xs text-white/50">Nothing here yet.</p>}</div></section>)}</div>
        </>}
      </div></main>
    </AppShell>
  );
}
