"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Activity,
  BrainCircuit,
  CheckCircle2,
  Clock3,
  RefreshCw,
  Target,
  TrendingUp,
  UserRound,
  XCircle,
} from "lucide-react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://127.0.0.1:8000";

const CANDIDATE_ID = "api-user";

type CareerTwinProfile = {
  name?: string | null;
  headline?: string | null;
  skills: string[];
  technical_skills: string[];
  soft_skills: string[];
  education: string[];
  certifications: string[];
  projects: string[];
  experience: Record<string, unknown>[];
  target_roles: string[];
  target_industries: string[];
  target_locations: string[];
  preferred_work_modes: string[];
  minimum_salary_lpa?: number | null;
  timeline_months?: number | null;
};

type CareerTwinDerived = {
  strengths: string[];
  skill_gaps: string[];
  readiness_score: number;
  readiness_level: string;
  career_directions: string[];
};

type CareerMemoryEvent = {
  event_id: string;
  event_type: string;
  summary: string;
  timestamp: string;
  payload: Record<string, unknown>;
};

type CareerTwin = {
  candidate_id: string;
  version: number;
  profile: CareerTwinProfile;
  derived: CareerTwinDerived;
  memory: CareerMemoryEvent[];
  created_at: string;
  updated_at: string;
};

function formatDate(value: string) {
  try {
    return new Intl.DateTimeFormat("en-IN", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

function Pill({
  children,
  muted = false,
}: {
  children: React.ReactNode;
  muted?: boolean;
}) {
  return (
    <span
      className={
        muted
          ? "rounded-full border border-white/8 bg-white/[0.025] px-3 py-1.5 text-xs text-white/40"
          : "rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs text-white/70"
      }
    >
      {children}
    </span>
  );
}

function Section({
  label,
  title,
  children,
}: {
  label: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
      <div className="text-[10px] uppercase tracking-[0.2em] text-white/30">
        {label}
      </div>

      <h2 className="mt-2 text-xl font-semibold tracking-tight">
        {title}
      </h2>

      <div className="mt-5">{children}</div>
    </section>
  );
}

export default function CareerTwinPage() {
  const [twin, setTwin] = useState<CareerTwin | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const loadCareerTwin = useCallback(
    async (refresh = false) => {
      if (refresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setError("");

      try {
        const response = await fetch(
          `${API_BASE_URL}/career-twin/${CANDIDATE_ID}`,
          {
            cache: "no-store",
          },
        );

        if (!response.ok) {
          throw new Error(
            `Career Twin request failed (${response.status})`,
          );
        }

        const data = (await response.json()) as CareerTwin;
        setTwin(data);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load Career Twin.",
        );
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [],
  );

  useEffect(() => {
    void loadCareerTwin();
  }, [loadCareerTwin]);

  const profile = twin?.profile;
  const derived = twin?.derived;

  return (
    <main className="min-h-screen bg-[#080a0f] p-8 text-white md:p-10">
      <div className="mx-auto max-w-6xl">
        <div className="flex items-start justify-between gap-6">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-white/30">
              CareerPilot Intelligence
            </p>

            <h1 className="mt-3 text-4xl font-semibold tracking-tight">
              Career Twin
            </h1>

            <p className="mt-4 max-w-3xl text-sm leading-6 text-white/45">
              Your persistent AI representation of skills, experience,
              goals, preferences, readiness and evolving career evidence.
            </p>
          </div>

          <button
            type="button"
            onClick={() => void loadCareerTwin(true)}
            disabled={refreshing}
            className="inline-flex shrink-0 items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2.5 text-xs font-medium text-white/65 transition hover:bg-white/[0.06] hover:text-white disabled:opacity-50"
          >
            <RefreshCw
              size={14}
              className={refreshing ? "animate-spin" : ""}
            />
            Refresh
          </button>
        </div>

        {loading && (
          <div className="mt-8 grid gap-4 md:grid-cols-4">
            {Array.from({ length: 4 }, (_, index) => (
              <div
                key={index}
                className="h-32 animate-pulse rounded-3xl border border-white/8 bg-white/[0.025]"
              />
            ))}
          </div>
        )}

        {error && !loading && (
          <div className="mt-8 rounded-3xl border border-red-400/15 bg-red-400/[0.04] p-6">
            <div className="flex items-center gap-2 text-sm font-medium text-red-200">
              <XCircle size={16} />
              Career Twin unavailable
            </div>

            <p className="mt-2 text-sm text-red-100/55">
              {error}
            </p>
          </div>
        )}

        {!loading && twin && profile && derived && (
          <>
            <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-5">
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-white/30">
                  <Activity size={13} />
                  Readiness
                </div>

                <div className="mt-3 text-3xl font-semibold">
                  {Math.round(derived.readiness_score)}
                </div>

                <div className="mt-1 text-xs text-white/35">
                  {derived.readiness_level}
                </div>
              </div>

              <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-5">
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-white/30">
                  <BrainCircuit size={13} />
                  Skills
                </div>

                <div className="mt-3 text-3xl font-semibold">
                  {profile.skills.length}
                </div>

                <div className="mt-1 text-xs text-white/35">
                  Persistent skills tracked
                </div>
              </div>

              <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-5">
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-white/30">
                  <Target size={13} />
                  Goals
                </div>

                <div className="mt-3 text-3xl font-semibold">
                  {profile.target_roles.length}
                </div>

                <div className="mt-1 text-xs text-white/35">
                  Target roles tracked
                </div>
              </div>

              <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-5">
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-white/30">
                  <TrendingUp size={13} />
                  Twin version
                </div>

                <div className="mt-3 text-3xl font-semibold">
                  v{twin.version}
                </div>

                <div className="mt-1 text-xs text-white/35">
                  Updated {formatDate(twin.updated_at)}
                </div>
              </div>
            </div>

            <div className="mt-6 grid gap-6 lg:grid-cols-2">
              <Section
                label="Profile"
                title={profile.name || "Career profile"}
              >
                <div className="flex items-start gap-4">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.04]">
                    <UserRound size={20} className="text-white/55" />
                  </div>

                  <div>
                    <div className="text-sm text-white/70">
                      {profile.headline || "Professional profile"}
                    </div>

                    <div className="mt-3 text-xs text-white/30">
                      Candidate ID: {twin.candidate_id}
                    </div>
                  </div>
                </div>

                <div className="mt-6">
                  <div className="text-xs text-white/40">
                    Technical capabilities
                  </div>

                  <div className="mt-3 flex flex-wrap gap-2">
                    {profile.technical_skills.length > 0 ? (
                      profile.technical_skills.map((skill) => (
                        <Pill key={skill}>{skill}</Pill>
                      ))
                    ) : (
                      <Pill muted>No technical skills recorded</Pill>
                    )}
                  </div>
                </div>

                <div className="mt-6">
                  <div className="text-xs text-white/40">
                    Professional skills
                  </div>

                  <div className="mt-3 flex flex-wrap gap-2">
                    {profile.soft_skills.length > 0 ? (
                      profile.soft_skills.map((skill) => (
                        <Pill key={skill}>{skill}</Pill>
                      ))
                    ) : (
                      <Pill muted>
                        No professional skills recorded
                      </Pill>
                    )}
                  </div>
                </div>
              </Section>

              <Section
                label="Career goals"
                title="Target trajectory"
              >
                <div>
                  <div className="text-xs text-white/40">
                    Target roles
                  </div>

                  <div className="mt-3 flex flex-wrap gap-2">
                    {profile.target_roles.length > 0 ? (
                      profile.target_roles.map((role) => (
                        <Pill key={role}>{role}</Pill>
                      ))
                    ) : (
                      <Pill muted>No target role recorded</Pill>
                    )}
                  </div>
                </div>

                <div className="mt-6">
                  <div className="text-xs text-white/40">
                    Locations
                  </div>

                  <div className="mt-3 flex flex-wrap gap-2">
                    {profile.target_locations.length > 0 ? (
                      profile.target_locations.map((location) => (
                        <Pill key={location}>{location}</Pill>
                      ))
                    ) : (
                      <Pill muted>No target location recorded</Pill>
                    )}
                  </div>
                </div>

                <div className="mt-6">
                  <div className="text-xs text-white/40">
                    Work modes
                  </div>

                  <div className="mt-3 flex flex-wrap gap-2">
                    {profile.preferred_work_modes.length > 0 ? (
                      profile.preferred_work_modes.map((mode) => (
                        <Pill key={mode}>{mode}</Pill>
                      ))
                    ) : (
                      <Pill muted>No work-mode preference recorded</Pill>
                    )}
                  </div>
                </div>

                {profile.minimum_salary_lpa != null && (
                  <div className="mt-6 text-sm text-white/55">
                    Minimum salary target:{" "}
                    <span className="text-white/80">
                      ₹{profile.minimum_salary_lpa} LPA
                    </span>
                  </div>
                )}
              </Section>
            </div>

            <div className="mt-6 grid gap-6 lg:grid-cols-3">
              <Section label="Strengths" title="What you already have">
                <div className="space-y-2">
                  {derived.strengths.length > 0 ? (
                    derived.strengths.map((strength) => (
                      <div
                        key={strength}
                        className="flex items-center gap-2 rounded-2xl border border-emerald-400/10 bg-emerald-400/[0.03] px-3 py-2.5 text-sm text-emerald-100/70"
                      >
                        <CheckCircle2 size={14} />
                        {strength}
                      </div>
                    ))
                  ) : (
                    <div className="text-sm text-white/30">
                      Strength evidence is still being accumulated.
                    </div>
                  )}
                </div>
              </Section>

              <Section label="Skill gaps" title="Where to improve">
                <div className="space-y-2">
                  {derived.skill_gaps.length > 0 ? (
                    derived.skill_gaps.map((gap) => (
                      <div
                        key={gap}
                        className="flex items-center gap-2 rounded-2xl border border-amber-400/10 bg-amber-400/[0.03] px-3 py-2.5 text-sm text-amber-100/70"
                      >
                        <Target size={14} />
                        {gap}
                      </div>
                    ))
                  ) : (
                    <div className="text-sm text-white/30">
                      No persistent skill gaps recorded yet.
                    </div>
                  )}
                </div>
              </Section>

              <Section
                label="Directions"
                title="Career directions"
              >
                <div className="space-y-2">
                  {derived.career_directions.length > 0 ? (
                    derived.career_directions.map((direction) => (
                      <div
                        key={direction}
                        className="rounded-2xl border border-white/8 bg-white/[0.02] px-3 py-2.5 text-sm text-white/65"
                      >
                        {direction}
                      </div>
                    ))
                  ) : (
                    <div className="text-sm text-white/30">
                      Career directions will evolve from profile evidence.
                    </div>
                  )}
                </div>
              </Section>
            </div>

            <section className="mt-6 rounded-3xl border border-white/10 bg-white/[0.025] p-6">
              <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.2em] text-white/30">
                <Clock3 size={13} />
                Career memory
              </div>

              <h2 className="mt-2 text-xl font-semibold tracking-tight">
                Evolution timeline
              </h2>

              <div className="mt-5 space-y-3">
                {twin.memory.length > 0 ? (
                  twin.memory
                    .slice()
                    .reverse()
                    .slice(0, 8)
                    .map((event) => (
                      <div
                        key={event.event_id}
                        className="rounded-2xl border border-white/8 bg-white/[0.02] p-4"
                      >
                        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                          <div className="text-xs uppercase tracking-[0.14em] text-white/35">
                            {event.event_type}
                          </div>

                          <div className="text-[10px] text-white/20">
                            {formatDate(event.timestamp)}
                          </div>
                        </div>

                        <p className="mt-2 text-sm leading-6 text-white/55">
                          {event.summary}
                        </p>
                      </div>
                    ))
                ) : (
                  <div className="rounded-2xl border border-white/8 bg-white/[0.02] p-5 text-sm text-white/30">
                    No career memory events have been recorded yet.
                  </div>
                )}
              </div>
            </section>
          </>
        )}
      </div>
    </main>
  );
}
