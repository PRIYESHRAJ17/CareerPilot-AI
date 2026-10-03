"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { apiJson } from "@/lib/apiClient";
import { listWorkspace, saveWorkspace } from "@/lib/productWorkspace";

type Settings = { workModes: string[]; alerts: boolean; locale: string; privacyMode: boolean };
const DEFAULT: Settings = { workModes: ["remote", "hybrid", "on-site"], alerts: true, locale: "en-IN", privacyMode: true };

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings>(DEFAULT);
  const [saved, setSaved] = useState(false);
  const [email, setEmail] = useState<string | null>(null);
  useEffect(() => {
    listWorkspace("settings").then((items) => { const root = items[0]; if (root?.settings && typeof root.settings === "object") setSettings({ ...DEFAULT, ...(root.settings as Partial<Settings>) }); }).catch(()=>undefined);
    apiJson<{email?:string|null}>("/session/me").then((session)=>setEmail(session.email ?? null)).catch(()=>undefined);
  }, []);
  function update<K extends keyof Settings>(key: K, value: Settings[K]) { setSettings((s)=>({ ...s, [key]: value })); setSaved(false); }
  async function save() { await saveWorkspace("settings", { key:"global", settings, updated_at:new Date().toISOString() }, "global"); window.localStorage.setItem("careerpilot.locale", settings.locale); setSaved(true); setTimeout(()=>setSaved(false), 3000); }
  function reset() { setSettings(DEFAULT); void saveWorkspace("settings", { key:"global", settings: DEFAULT, updated_at:new Date().toISOString() }, "global"); }
  return <AppShell><main className="min-h-screen p-5 text-white md:p-8"><div className="mx-auto max-w-5xl"><div className="border-b border-white/10 pb-6"><p className="text-xs uppercase tracking-[0.2em] text-white/60">CareerPilot Workspace</p><h1 className="mt-2 text-4xl font-semibold">Settings</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-white/70">Persist career preferences, privacy, locale and workspace behavior server-side under your account.</p>{email && <p className="mt-3 text-xs text-white/50">Signed in as {email}</p>}</div><div className="mt-6 space-y-5"><section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6"><h2 className="text-base font-semibold">Work modes</h2><div className="mt-4 flex flex-wrap gap-2.5">{["remote","hybrid","on-site"].map((mode)=><label key={mode} className="flex cursor-pointer items-center rounded-xl border border-white/10 px-3.5 py-2 text-xs capitalize text-white/80"><input type="checkbox" className="mr-2" checked={settings.workModes.includes(mode)} onChange={()=>update("workModes",settings.workModes.includes(mode)?settings.workModes.filter((x)=>x!==mode):[...settings.workModes,mode])}/>{mode}</label>)}</div></section><section className="space-y-4 rounded-3xl border border-white/10 bg-white/[0.025] p-6"><h2 className="text-base font-semibold">Preferences & Privacy</h2><label className="flex items-center justify-between border-b border-white/8 pb-3 text-sm"><span>Opportunity alerts</span><input type="checkbox" checked={settings.alerts} onChange={(e)=>update("alerts",e.target.checked)}/></label><label className="flex items-center justify-between border-b border-white/8 pb-3 text-sm"><span>Privacy mode</span><input type="checkbox" checked={settings.privacyMode} onChange={(e)=>update("privacyMode",e.target.checked)}/></label><label className="flex items-center justify-between text-sm"><span>Locale & currency</span><select value={settings.locale} onChange={(e)=>update("locale",e.target.value)} className="rounded-xl border border-white/10 bg-black/10 px-3 py-1.5 text-xs"><option value="en-IN">English (India)</option><option value="en-US">English (US)</option></select></label></section><div className="flex flex-wrap items-center gap-3"><button type="button" onClick={()=>void save()} className="rounded-xl bg-white px-5 py-2.5 text-xs font-semibold text-black">Save settings</button><button type="button" onClick={reset} className="rounded-xl border border-red-500/20 px-4 py-2.5 text-xs text-red-200">Reset</button>{saved && <span className="text-xs text-emerald-400">Saved.</span>}</div></div></div></main></AppShell>;
}
