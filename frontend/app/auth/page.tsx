"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ShieldCheck, Sparkles } from "lucide-react";
import { apiJson } from "@/lib/apiClient";

export default function AuthPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    apiJson<{ authenticated: boolean }>("/session/me")
      .then((session) => { if (session.authenticated) router.replace("/dashboard"); })
      .catch(() => undefined);
  }, [router]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await apiJson(mode === "login" ? "/session/login" : "/session/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      router.replace("/dashboard");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#080a0f] px-5 py-12 text-white md:px-8">
      <div className="mx-auto grid max-w-6xl gap-12 lg:grid-cols-[1fr_430px] lg:items-center">
        <section>
          <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-white/60">
            <Sparkles size={14} className="text-cyan-400" /> CareerPilot AI
          </div>
          <h1 className="mt-5 max-w-3xl text-5xl font-semibold tracking-tight md:text-6xl">
            Your career operating system, tied to one persistent identity.
          </h1>
          <p className="mt-6 max-w-2xl text-base leading-7 text-white/65">
            Keep your Career Twin, opportunities, applications, interviews, plans,
            saved jobs, documents, networking, and alerts connected across sessions.
          </p>
          <div className="mt-8 flex items-center gap-3 text-sm text-white/60">
            <ShieldCheck size={18} className="text-emerald-400" />
            Session-isolated workspace with user-controlled final application submission.
          </div>
        </section>

        <section className="rounded-3xl border border-white/10 bg-white/[0.03] p-6 shadow-2xl backdrop-blur">
          <div className="flex rounded-2xl border border-white/10 p-1">
            {(["login", "signup"] as const).map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => { setMode(item); setError(""); }}
                className={`flex-1 rounded-xl px-3 py-2.5 text-xs font-semibold capitalize ${mode === item ? "bg-white text-black" : "text-white/60"}`}
              >
                {item}
              </button>
            ))}
          </div>

          <form onSubmit={submit} className="mt-6 space-y-4">
            <label className="block text-sm text-white/80">
              Email
              <input
                required type="email" autoComplete="email" value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-2 w-full rounded-xl border border-white/10 bg-black/20 px-3 py-3 outline-none focus:border-white/30"
              />
            </label>
            <label className="block text-sm text-white/80">
              Password
              <input
                required minLength={8} type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-2 w-full rounded-xl border border-white/10 bg-black/20 px-3 py-3 outline-none focus:border-white/30"
              />
            </label>
            {error && <div role="alert" className="rounded-xl border border-red-500/20 bg-red-500/5 p-3 text-sm text-red-200">{error}</div>}
            <button disabled={busy} className="w-full rounded-xl bg-white px-4 py-3 text-sm font-semibold text-black disabled:opacity-50">
              {busy ? "Working…" : mode === "login" ? "Log in" : "Create account"}
            </button>
          </form>
        </section>
      </div>
    </main>
  );
}
