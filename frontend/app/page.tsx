"use client";

import {
  Activity,
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  Circle,
  Loader2,
  Search,
  ShieldCheck,
  Sparkles,
  Target,
  UserRound,
  XCircle,
} from "lucide-react";

import {
  runAgenticWorkflow,
  type AgenticRunResponse,
  type DelegationTrace,
  type KnowledgeEvidence,
} from "../lib/agentic";

import { useMemo, useState } from "react";


const AGENTS = [
  {
    id: "supervisor",
    label: "Supervisor",
    description: "Plans and orchestrates the workflow.",
  },
  {
    id: "candidate",
    label: "Candidate",
    description: "Builds candidate intelligence.",
  },
  {
    id: "resume",
    label: "Resume",
    description: "Analyzes resume evidence.",
  },
  {
    id: "job",
    label: "Job",
    description: "Understands opportunities and requirements.",
  },
  {
    id: "strategy",
    label: "Strategy",
    description: "Builds career direction.",
  },
  {
    id: "recommendation",
    label: "Recommendation",
    description: "Synthesizes personalized actions.",
  },
  {
    id: "validation",
    label: "Validation",
    description: "Verifies the final workflow output.",
  },
];


function agentLabel(value?: string | null): string {
  if (!value) {
    return "Unknown";
  }

  return value.charAt(0).toUpperCase() + value.slice(1);
}


function getAgentState(
  agent: string,
  result: AgenticRunResponse | null,
): "done" | "active" | "idle" {
  if (!result) {
    return "idle";
  }

  if (
    result.agents_used.includes(agent)
  ) {
    if (
      result.status === "COMPLETED" ||
      result.status === "FAILED"
    ) {
      return "done";
    }

    return "active";
  }

  if (
    result.current_agent === agent
  ) {
    return "active";
  }

  return "idle";
}


function getLatestDelegation(
  traces: DelegationTrace[],
): DelegationTrace | null {
  if (!traces.length) {
    return null;
  }

  return traces[traces.length - 1];
}


function getRecommendationTitle(
  recommendation: Record<string, unknown>,
): string {
  const title = recommendation.title;

  return typeof title === "string"
    ? title
    : "Career action";
}


function getRecommendationAction(
  recommendation: Record<string, unknown>,
): string {
  const action = recommendation.action;

  return typeof action === "string"
    ? action
    : "Review this recommendation.";
}


function getEvidencePreview(
  evidence: KnowledgeEvidence,
): string {
  const text = evidence.text.trim();

  if (text.length <= 360) {
    return text;
  }

  return `${text.slice(0, 360).trim()}…`;
}


