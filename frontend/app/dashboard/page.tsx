"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { apiJson } from "@/lib/apiClient";
import {
  getWorkspaceState,
  type WorkspaceState,
} from "@/lib/workspace";

export default function DashboardPage() {
  const [
    workspace,
    setWorkspace,
  ] = useState<WorkspaceState>({
    jobs: [],
    applications: [],
    activity: [],
  });

  const [skills, setSkills] =
    useState<string[]>([]);

  useEffect(() => {
    const sync = () =>
      setWorkspace(
        getWorkspaceState(),
      );

    sync();

    window.addEventListener(
      "careerpilot:workspace",
      sync,
    );

    return () =>
      window.removeEventListener(
        "careerpilot:workspace",
        sync,
      );
  }, []);

  useEffect(() => {
    apiJson<{ profile?: { skills?: unknown } }>("/career-twin/session")
      .then((data) => {
        const values = data?.profile?.skills;
        if (Array.isArray(values)) {
          setSkills(values.filter((value): value is string => typeof value === "string"));
        }
      })
      .catch(() => undefined);

  }, []);

  const strongMatches =
    workspace.jobs.filter(
      (job) => {
        const score =
          Number(
            job.match_score ?? 0,
          );

        return (
          score >= 70 ||
          job.decision ===
            "APPLY_NOW" ||
          job.decision ===
            "GOOD_MATCH"
        );
      },
    ).length;

  return (
    <AppShell>
      <main className="min-h-screen bg-[#080a0f] p-6 text-white md:p-10">
        <div className="mx-auto max-w-7xl">
          <p className="text-xs uppercase tracking-[0.2em] text-white/60">
            CareerPilot Overview
          </p>

          <h1 className="mt-3 text-4xl font-semibold tracking-tight">
            Your Career Command Center
          </h1>

          <p className="mt-4 max-w-2xl text-sm leading-6 text-white/70">
            Live workspace metrics sourced from the shared
            opportunity, Career Twin and application state.
          </p>

          <div className="mt-10 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {[
              [
                "Opportunities",
                workspace.jobs.length,
              ],
              [
                "Strong matches",
                strongMatches,
              ],
              [
                "Skills",
                skills.length,
              ],
              [
                "Applications",
                workspace.applications.length,
              ],
            ].map(
              ([label, value]) => (
                <section
                  key={String(label)}
                  className="rounded-3xl border border-white/10 bg-white/[0.025] p-6 backdrop-blur"
                >
                  <div className="text-xs uppercase tracking-[0.16em] text-white/60">
                    {label}
                  </div>

                  <div className="mt-3 text-3xl font-semibold text-white">
                    {value}
                  </div>
                </section>
              ),
            )}
          </div>

          <section className="mt-6 rounded-3xl border border-white/10 bg-white/[0.025] p-6 backdrop-blur">
            <div className="text-xs uppercase tracking-[0.16em] text-white/60">
              Recent activity
            </div>

            <div className="mt-5 space-y-3">
              {workspace.activity.length ? (
                workspace.activity
                  .slice(0, 8)
                  .map((item) => (
                    <div
                      key={item.id}
                      className="rounded-2xl border border-white/8 bg-black/10 p-4"
                    >
                      <div className="text-sm font-medium text-white/90">
                        {item.title}
                      </div>

                      <div className="mt-1 text-xs text-white/60">
                        {item.detail}
                      </div>
                    </div>
                  ))
              ) : (
                <div className="text-sm text-white/50">
                  No activity yet. Search opportunities or run CareerPilot to generate live activity logs.
                </div>
              )}
            </div>
          </section>
        </div>
      </main>
    </AppShell>
  );
}
