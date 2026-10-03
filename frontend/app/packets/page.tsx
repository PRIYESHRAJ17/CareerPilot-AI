"use client";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { listWorkspace } from "@/lib/productWorkspace";

type Packet = Record<string, unknown> & { id?: string };
export default function PacketsPage(){
 const [items,setItems]=useState<Packet[]>([]);
 useEffect(()=>{listWorkspace("packets").then(setItems).catch(()=>undefined)},[]);
 return <AppShell><main className="min-h-screen p-5 text-white md:p-8"><div className="mx-auto max-w-6xl"><header className="border-b border-white/10 pb-6"><p className="text-xs uppercase tracking-[0.2em] text-white/60">Application intelligence</p><h1 className="mt-2 text-4xl font-semibold">Application Packets</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-white/70">Versioned application artifacts, evidence safeguards and explicit human review before any external submission.</p></header><div className="mt-6 space-y-3">{items.length?items.map((item)=><article key={String(item.id)} className="rounded-3xl border border-white/10 p-5"><div className="flex flex-wrap items-center justify-between gap-3"><div className="font-semibold">{String(item.title)}</div><span className="rounded-full border border-white/10 px-2.5 py-1 text-[10px] text-cyan-200">Human submission required</span></div><div className="mt-3 grid gap-2 text-xs text-white/55 md:grid-cols-3"><span>Resume: {String(item.resume_version)}</span><span>Cover letter: {String(item.cover_letter_status)}</span><span>Evidence: {String(item.evidence_status)}</span></div></article>):<p className="text-sm text-white/50">No packets yet. Create one from an application.</p>}</div></div></main></AppShell>;
}
