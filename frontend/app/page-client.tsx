"use client";

import {
  Activity,
  Check,
  CheckCircle2,
  Circle,
  Copy,
  Loader2,
  Printer,
  Search,
  ShieldCheck,
  Sparkles,
  UserRound,
} from "lucide-react";
import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  runAgenticWorkflow,
  type AgenticRunResponse,
} from "@/lib/agentic";
import {
  clampScore,
  friendlyStatus,
} from "@/lib/config";
import {
  GoalSchema,
  normalizeCommaList,
} from "@/lib/validation";

const AGENTS = [
  ["supervisor", "Supervisor"],
  ["candidate", "Candidate"],
  ["resume", "Resume"],
  ["job", "Job"],
  ["strategy", "Strategy"],
  ["recommendation", "Recommendation"],
  ["validation", "Validation"],
] as const;

const DRAFT_KEY = "careerpilot.home.draft.v1";

interface HomeDraft {
  goal: string;
  role: string;
  skills: string;
  location: string;
  projects: string;
}

function loadInitialDraft(): HomeDraft {
  if (typeof window === "undefined") {
    return {
      goal: "Find AI Engineer opportunities and tell me what I should do next.",
      role: "AI Engineer",
      skills: "Python, FastAPI, SQL",
      location: "",
      projects: "",
    };
  }
  try {
    const raw = window.localStorage.getItem(DRAFT_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed === "object") {
        return {
          goal: typeof parsed.goal === "string" && parsed.goal ? parsed.goal : "Find AI Engineer opportunities and tell me what I should do next.",
          role: typeof parsed.role === "string" ? parsed.role : "AI Engineer",
          skills: typeof parsed.skills === "string" ? parsed.skills : "Python, FastAPI, SQL",
          location: typeof parsed.location === "string" ? parsed.location : "",
          projects: typeof parsed.projects === "string" ? parsed.projects : "",
        };
      }
    }
  } catch {}
  return {
    goal: "Find AI Engineer opportunities and tell me what I should do next.",
    role: "AI Engineer",
    skills: "Python, FastAPI, SQL",
    location: "",
    projects: "",
  };
}

function getAgentState(
  id: string,
  result: AgenticRunResponse | null,
) {
  if (!result) {
    return "idle";
  }

  if (result.current_agent === id) {
    return "active";
  }

  if (result.agents_used.includes(id)) {
    return "done";
  }

  return "idle";
}

function safeEvidencePreview(value: unknown) {
  const text = typeof value === "string" ? value.trim() : "";
  if (text.length <= 360) {
    return text;
  }
  return `${text.slice(0, 360).trim()}…`;
}