export default function Home() {
  const [
    userGoal,
    setUserGoal,
  ] = useState(
    "Find AI Engineer opportunities and tell me what I should do next.",
  );

  const [
    role,
    setRole,
  ] = useState("AI Engineer");

  const [
    skills,
    setSkills,
  ] = useState(
    "Python, FastAPI, SQL",
  );

  const [
    location,
    setLocation,
  ] = useState("Bengaluru");

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState<string | null>(null);

  const [
    result,
    setResult,
  ] = useState<AgenticRunResponse | null>(null);


  const latestDelegation = useMemo(
    () =>
      getLatestDelegation(
        result?.delegation_trace ?? [],
      ),
    [
      result?.delegation_trace,
    ],
  );


  const runCareerPilot = async () => {
    setLoading(true);
    setError(null);

    try {
      const candidateSkills = skills
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean);

      const requestId =
        `frontend-${Date.now()}`;

      const response =
        await runAgenticWorkflow({
          request_id: requestId,

          thread_id:
            `frontend-thread-${Date.now()}`,

          user_goal: userGoal,

          candidate_profile: {
            candidate_id: requestId,

            headline: role,

            skills: candidateSkills,

            technical_skills:
              candidateSkills,

            projects: [
              "CareerPilot",
            ],

            preferred_locations: [
              location,
            ],

            career_goal: {
              target_roles: [
                role,
              ],
            },
          },

          conversation_context: [],
        });

      setResult(response);
    } catch (runError) {
      setError(
        runError instanceof Error
          ? runError.message
          : "Unable to run CareerPilot.",
      );
    } finally {
      setLoading(false);
    }
  };


  return (
    <main className="min-h-screen bg-[#080a0f] text-white">
      <div className="mx-auto max-w-[1500px] px-5 py-6 md:px-8 md:py-8">

        {/* HEADER */}

        <header className="flex flex-col gap-5 border-b border-white/8 pb-7 md:flex-row md:items-end md:justify-between">

          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[10px] uppercase tracking-[0.18em] text-white/55">
              <Sparkles size={12} />
              CareerPilot Agentic OS
            </div>

            <h1 className="mt-4 text-4xl font-semibold tracking-[-0.04em] md:text-6xl">
              Your career,
              <br />
              <span className="text-white/40">
                intelligently orchestrated.
              </span>
            </h1>

            <p className="mt-4 max-w-2xl text-sm leading-6 text-white/45 md:text-base">
              CareerPilot coordinates specialist agents,
              deterministic intelligence and validation to
              turn your career goal into an actionable plan.
            </p>
          </div>


          <div className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3">
            <div className="flex items-center gap-2">
              <Activity
                size={15}
                className={
                  result?.status === "COMPLETED"
                    ? "text-white"
                    : "text-white/35"
                }
              />

              <span className="text-xs font-medium">
                {result
                  ? result.status
                  : "READY"}
              </span>
            </div>

            <div className="mt-1 text-[10px] uppercase tracking-[0.16em] text-white/30">
              Agentic workflow
            </div>
          </div>

        </header>


        {/* INPUT AREA */}

        <section className="mt-6 overflow-hidden rounded-[28px] border border-white/10 bg-[radial-gradient(circle_at_top_right,rgba(255,255,255,0.10),transparent_35%),linear-gradient(135deg,#11151d,#0b0d12)] p-6 md:p-8">

          <div className="grid gap-5 lg:grid-cols-[1.4fr_1fr]">

            <div>
              <div className="text-[10px] uppercase tracking-[0.18em] text-white/30">
                What should CareerPilot do?
              </div>

              <textarea
                value={userGoal}
                onChange={(event) =>
                  setUserGoal(
                    event.target.value,
                  )
                }
                rows={4}
                className="mt-3 w-full resize-none rounded-2xl border border-white/10 bg-black/20 p-4 text-sm leading-6 text-white outline-none transition placeholder:text-white/25 focus:border-white/20"
                placeholder="Tell CareerPilot what you want to accomplish..."
              />
            </div>


            <div className="grid gap-3">

              <div>
                <label className="text-[10px] uppercase tracking-[0.16em] text-white/30">
                  Target role
                </label>

                <input
                  value={role}
                  onChange={(event) =>
                    setRole(
                      event.target.value,
                    )
                  }
                  className="mt-2 w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none focus:border-white/20"
                />
              </div>


              <div>
                <label className="text-[10px] uppercase tracking-[0.16em] text-white/30">
                  Skills
                </label>

                <input
                  value={skills}
                  onChange={(event) =>
                    setSkills(
                      event.target.value,
                    )
                  }
                  className="mt-2 w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none focus:border-white/20"
                />
              </div>


              <div>
                <label className="text-[10px] uppercase tracking-[0.16em] text-white/30">
                  Location
                </label>

                <input
                  value={location}
                  onChange={(event) =>
                    setLocation(
                      event.target.value,
                    )
                  }
                  className="mt-2 w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none focus:border-white/20"
                />
              </div>

            </div>

          </div>


          <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">

            <div className="flex items-center gap-2 text-xs text-white/35">
              <ShieldCheck size={15} />
              Deterministic validation remains active.
            </div>

            <button
              onClick={runCareerPilot}
              disabled={
                loading ||
                !userGoal.trim()
              }
              className="inline-flex items-center justify-center gap-2 rounded-2xl bg-white px-6 py-3.5 text-sm font-semibold text-black transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {loading ? (
                <>
                  <Loader2
                    size={16}
                    className="animate-spin"
                  />
                  CareerPilot is thinking...
                </>
              ) : (
                <>
                  <Search size={16} />
                  Run CareerPilot
                  <ArrowRight size={16} />
                </>
              )}
            </button>

          </div>

        </section>


        {/* ERROR */}

        {error && (
          <section className="mt-5 rounded-2xl border border-red-400/20 bg-red-400/5 p-4">
            <div className="flex items-start gap-3">
              <XCircle
                size={18}
                className="mt-0.5 shrink-0 text-red-300"
              />

              <div>
                <div className="text-sm font-medium text-red-200">
                  Workflow failed
                </div>

                <div className="mt-1 text-xs leading-5 text-red-200/60">
                  {error}
                </div>
              </div>
            </div>
          </section>
        )}


        {/* EMPTY STATE */}

        {!result && !loading && (
          <section className="mt-6 grid gap-4 md:grid-cols-3">

            {[
              {
                icon: UserRound,
                title: "Understand me",
                text: "Candidate intelligence builds a structured view of your skills and readiness.",
              },
              {
                icon: BrainCircuit,
                title: "Reason about my career",
                text: "Specialists combine your profile, goals and opportunity signals.",
              },
              {
                icon: ShieldCheck,
                title: "Verify the answer",
                text: "Validation checks the resulting workflow before it reaches you.",
              },
            ].map((item) => {
              const Icon = item.icon;

              return (
                <div
                  key={item.title}
                  className="rounded-3xl border border-white/8 bg-white/[0.025] p-6"
                >
                  <Icon
                    size={20}
                    className="text-white/60"
                  />

                  <h2 className="mt-5 text-lg font-semibold">
                    {item.title}
                  </h2>

                  <p className="mt-2 text-sm leading-6 text-white/35">
                    {item.text}
                  </p>
                </div>
              );
            })}

          </section>
        )}


        {/* LOADING */}

        {loading && (
          <section className="mt-6 rounded-3xl border border-white/10 bg-white/[0.025] p-7">

            <div className="flex items-center gap-3">
              <Loader2
                size={18}
                className="animate-spin"
              />

              <div>
                <div className="text-sm font-medium">
                  CareerPilot is orchestrating specialists
                </div>

                <div className="mt-1 text-xs text-white/35">
                  Planning, analyzing, strategizing and validating...
                </div>
              </div>
            </div>

            <div className="mt-6 grid gap-2 md:grid-cols-7">

              {AGENTS.map((agent) => (
                <div
                  key={agent.id}
                  className="rounded-2xl border border-white/8 bg-black/15 p-3"
                >
                  <div className="flex items-center gap-2">
                    <Circle
                      size={10}
                      className="text-white/30"
                    />

                    <span className="text-[10px] font-medium text-white/60">
                      {agent.label}
                    </span>
                  </div>
                </div>
              ))}

            </div>

          </section>
        )}


        {/* RESULTS */}

        {result && (
          <div className="mt-6 grid gap-4 xl:grid-cols-[1.35fr_0.65fr]">

            {/* MAIN */}

            <div className="space-y-4">

              {/* WORKFLOW */}

              <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">

                <div className="flex flex-col justify-between gap-4 md:flex-row md:items-start">

                  <div>
                    <div className="text-[10px] uppercase tracking-[0.18em] text-white/30">
                      Agent orchestration
                    </div>

                    <h2 className="mt-2 text-2xl font-semibold">
                      Workflow trace
                    </h2>

                    <p className="mt-2 text-sm text-white/35">
                      {latestDelegation
                        ? `Last delegation: ${agentLabel(latestDelegation.from_agent)} → ${agentLabel(latestDelegation.to_agent)}`
                        : "Workflow completed without delegation trace."}
                    </p>
                  </div>


                  <div className="rounded-xl border border-white/10 px-3 py-2 text-xs text-white/50">
                    {result.agents_used.length} agents used
                  </div>

                </div>


                <div className="mt-6 grid gap-2 md:grid-cols-7">

                  {AGENTS.map((agent) => {

                    const state =
                      getAgentState(
                        agent.id,
                        result,
                      );

                    return (
                      <div
                        key={agent.id}
                        className={`rounded-2xl border p-3 transition ${
                          state === "done"
                            ? "border-white/15 bg-white/[0.06]"
                            : state === "active"
                              ? "border-white/20 bg-white/[0.10]"
                              : "border-white/8 bg-black/10"
                        }`}
                      >

                        <div className="flex items-center gap-2">

                          {state === "done" ? (
                            <CheckCircle2
                              size={14}
                              className="text-white"
                            />
                          ) : state === "active" ? (
                            <Loader2
                              size={14}
                              className="animate-spin text-white"
                            />
                          ) : (
                            <Circle
                              size={14}
                              className="text-white/25"
                            />
                          )}

                          <span className="text-[10px] font-medium text-white/65">
                            {agent.label}
                          </span>

                        </div>

                        <div className="mt-2 text-[9px] leading-4 text-white/25">
                          {agent.description}
                        </div>

                      </div>
                    );
                  })}

                </div>


                <div className="mt-6 space-y-2">

                  {result.delegation_trace.map(
                    (trace, index) => (
                      <div
                        key={`${trace.from_agent}-${trace.to_agent}-${index}`}
                        className="flex items-center gap-3 rounded-xl border border-white/6 bg-black/10 px-4 py-3"
                      >

                        <div className="text-xs font-medium text-white/65">
                          {agentLabel(
                            trace.from_agent,
                          )}
                        </div>

                        <ArrowRight
                          size={14}
                          className="text-white/25"
                        />

                        <div className="text-xs text-white/50">
                          {agentLabel(
                            trace.to_agent,
                          )}
                        </div>

                        <span className="ml-auto text-[9px] uppercase tracking-wider text-white/25">
                          {trace.status}
                        </span>

                      </div>
                    ),
                  )}

                </div>

              </section>


              {/* CAREER KNOWLEDGE EVIDENCE */}

              <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">

                <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
                  <div>
                    <div className="text-[10px] uppercase tracking-[0.18em] text-white/30">
                      Career knowledge
                    </div>

                    <h2 className="mt-2 text-2xl font-semibold">
                      Evidence behind the reasoning
                    </h2>

                    <p className="mt-2 text-sm leading-6 text-white/35">
                      Retrieved from CareerPilot's career-intelligence knowledge base and passed into the workflow as supporting evidence.
                    </p>
                  </div>

                  <div className="rounded-xl border border-white/10 px-3 py-2 text-xs text-white/50">
                    {result.career_knowledge_evidence?.length ?? 0} sources used
                  </div>
                </div>

                <div className="mt-5 space-y-3">
                  {result.career_knowledge_evidence?.length ? (
                    result.career_knowledge_evidence.map((evidence) => (
                      <article
                        key={evidence.evidence_id}
                        className="rounded-2xl border border-white/8 bg-black/10 p-5"
                      >
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-[9px] uppercase tracking-[0.14em] text-white/45">
                            {evidence.publisher}
                          </span>

                          <span className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-[9px] uppercase tracking-[0.14em] text-white/35">
                            {evidence.source_id}
                          </span>

                          <span className="ml-auto text-[10px] text-white/30">
                            relevance {evidence.relevance.toFixed(3)}
                          </span>
                        </div>

                        <h3 className="mt-3 font-medium">
                          {evidence.title}
                        </h3>

                        <p className="mt-2 text-sm leading-6 text-white/45">
                          {getEvidencePreview(evidence)}
                        </p>

                        <a
                          href={evidence.url}
                          target="_blank"
                          rel="noreferrer"
                          className="mt-3 inline-block text-xs text-white/40 underline decoration-white/15 underline-offset-4 transition hover:text-white/70"
                        >
                          View source ↗
                        </a>
                      </article>
                    ))
                  ) : (
                    <div className="rounded-2xl border border-white/8 p-5 text-sm text-white/35">
                      No external career knowledge evidence was retrieved for this run.
                    </div>
                  )}
                </div>

              </section>


              {/* RECOMMENDATIONS */}

              <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">

                <div className="text-[10px] uppercase tracking-[0.18em] text-white/30">
                  Personalized output
                </div>

                <h2 className="mt-2 text-2xl font-semibold">
                  What CareerPilot recommends
                </h2>


                <div className="mt-5 space-y-3">

                  {result.recommendations.length ? (
                    result.recommendations.map(
                      (recommendation, index) => (
                        <article
                          key={index}
                          className="rounded-2xl border border-white/8 bg-black/10 p-5"
                        >

                          <div className="flex items-start gap-4">

                            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white text-black">
                              {index + 1}
                            </div>

                            <div className="min-w-0">
                              <h3 className="font-medium">
                                {getRecommendationTitle(
                                  recommendation,
                                )}
                              </h3>

                              <p className="mt-1 text-sm leading-6 text-white/45">
                                {getRecommendationAction(
                                  recommendation,
                                )}
                              </p>

                              {typeof recommendation.reason ===
                                "string" &&
                                recommendation.reason && (
                                  <p className="mt-3 text-xs leading-5 text-white/30">
                                    {recommendation.reason}
                                  </p>
                                )}

                            </div>

                          </div>

                        </article>
                      ),
                    )
                  ) : (
                    <div className="rounded-2xl border border-white/8 p-5 text-sm text-white/35">
                      No recommendations returned.
                    </div>
                  )}

                </div>

              </section>

            </div>


            {/* SIDEBAR */}

            <aside className="space-y-4">

              {/* VALIDATION */}

              <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">

                <div className="flex items-center gap-2">
                  <ShieldCheck
                    size={17}
                  />

                  <span className="text-[10px] uppercase tracking-[0.18em] text-white/35">
                    Trust layer
                  </span>
                </div>

                <div className="mt-4">

                  {result.final_validation?.valid ? (
                    <div className="flex items-center gap-3">
                      <CheckCircle2
                        size={24}
                        className="text-white"
                      />

                      <div>
                        <div className="text-lg font-semibold">
                          Validated
                        </div>

                        <div className="text-xs text-white/35">
                          Workflow passed final checks.
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center gap-3">
                      <XCircle
                        size={24}
                        className="text-white/60"
                      />

                      <div>
                        <div className="text-lg font-semibold">
                          Review required
                        </div>

                        <div className="text-xs text-white/35">
                          Validation did not fully pass.
                        </div>
                      </div>
                    </div>
                  )}

                </div>


                <div className="mt-5 grid grid-cols-2 gap-2">

                  <div className="rounded-xl border border-white/8 bg-black/10 p-3">
                    <div className="text-[9px] uppercase tracking-wider text-white/25">
                      Retries
                    </div>

                    <div className="mt-1 text-xl font-semibold">
                      {result.retry_count}
                    </div>
                  </div>

                  <div className="rounded-xl border border-white/8 bg-black/10 p-3">
                    <div className="text-[9px] uppercase tracking-wider text-white/25">
                      Tools
                    </div>

                    <div className="mt-1 text-xl font-semibold">
                      {result.tools_used.length}
                    </div>
                  </div>

                  <div className="rounded-xl border border-white/8 bg-black/10 p-3">
                    <div className="text-[9px] uppercase tracking-wider text-white/25">
                      Evidence
                    </div>

                    <div className="mt-1 text-xl font-semibold">
                      {result.career_knowledge_evidence?.length ?? 0}
                    </div>
                  </div>

                </div>

              </section>


              {/* NEXT ACTION */}

              <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">

                <div className="text-[10px] uppercase tracking-[0.18em] text-white/30">
                  Next best action
                </div>

                {result.next_action ? (
                  <>
                    <h2 className="mt-3 text-xl font-semibold">
                      {typeof result.next_action.title ===
                      "string"
                        ? result.next_action.title
                        : "Continue your career plan"}
                    </h2>

                    <p className="mt-3 text-sm leading-6 text-white/40">
                      {typeof result.next_action.action ===
                      "string"
                        ? result.next_action.action
                        : "Review the recommendations and take the highest-impact action."}
                    </p>
                  </>
                ) : (
                  <p className="mt-3 text-sm leading-6 text-white/35">
                    Review the recommendations above and
                    take the highest-impact action first.
                  </p>
                )}

              </section>


              {/* CANDIDATE INTELLIGENCE */}

              <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">

                <div className="flex items-center gap-2">
                  <Target size={17} />

                  <span className="text-[10px] uppercase tracking-[0.18em] text-white/30">
                    Candidate intelligence
                  </span>
                </div>


                {result.candidate_intelligence ? (
                  <div className="mt-5 space-y-4">

                    <div>
                      <div className="text-[9px] uppercase tracking-wider text-white/25">
                        Readiness
                      </div>

                      <div className="mt-1 text-lg font-semibold">
                        {typeof result
                          .candidate_intelligence
                          .readiness_level ===
                        "string"
                          ? result
                              .candidate_intelligence
                              .readiness_level
                          : "Assessed"}
                      </div>
                    </div>


                    <div>
                      <div className="text-[9px] uppercase tracking-wider text-white/25">
                        Readiness score
                      </div>

                      <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/8">
                        <div
                          className="h-full rounded-full bg-white"
                          style={{
                            width: `${Math.max(
                              0,
                              Math.min(
                                100,
                                Number(
                                  result
                                    .candidate_intelligence
                                    .readiness_score ??
                                    0,
                                ),
                              ),
                            )}%`,
                          }}
                        />
                      </div>
                    </div>

                  </div>
                ) : (
                  <div className="mt-4 text-sm text-white/35">
                    Candidate intelligence is not available.
                  </div>
                )}

              </section>

            </aside>

          </div>
        )}

      </div>
    </main>
  );
}