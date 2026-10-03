"use client";

import { useEffect, useMemo, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { listWorkspace, saveWorkspace } from "@/lib/productWorkspace";

const QUESTION_BANK: Record<string, string[]> = {
  general: ["Tell me about yourself.", "Describe a project you are proud of.", "What would you improve in your current skill set?"],
  technical: ["Explain a production system you have built.", "How would you debug a slow API?", "What trade-offs matter when designing a service?"],
  behavioral: ["Tell me about a difficult disagreement and how you handled it.", "Describe a time you changed your approach after feedback.", "Tell me about a measurable outcome you drove."],
};

export default function InterviewsPage() {
  const [mode, setMode] = useState<keyof typeof QUESTION_BANK>("general");
  const [index, setIndex] = useState(0);
  const [answer, setAnswer] = useState("");
  const [reviewed, setReviewed] = useState(false);
  const [history, setHistory] = useState<Record<string, unknown>[]>([]);
  const question = useMemo(() => QUESTION_BANK[mode][index % QUESTION_BANK[mode].length], [index, mode]);
  useEffect(()=>{ listWorkspace("interviews").then(setHistory).catch(()=>undefined); },[]);
  async function review() {
    const words = answer.trim().split(/\s+/).filter(Boolean).length;
    const feedback = {
      question, mode, answer, word_count: words,
      score: words >= 60 ? 85 : words >= 30 ? 70 : 50,
      feedback: words >= 60 ? "Strong detail. Add a concrete metric or trade-off." : "Add situation, action and measurable result evidence.",
      reviewed_at: new Date().toISOString(),
    };
    const saved = await saveWorkspace("interviews", feedback);
    setHistory((items)=>[saved,...items]); setReviewed(true);
  }
  function next() { setAnswer(""); setReviewed(false); setIndex((i)=>i+1); }
  return <AppShell><main className="min-h-screen p-5 text-white md:p-8"><div className="mx-auto max-w-5xl"><header className="border-b border-white/10 pb-6"><p className="text-xs uppercase tracking-[0.2em] text-white/60">Adaptive interview engine</p><h1 className="mt-2 text-4xl font-semibold">Interviews</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-white/70">Role-aware practice with persistent answer history, adaptive question modes and measurable feedback.</p></header><div className="mt-6 flex flex-wrap gap-2">{(Object.keys(QUESTION_BANK) as Array<keyof typeof QUESTION_BANK>).map((item)=><button key={item} type="button" onClick={()=>{setMode(item);setIndex(0);setReviewed(false);}} className={`rounded-xl border px-3.5 py-2 text-xs capitalize ${mode===item?"border-cyan-400 bg-cyan-500/10 text-cyan-200":"border-white/10 text-white/65"}`}>{item}</button>)}<span className="rounded-xl border border-white/10 px-3.5 py-2 text-xs text-white/50">Reviews saved: {history.length}</span></div><section className="mt-6 rounded-3xl border border-white/10 bg-white/[0.025] p-7"><p className="text-xs uppercase tracking-[0.16em] text-white/60">Question {index+1}</p><h2 className="mt-3 text-2xl font-semibold">{question}</h2><textarea aria-label="Interview answer" value={answer} onChange={(e)=>setAnswer(e.target.value)} maxLength={3000} rows={8} className="mt-6 w-full rounded-2xl border border-white/10 bg-black/10 p-4 text-sm leading-6 outline-none focus:border-white/30" placeholder="Structure your answer around context, action, evidence and result…"/><div className="mt-4 flex flex-wrap justify-between gap-3"><button type="button" onClick={()=>void review()} className="rounded-xl bg-white px-5 py-2.5 text-xs font-semibold text-black">Review answer</button><button type="button" onClick={next} className="rounded-xl border border-white/10 px-4 py-2.5 text-xs">Next question</button></div>{reviewed && <div className="mt-5 rounded-2xl border border-emerald-500/20 bg-emerald-500/[0.04] p-4 text-sm text-emerald-200">Answer reviewed and saved to your interview history. Add a concrete metric, trade-off or result wherever possible.</div>}</section><section className="mt-6 rounded-3xl border border-white/10 bg-white/[0.025] p-6"><h2 className="font-semibold">Progress history</h2><div className="mt-4 space-y-3">{history.slice(0,8).map((item,i)=><div key={String(item.id ?? i)} className="rounded-2xl border border-white/8 p-4"><div className="flex justify-between text-xs"><span>{String(item.mode)}</span><span>{String(item.score)}/100</span></div><p className="mt-2 text-sm text-white/70">{String(item.feedback)}</p></div>)}</div></section></div></main></AppShell>;
}