export default function HomeClient() {
  const [draftLoaded, setDraftLoaded] = useState(false);
  const [goal, setGoal] = useState("Find AI Engineer opportunities and tell me what I should do next.");
  const [role, setRole] = useState("AI Engineer");
  const [skills, setSkills] = useState("Python, FastAPI, SQL");
  const [location, setLocation] = useState("");
  const [projects, setProjects] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AgenticRunResponse | null>(null);

  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [copiedAll, setCopiedAll] = useState(false);

  const goalRef = useRef<HTMLTextAreaElement | null>(null);
  const resultsRef = useRef<HTMLDivElement | null>(null);
  const controllerRef = useRef<AbortController | null>(null);

  // Load draft on mount
  useEffect(() => {
    const handle = window.requestAnimationFrame(() => {
      const draft = loadInitialDraft();
      setGoal(draft.goal);
      setRole(draft.role);
      setSkills(draft.skills);
      setLocation(draft.location);
      setProjects(draft.projects);
      setDraftLoaded(true);
    });
    return () => window.cancelAnimationFrame(handle);
  }, []);

  // Save draft on edit
  useEffect(() => {
    if (!draftLoaded || typeof window === "undefined") return;
    try {
      window.localStorage.setItem(
        DRAFT_KEY,
        JSON.stringify({ goal, role, skills, location, projects }),
      );
    } catch {}
  }, [goal, role, skills, location, projects, draftLoaded]);

  const latestDelegation = useMemo(
    () =>
      result?.delegation_trace?.length
        ? result.delegation_trace[result.delegation_trace.length - 1]
        : null,
    [result],
  );

  useEffect(() => {
    if (!result) return;
    window.requestAnimationFrame(() =>
      resultsRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      }),
    );
  }, [result]);

  async function run() {
    if (typeof navigator !== "undefined" && navigator.onLine === false) {
      setError("You appear to be offline. Reconnect and try again.");
      return;
    }

    const goalResult = GoalSchema.safeParse(goal);
    if (!goalResult.success) {
      setError(goalResult.error.issues[0]?.message ?? "Please describe your career goal.");
      goalRef.current?.focus();
      return;
    }

    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;

    setLoading(true);
    setError(null);

    try {
      const traceId = crypto.randomUUID();
      const candidateSkills = normalizeCommaList(skills);
      const candidateProjects = normalizeCommaList(projects);

      const response = await runAgenticWorkflow(
        {
          request_id: traceId,
          thread_id: traceId,
          user_goal: goal.trim(),
          candidate_profile: {
            headline: role.trim(),
            skills: candidateSkills,
            technical_skills: candidateSkills,
            projects: candidateProjects,
            preferred_locations: location.trim() ? [location.trim()] : [],
            career_goal: {
              target_roles: role.trim() ? [role.trim()] : [],
            },
          },
          conversation_context: [],
        },
        controller.signal,
      );

      setResult(response);
      setError(null);
    } catch (caught) {
      if (caught instanceof DOMException && caught.name === "AbortError") {
        return;
      }

      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to run CareerPilot.",
      );
    } finally {
      setLoading(false);
      controllerRef.current = null;
    }
  }

  function resetWorkspace() {
    controllerRef.current?.abort();
    controllerRef.current = null;
    setResult(null);
    setError(null);
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(DRAFT_KEY);
    }
    const def = loadInitialDraft();
    setGoal(def.goal);
    setRole(def.role);
    setSkills(def.skills);
    setLocation(def.location);
    setProjects(def.projects);
    goalRef.current?.focus();
  }

  function copySingleRecommendation(id: string, text: string) {
    if (typeof window === "undefined") return;
    navigator.clipboard.writeText(text).then(() => {
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    });
  }

  function copyAllRecommendations() {
    if (!result?.recommendations?.length || typeof window === "undefined") return;
    const all = result.recommendations
      .map((r, i) => `${i + 1}. ${r.title}\nAction: ${r.action}\nRationale: ${r.rationale || "Direct alignment"}`)
      .join("\n\n");
    navigator.clipboard.writeText(all).then(() => {
      setCopiedAll(true);
      setTimeout(() => setCopiedAll(false), 2000);
    });
  }

  function handlePrint() {
    if (typeof window !== "undefined") {
      window.print();
    }
  }

  const status = friendlyStatus(result?.status, loading);

  return (
    <main id="main-content" className="min-h-screen bg-[#080a0f] p-5 text-white md:p-8">
      <div className="mx-auto max-w-7xl">
        <header className="border-b border-white/10 pb-7">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-white/60">
                <Sparkles size={14} />
                Autonomous Career OS
              </div>

              <h1 className="mt-3 text-4xl font-semibold tracking-tight">
                Your career,{" "}
                <br className="hidden sm:inline" />
                intelligently orchestrated.
              </h1>

              <p className="mt-3 max-w-2xl text-sm leading-6 text-white/70">
                Align goals, discover opportunities, analyze market fit, and execute resume optimizations through coordinated multi-agent intelligence.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <div className="inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/[0.025] px-4 py-3 text-xs text-white/70">
                <Activity size={14} className={loading ? "animate-spin text-cyan-400" : "text-emerald-400"} />
                {status}
              </div>
            </div>
          </div>
        </header>

        <form
          onSubmit={(event) => {
            event.preventDefault();
            void run();
          }}
          className="mt-6 grid gap-6 lg:grid-cols-3"
        >
          <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6 lg:col-span-2">
            <label htmlFor="user-goal" className="block text-xs uppercase tracking-[0.18em] text-white/60">
              Career Goal
            </label>

            <textarea
              id="user-goal"
              ref={goalRef}
              value={goal}
              maxLength={2000}
              onInput={(event) => {
                const target = event.currentTarget;
                target.style.height = "auto";
                target.style.height = `${Math.max(110, target.scrollHeight)}px`;
              }}
              onChange={(event) => {
                setGoal(event.target.value);
                if (error) setError(null);
              }}
              rows={4}
              placeholder="Describe what you want to achieve (e.g. Find senior backend roles, optimize my ATS score)..."
              className="mt-3 min-h-[110px] w-full resize-y rounded-2xl border border-white/10 bg-black/10 p-4 text-sm leading-6 text-white outline-none focus:border-white/30"
            />

            <div className="mt-1 flex justify-between text-xs text-white/50">
              <span>{goal.length}/2000 characters</span>
              {goal.length > 1800 && <span className="text-amber-300">Approaching character limit</span>}
            </div>

            <div className="mt-6 grid gap-4 md:grid-cols-2">
              <div>
                <label htmlFor="target-role" className="block text-xs text-white/60">
                  Target role
                </label>
                <input
                  id="target-role"
                  value={role}
                  onChange={(event) => {
                    setRole(event.target.value);
                    if (error) setError(null);
                  }}
                  className="mt-2 w-full rounded-xl border border-white/10 bg-black/10 px-3 py-2.5 text-sm outline-none focus:border-white/30"
                />
              </div>

              <div>
                <label htmlFor="target-skills" className="block text-xs text-white/60">
                  Skills
                </label>
                <input
                  id="target-skills"
                  value={skills}
                  onChange={(event) => {
                    setSkills(event.target.value);
                    if (error) setError(null);
                  }}
                  className="mt-2 w-full rounded-xl border border-white/10 bg-black/10 px-3 py-2.5 text-sm outline-none focus:border-white/30"
                />
              </div>

              <div>
                <label htmlFor="target-location" className="block text-xs text-white/60">
                  Location
                </label>
                <input
                  id="target-location"
                  value={location}
                  placeholder="e.g. Bangalore, Remote"
                  onChange={(event) => {
                    setLocation(event.target.value);
                    if (error) setError(null);
                  }}
                  className="mt-2 w-full rounded-xl border border-white/10 bg-black/10 px-3 py-2.5 text-sm outline-none focus:border-white/30"
                />
              </div>

              <div>
                <label htmlFor="target-projects" className="block text-xs text-white/60">
                  Projects
                </label>
                <input
                  id="target-projects"
                  value={projects}
                  placeholder="e.g. Portfolio app, E-commerce API"
                  onChange={(event) => {
                    setProjects(event.target.value);
                    if (error) setError(null);
                  }}
                  className="mt-2 w-full rounded-xl border border-white/10 bg-black/10 px-3 py-2.5 text-sm outline-none focus:border-white/30"
                />
              </div>
            </div>

            {error && (
              <div className="mt-5 rounded-2xl border border-red-400/15 bg-red-400/[0.04] p-4 text-sm text-red-100/90">
                {error}
              </div>
            )}

            <div className="mt-6 flex flex-wrap items-center gap-3">
              <button
                type="submit"
                disabled={loading}
                className="inline-flex items-center gap-2 rounded-xl bg-white px-5 py-2.5 text-xs font-semibold text-black transition hover:bg-white/90 disabled:opacity-50"
              >
                {loading ? <Loader2 size={15} className="animate-spin" /> : <Search size={15} />}
                {loading ? "Orchestrating agents..." : "Run CareerPilot"}
              </button>

              <button
                type="button"
                onClick={resetWorkspace}
                className="rounded-xl border border-white/10 px-4 py-2.5 text-xs text-white/70 transition hover:bg-white/5"
              >
                Reset Workspace
              </button>
            </div>
          </section>

          <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
            <div className="text-xs uppercase tracking-[0.18em] text-white/60">
              Workflow lifecycle
            </div>

            <div className="mt-5 space-y-2">
              {AGENTS.map(([id, label]) => {
                const state = getAgentState(id, result);

                return (
                  <div
                    key={`agent-${id}`}
                    className="flex items-center gap-3 rounded-2xl border border-white/8 bg-white/[0.02] px-3 py-2.5"
                  >
                    {state === "done" ? (
                      <CheckCircle2 size={15} className="text-emerald-400" />
                    ) : state === "active" ? (
                      <Loader2 size={15} className="animate-spin text-cyan-400" />
                    ) : (
                      <Circle size={15} className="text-white/40" />
                    )}

                    <span className="text-sm font-medium text-white/90">{label}</span>

                    <span className="ml-auto text-xs uppercase tracking-[0.14em] text-white/50">
                      {state}
                    </span>
                  </div>
                );
              })}
            </div>

            {latestDelegation && (
              <div className="mt-5 rounded-2xl border border-white/8 bg-white/[0.02] p-4 text-xs text-white/70">
                {latestDelegation.from_agent} {" → "} {latestDelegation.to_agent} {" • "} {latestDelegation.status}
              </div>
            )}
          </section>
        </form>

        <div ref={resultsRef} className="mt-8 grid gap-6 lg:grid-cols-2">
          <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
            <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-white/60">
              <ShieldCheck size={14} className="text-emerald-400" />
              Validation
            </div>

            <div className="mt-5">
              <div className="text-3xl font-semibold">
                {clampScore(
                  result?.final_validation && typeof result.final_validation === "object"
                    ? (result.final_validation as { valid?: boolean }).valid
                      ? 100
                      : 0
                    : 0,
                )}%
              </div>

              <div className="mt-1 text-xs text-white/50">
                Deterministic final-state policy validation
              </div>
            </div>
          </section>

          <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
            <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-white/60">
              <UserRound size={14} className="text-cyan-400" />
              Next action
            </div>

            <div className="mt-5 text-lg font-medium text-white/90">
              {result?.next_action?.action || "Run the workflow to generate a personalized next action."}
            </div>
          </section>
        </div>

        {result && (
          <section className="mt-6 rounded-3xl border border-white/10 bg-white/[0.025] p-6">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-4">
              <div className="text-xs uppercase tracking-[0.18em] text-white/60">
                Strategic Recommendations
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={copyAllRecommendations}
                  className="inline-flex items-center gap-1.5 rounded-xl border border-white/10 px-3 py-1.5 text-xs text-white/70 transition hover:bg-white/5"
                >
                  {copiedAll ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
                  {copiedAll ? "Copied all" : "Copy all"}
                </button>

                <button
                  type="button"
                  onClick={handlePrint}
                  className="inline-flex items-center gap-1.5 rounded-xl border border-white/10 px-3 py-1.5 text-xs text-white/70 transition hover:bg-white/5"
                >
                  <Printer size={13} />
                  Print / PDF
                </button>
              </div>
            </div>

            <div className="mt-5 space-y-3">
              {(result.recommendations ?? []).map((recommendation, index) => {
                const recId = recommendation.id || `recommendation-${index}`;
                const isCopied = copiedId === recId;

                return (
                  <div
                    key={recId}
                    className="flex items-start justify-between gap-4 rounded-2xl border border-white/8 bg-white/[0.02] p-4 transition hover:border-white/20"
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex h-6 min-w-[1.5rem] items-center justify-center rounded-lg border border-white/10 bg-white/[0.04] px-1 text-xs font-semibold text-white/60">
                        {index + 1}
                      </div>

                      <div>
                        <div className="font-medium text-white">{recommendation.title}</div>
                        <div className="mt-1 text-sm text-white/70">{recommendation.action}</div>
                        {recommendation.rationale && (
                          <div className="mt-2 text-xs italic text-white/50">{recommendation.rationale}</div>
                        )}
                      </div>
                    </div>

                    <button
                      type="button"
                      aria-label="Copy recommendation text"
                      onClick={() =>
                        copySingleRecommendation(
                          recId,
                          `${recommendation.title}: ${recommendation.action}`,
                        )
                      }
                      className="rounded-lg border border-white/10 p-2 text-white/50 transition hover:bg-white/10 hover:text-white"
                    >
                      {isCopied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
                    </button>
                  </div>
                );
              })}

              {result.recommendations?.length === 0 && (
                <div className="text-sm text-white/50">
                  No recommendations were returned.
                </div>
              )}
            </div>
          </section>
        )}

        {result?.career_knowledge_evidence?.length ? (
          <section className="mt-6 rounded-3xl border border-white/10 bg-white/[0.025] p-6">
            <div className="text-xs uppercase tracking-[0.18em] text-white/60">
              Retrieved Evidence & Intelligence
            </div>

            <div className="mt-4 space-y-3">
              {result.career_knowledge_evidence.map((item) => (
                <div
                  key={item.evidence_id}
                  className="rounded-2xl border border-white/8 p-4 transition hover:border-white/15"
                >
                  <div className="font-medium text-white/90">{item.title}</div>
                  <p className="mt-2 text-sm leading-6 text-white/70">
                    {safeEvidencePreview(item.text)}
                  </p>
                </div>
              ))}
            </div>
          </section>
        ) : null}

        {(result?.retry_count ?? 0) > 0 && (
          <div className="mt-4 text-xs text-white/50">
            Recovery retries: {result?.retry_count ?? 0}
          </div>
        )}

        {result && (result.tools_used ?? []).length > 0 && (
          <div className="mt-2 text-xs text-white/50">
            Tools utilized: {(result.tools_used ?? []).join(", ")}
          </div>
        )}
      </div>
    </main>
  );
}
