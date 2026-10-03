"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { listWorkspace } from "@/lib/productWorkspace";

type Job = Record<string, unknown>;
export default function CompaniesPage() {
  const [query, setQuery] = useState("");
  const [jobs, setJobs] = useState<Job[]>([]);
  useEffect(()=>{ listWorkspace("saved-jobs").then(setJobs).catch(()=>undefined); },[]);
  const companies = useMemo(() => {
    const map = new Map<string,{company:string;roles:number;locations:string[];skills:string[]}>();
    jobs.forEach((job)=>{ const company=String(job.company??"Unknown company"); const item=map.get(company)??{company,roles:0,locations:[],skills:[]}; item.roles+=1; item.locations.push(...(Array.isArray(job.location)?job.location.map(String):[])); item.skills.push(...(Array.isArray(job.matched_skills)?job.matched_skills.map(String):[])); map.set(company,item); });
    return [...map.values()].map((item)=>({...item,locations:[...new Set(item.locations)].filter(Boolean),skills:[...new Set(item.skills)].slice(0,8)})).filter((item)=>item.company.toLowerCase().includes(query.trim().toLowerCase()));
  }, [jobs,query]);
  return <AppShell><main className="min-h-screen p-5 text-white md:p-8"><div className="mx-auto max-w-7xl"><div className="border-b border-white/10 pb-6"><p className="text-xs uppercase tracking-[0.2em] text-white/60">CareerPilot Intelligence</p><h1 className="mt-2 text-4xl font-semibold">Companies</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-white/70">Company intelligence is grounded in persisted opportunities: role presence, locations and observed skill signals.</p></div><div className="mt-6 flex gap-3"><input aria-label="Search companies" value={query} onChange={(e)=>setQuery(e.target.value)} placeholder="Search companies" className="w-full max-w-xl rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm outline-none"/><Link href="/opportunities" className="rounded-xl border border-white/10 px-4 py-3 text-xs">Search jobs</Link></div><div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">{companies.length ? companies.map((company)=><article key={company.company} className="rounded-3xl border border-white/10 bg-white/[0.025] p-6"><h2 className="text-lg font-semibold">{company.company}</h2><p className="mt-2 text-xs text-white/60">{company.roles} persisted roles</p><p className="mt-3 text-xs text-white/60">{company.locations.join(" · ")||"Location not specified"}</p>{company.skills.length>0&&<div className="mt-4 flex flex-wrap gap-1.5">{company.skills.map((skill)=><span key={skill} className="rounded-full border border-white/10 px-2 py-1 text-[10px] text-white/55">{skill}</span>)}</div>}</article>):<div className="rounded-3xl border border-dashed border-white/10 p-8 text-sm text-white/50 md:col-span-2 xl:col-span-3">Save opportunities to populate company intelligence.</div>}</div></div></main></AppShell>;
}
