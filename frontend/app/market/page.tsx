"use client";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { listWorkspace } from "@/lib/productWorkspace";

type Snapshot = Record<string, unknown>;
export default function MarketPage() {
  const [items, setItems] = useState<Snapshot[]>([]);
  useEffect(()=>{ listWorkspace("market").then(setItems).catch(()=>undefined); },[]);
  return <AppShell><main className="min-h-screen p-5 text-white md:p-8"><div className="mx-auto max-w-7xl"><header className="border-b border-white/10 pb-6"><p className="text-xs uppercase tracking-[0.2em] text-white/60">Market intelligence</p><h1 className="mt-2 text-4xl font-semibold">Market Intelligence</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-white/70">Review persisted market snapshots, live-source contribution counts and candidate-relative signals rather than fabricated benchmark statistics.</p></header><div className="mt-6 grid gap-4 md:grid-cols-3"><div className="rounded-3xl border border-white/10 p-5"><div className="text-xs uppercase tracking-widest text-white/50">Snapshots</div><div className="mt-2 text-3xl font-semibold">{items.length}</div></div><div className="rounded-3xl border border-white/10 p-5"><div className="text-xs uppercase tracking-widest text-white/50">Latest sources</div><div className="mt-2 text-sm text-white/70">{String(items[0]?.sources ?? "Run a live opportunity search to create one.")}</div></div><div className="rounded-3xl border border-white/10 p-5"><div className="text-xs uppercase tracking-widest text-white/50">Latest result count</div><div className="mt-2 text-3xl font-semibold">{String(items[0]?.result_count ?? 0)}</div></div></div><div className="mt-6 space-y-3">{items.map((item,i)=><article key={String(item.id ?? i)} className="rounded-2xl border border-white/10 p-4"><div className="text-sm font-medium">Snapshot {i+1}</div><pre className="mt-3 overflow-auto text-xs text-white/55">{JSON.stringify(item,null,2)}</pre></article>)}</div></div></main></AppShell>;
}
