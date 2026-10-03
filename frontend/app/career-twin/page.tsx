"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Download,
  GraduationCap,
  Award,
  Layers,
  MapPin,
  RefreshCw,
  Sparkles,
  UserRound,
} from "lucide-react";
import { apiJson } from "@/lib/apiClient";
import { AppShell } from "@/components/AppShell";
import { formatCurrency, formatRelativeTime } from "@/lib/formatters";

type CareerTwin = {
  candidate_id: string;
  version: number;
  profile: {
    name?: string | null;
    headline?: string | null;
    skills: string[];
    technical_skills: string[];
    soft_skills: string[];
    education: string[];
    certifications: string[];
    projects: string[];
    target_roles: string[];
    target_industries: string[];
    target_locations: string[];
    preferred_work_modes: string[];
    minimum_salary_lpa?: number | null;
  };
  derived: {
    strengths: string[];
    skill_gaps: string[];
    readiness_score: number;
    readiness_level: string;
    career_directions: string[];
  };
  memory: Array<{
    event_id: string;
    event_type: string;
    summary: string;
    timestamp: string;
  }>;
};

export default function CareerTwinPage() {
  const [twin, setTwin] = useState<CareerTwin | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [memoryLimit, setMemoryLimit] = useState(8);

  const load = useCallback(async () => {
    try {
      const data = await apiJson<CareerTwin>("/career-twin/session", {
        credentials: "include",
      });
      setTwin(data);
      return true;
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to load Career Twin.",
      );
      return false;
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    const run = async () => {
      await load();
      if (!cancelled) {
        setLoading(false);
      }
    };

    void run();

    return () => {
      cancelled = true;
    };
  }, [load]);

  function exportProfileJson() {
    if (!twin || typeof window === "undefined") return;
    const blob = new Blob([JSON.stringify(twin, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `careerpilot-twin-${twin.candidate_id || "profile"}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  if (loading) {
    return (
      <AppShell>
        <main className="min-h-screen bg-[#080a0f] p-8 text-white">
          <div className="mx-auto max-w-6xl">
            <div className="h-10 w-64 animate-pulse rounded-2xl bg-white/5" />
            <div className="mt-8 grid gap-4 md:grid-cols-4">
              {Array.from({ length: 4 }, (_, index) => (
                <div
                  key={`twin-skeleton-${index}`}
                  className="h-32 animate-pulse rounded-3xl bg-white/[0.03]"
                />
              ))}
            </div>
          </div>
        </main>
      </AppShell>
    );
  }

  if (error) {
    return (
      <AppShell>
        <main className="min-h-screen bg-[#080a0f] p-8 text-white">
          <div className="mx-auto max-w-6xl">
            <div className="rounded-3xl border border-red-500/20 bg-red-500/[0.04] p-6 text-red-200">
              <h2 className="text-base font-semibold text-red-100">Unable to load profile</h2>
              <p className="mt-2 text-sm text-red-200/80">{error}</p>
              <button
                type="button"
                onClick={() => {
                  setError("");
                  setLoading(true);
                  void load().finally(() => setLoading(false));
                }}
                className="mt-4 rounded-xl border border-red-400/30 bg-red-400/10 px-4 py-2 text-xs font-semibold text-red-100"
              >
                Retry
              </button>
            </div>
          </div>
        </main>
      </AppShell>
    );
  }

  if (!twin) {
    return null;
  }

  const profile = twin.profile;

  return (
    <AppShell>
      <main className="min-h-screen bg-[#080a0f] p-5 text-white md:p-8">
        <div className="mx-auto max-w-6xl">
          <header className="border-b border-white/10 pb-7">
            <div className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
              <div>
                <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-white/60">
                  <Sparkles size={14} className="text-cyan-400" />
                  Persistent Career Memory
                </div>

                <h1 className="mt-3 text-4xl font-semibold tracking-tight">
                  Career Twin
                </h1>

                <p className="mt-3 max-w-2xl text-sm leading-6 text-white/70">
                  Your evolving career representation across skills, goals,
                  opportunities, preferences, and historical agent interactions.
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={exportProfileJson}
                  aria-label="Export profile as JSON"
                  className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-4 py-2.5 text-xs text-white/80 transition hover:bg-white/5"
                >
                  <Download size={14} />
                  Export JSON
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setError("");
                    setLoading(true);
                    void load().finally(() => setLoading(false));
                  }}
                  className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-xs text-white transition hover:bg-white/10"
                >
                  <RefreshCw size={14} />
                  Refresh
                </button>
              </div>
            </div>
          </header>

          <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {[
              ["Readiness", `${Math.round(twin.derived.readiness_score)}%`, "Market alignment"],
              ["Skills Tracked", profile.skills.length, "Technical & soft skills"],
              ["Target Roles", profile.target_roles.length, "Target career tracks"],
              ["Twin Version", `v${twin.version}`, "Continuous state graph"],
            ].map(([label, value, hint]) => (
              <section
                key={String(label)}
                className="rounded-3xl border border-white/10 bg-white/[0.025] p-5 backdrop-blur"
              >
                <div className="text-xs uppercase tracking-[0.18em] text-white/60">
                  {label}
                </div>

                <div className="mt-3 text-3xl font-semibold text-white">
                  {value}
                </div>

                <div className="mt-1 text-[11px] text-white/50">{hint}</div>
              </section>
            ))}
          </div>

          <div className="mt-6 grid gap-6 lg:grid-cols-2">
            {/* Identity & Technical Skills */}
            <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6 backdrop-blur">
              <div className="flex items-center gap-3 border-b border-white/10 pb-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-white/10 bg-white/5">
                  <UserRound size={20} className="text-cyan-400" />
                </div>
                <div>
                  <div className="font-semibold text-white/95">
                    {profile.name || "Career Profile"}
                  </div>
                  <div className="text-xs text-white/60">
                    {profile.headline || "Autonomous Career Candidate"}
                  </div>
                </div>
              </div>

              <div className="mt-5">
                <div className="text-xs uppercase tracking-[0.16em] text-white/60">
                  Technical Skills ({profile.technical_skills.length})
                </div>

                <div className="mt-3 flex flex-wrap gap-2">
                  {profile.technical_skills.length ? (
                    profile.technical_skills.map((skill) => (
                      <span
                        key={skill}
                        className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-xs font-medium text-white/80"
                      >
                        {skill}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-white/50">No technical skills recorded.</span>
                  )}
                </div>
              </div>

              {profile.soft_skills.length > 0 && (
                <div className="mt-5">
                  <div className="text-xs uppercase tracking-[0.16em] text-white/60">
                    Soft Skills & Leadership
                  </div>

                  <div className="mt-2.5 flex flex-wrap gap-2">
                    {profile.soft_skills.map((skill) => (
                      <span
                        key={skill}
                        className="rounded-full border border-white/8 bg-white/[0.02] px-2.5 py-1 text-xs text-white/70"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Preferences */}
              <div className="mt-6 border-t border-white/10 pt-4">
                <div className="text-xs uppercase tracking-[0.16em] text-white/60">
                  Work Preferences
                </div>

                <div className="mt-3 grid grid-cols-2 gap-3 text-xs">
                  <div className="rounded-xl border border-white/8 bg-white/[0.02] p-3">
                    <span className="text-white/50">Min. Target Salary:</span>
                    <div className="mt-1 font-semibold text-white/90">
                      {profile.minimum_salary_lpa
                        ? formatCurrency(profile.minimum_salary_lpa * 100000) + "/yr"
                        : "Flexible / Not set"}
                    </div>
                  </div>

                  <div className="rounded-xl border border-white/8 bg-white/[0.02] p-3">
                    <span className="text-white/50">Preferred Modes:</span>
                    <div className="mt-1 font-semibold text-white/90">
                      {profile.preferred_work_modes?.length
                        ? profile.preferred_work_modes.join(", ")
                        : "Any"}
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Career Direction & Target Industries */}
            <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6 backdrop-blur">
              <div className="text-xs uppercase tracking-[0.16em] text-white/60">
                Target Roles & Directions
              </div>

              <div className="mt-4 space-y-2">
                {profile.target_roles.length ? (
                  profile.target_roles.map((role) => (
                    <div
                      key={role}
                      className="flex items-center justify-between rounded-2xl border border-white/8 bg-white/[0.02] p-3.5 text-sm"
                    >
                      <span className="font-medium text-white/90">{role}</span>
                      <span className="rounded-full border border-cyan-500/20 bg-cyan-500/10 px-2.5 py-0.5 text-[11px] text-cyan-300">
                        Target Role
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="rounded-2xl border border-dashed border-white/10 p-4 text-xs text-white/50">
                    No target roles configured. Run CareerPilot on the home page to set your goal.
                  </div>
                )}
              </div>

              {profile.target_industries?.length > 0 && (
                <div className="mt-5">
                  <div className="text-xs uppercase tracking-[0.16em] text-white/60">
                    Target Industries
                  </div>
                  <div className="mt-2.5 flex flex-wrap gap-2">
                    {profile.target_industries.map((ind) => (
                      <span
                        key={ind}
                        className="rounded-full border border-white/8 bg-white/[0.02] px-3 py-1 text-xs text-white/70"
                      >
                        {ind}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {profile.target_locations?.length > 0 && (
                <div className="mt-5">
                  <div className="text-xs uppercase tracking-[0.16em] text-white/60">
                    Target Locations
                  </div>
                  <div className="mt-2.5 flex flex-wrap gap-2">
                    {profile.target_locations.map((loc) => (
                      <span
                        key={loc}
                        className="inline-flex items-center gap-1 rounded-full border border-white/8 bg-white/[0.02] px-3 py-1 text-xs text-white/70"
                      >
                        <MapPin size={11} className="text-cyan-400" />
                        {loc}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Strengths & Skill Gaps */}
              <div className="mt-6 border-t border-white/10 pt-4">
                <div className="text-xs uppercase tracking-[0.16em] text-white/60">
                  Derived Market Signals
                </div>

                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                  <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/[0.02] p-3 text-xs">
                    <span className="font-semibold text-emerald-300">Core Strengths:</span>
                    <ul className="mt-1.5 space-y-1 text-white/70">
                      {twin.derived.strengths?.length ? (
                        twin.derived.strengths.slice(0, 3).map((s, i) => (
                          <li key={i}>• {s}</li>
                        ))
                      ) : (
                        <li>• Established foundational skills</li>
                      )}
                    </ul>
                  </div>

                  <div className="rounded-2xl border border-amber-500/20 bg-amber-500/[0.02] p-3 text-xs">
                    <span className="font-semibold text-amber-300">Growth Opportunities:</span>
                    <ul className="mt-1.5 space-y-1 text-white/70">
                      {twin.derived.skill_gaps?.length ? (
                        twin.derived.skill_gaps.slice(0, 3).map((g, i) => (
                          <li key={i}>• {g}</li>
                        ))
                      ) : (
                        <li>• High readiness across active targets</li>
                      )}
                    </ul>
                  </div>
                </div>
              </div>
            </section>
          </div>

          {/* Education, Certifications & Projects */}
          <div className="mt-6 grid gap-6 lg:grid-cols-3">
            <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6 backdrop-blur">
              <div className="flex items-center gap-2 text-xs uppercase tracking-[0.16em] text-white/60">
                <GraduationCap size={15} className="text-cyan-400" />
                Education
              </div>

              <div className="mt-4 space-y-2">
                {profile.education?.length ? (
                  profile.education.map((edu, idx) => (
                    <div key={idx} className="rounded-2xl border border-white/8 bg-white/[0.02] p-3 text-xs text-white/80">
                      {edu}
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-white/50">No formal education entries recorded.</div>
                )}
              </div>
            </section>

            <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6 backdrop-blur">
              <div className="flex items-center gap-2 text-xs uppercase tracking-[0.16em] text-white/60">
                <Award size={15} className="text-emerald-400" />
                Certifications
              </div>

              <div className="mt-4 space-y-2">
                {profile.certifications?.length ? (
                  profile.certifications.map((cert, idx) => (
                    <div key={idx} className="rounded-2xl border border-white/8 bg-white/[0.02] p-3 text-xs text-white/80">
                      {cert}
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-white/50">No certifications recorded.</div>
                )}
              </div>
            </section>

            <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6 backdrop-blur">
              <div className="flex items-center gap-2 text-xs uppercase tracking-[0.16em] text-white/60">
                <Layers size={15} className="text-purple-400" />
                Key Projects
              </div>

              <div className="mt-4 space-y-2">
                {profile.projects?.length ? (
                  profile.projects.map((proj, idx) => (
                    <div key={idx} className="rounded-2xl border border-white/8 bg-white/[0.02] p-3 text-xs text-white/80">
                      {proj}
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-white/50">No project portfolio entries recorded.</div>
                )}
              </div>
            </section>
          </div>

          {/* Career Memory Timeline */}
          <section className="mt-6 rounded-3xl border border-white/10 bg-white/[0.025] p-6 backdrop-blur">
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <div>
                <div className="text-xs uppercase tracking-[0.16em] text-white/60">
                  Career Memory Timeline
                </div>
                <p className="mt-1 text-xs text-white/60">
                  Audit log of historical agent reasoning, search dispatches, and profile checkpoints.
                </p>
              </div>

              <div className="flex items-center gap-3">
                {twin.memory.length > memoryLimit && (
                  <button
                    type="button"
                    onClick={() => setMemoryLimit(twin.memory.length)}
                    className="text-xs font-medium text-cyan-400 underline underline-offset-4 hover:text-cyan-300"
                  >
                    View all ({twin.memory.length})
                  </button>
                )}

                {memoryLimit >= twin.memory.length && twin.memory.length > 8 && (
                  <button
                    type="button"
                    onClick={() => setMemoryLimit(8)}
                    className="text-xs font-medium text-cyan-400 underline underline-offset-4 hover:text-cyan-300"
                  >
                    Collapse
                  </button>
                )}
              </div>
            </div>

            <div className="mt-4 space-y-2.5">
              {twin.memory.slice(0, memoryLimit).map((event) => (
                <div
                  key={event.event_id}
                  className="rounded-2xl border border-white/8 bg-white/[0.02] p-3.5 transition hover:border-white/15"
                >
                  <div className="text-sm font-medium text-white/90">
                    {event.summary}
                  </div>

                  <div className="mt-1 text-[11px] text-white/50">
                    {event.event_type} • {formatRelativeTime(event.timestamp)}
                  </div>
                </div>
              ))}

              {twin.memory.length === 0 && (
                <div className="py-6 text-center text-sm text-white/50">
                  No career memory events recorded yet. Run a workflow to record memory milestones.
                </div>
              )}
            </div>
          </section>
        </div>
      </main>
    </AppShell>
  );
}
