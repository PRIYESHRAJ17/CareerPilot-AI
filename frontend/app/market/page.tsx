"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  BarChart3,
  BriefcaseBusiness,
  CheckCircle2,
  ChevronRight,
  Globe2,
  Lightbulb,
  Target,
  TrendingUp,
  X,
} from "lucide-react";

import { AppShell } from "@/components/AppShell";
import { listWorkspace } from "@/lib/productWorkspace";

type Snapshot = Record<string, unknown>;

function stringValue(
  value: unknown,
  fallback = "",
): string {
  return typeof value === "string"
    ? value
    : value == null
      ? fallback
      : String(value);
}

function numberValue(
  value: unknown,
  fallback = 0,
): number {
  return typeof value === "number"
    ? value
    : typeof value === "string" && value.trim()
      ? Number(value) || fallback
      : fallback;
}

function stringList(
  value: unknown,
): string[] {
  if (Array.isArray(value)) {
    return value
      .map((item) => {
        if (typeof item === "string") {
          return item.trim();
        }

        if (
          item &&
          typeof item === "object"
        ) {
          const record =
            item as Record<string, unknown>;

          return (
            stringValue(
              record.value,
            ) ||
            stringValue(
              record.skill,
            ) ||
            stringValue(
              record.role,
            ) ||
            stringValue(
              record.name,
            )
          ).trim();
        }

        return "";
      })
      .filter(Boolean);
  }

  if (typeof value === "string") {
    return value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }

  return [];
}

function objectValue(
  value: unknown,
): Record<string, unknown> {
  return value &&
    typeof value === "object" &&
    !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function formatLabel(
  value: string,
): string {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) =>
      char.toUpperCase(),
    );
}

function formatDate(
  value: unknown,
): string | null {
  const raw = stringValue(value);

  if (!raw) {
    return null;
  }

  const date = new Date(raw);

  if (Number.isNaN(date.getTime())) {
    return null;
  }

  return date.toLocaleString(
    undefined,
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  );
}

function getMarketSummary(
  item: Snapshot,
): Record<string, unknown> {
  const value = item?.market_summary;

  if (
    !value ||
    typeof value !== "object" ||
    Array.isArray(value)
  ) {
    return {};
  }

  return value as Record<string, unknown>;
}

function getTopItems(
  item: Snapshot,
  key: string,
): string[] {
  const raw = item[key];

  if (!Array.isArray(raw)) {
    return [];
  }

  return raw
    .map((entry) => {
      if (
        typeof entry === "string"
      ) {
        return entry;
      }

      if (
        entry &&
        typeof entry === "object"
      ) {
        const record =
          entry as Record<string, unknown>;

        return (
          stringValue(
            record.value,
          ) ||
          stringValue(
            record.skill,
          ) ||
          stringValue(
            record.role,
          ) ||
          stringValue(
            record.name,
          )
        );
      }

      return "";
    })
    .filter(Boolean);
}

export default function MarketPage() {
  const [items, setItems] =
    useState<Snapshot[]>([]);

  const [selectedSnapshot, setSelectedSnapshot] =
    useState<Snapshot | null>(null);

  useEffect(() => {
    listWorkspace("market")
      .then((data) => {
        setItems(
          Array.isArray(data)
            ? data
            : [],
        );
      })
      .catch(() => {
        setItems([]);
      });
  }, []);

  const latest =
    items[0] ?? null;
  const latestRecord =
    latest ?? {};

  const latestSources = useMemo(
    () =>
      latest
        ? stringList(
            latest.sources,
          )
        : [],
    [latest],
  );

  const latestMarketSummary =
    latest
      ? getMarketSummary(latest)
      : {};

  const latestSkills =
    latest
      ? getTopItems(
          latest,
          "top_market_skills",
        )
      : [];

  const latestRequiredSkills =
    latest
      ? getTopItems(
          latest,
          "top_required_skills",
        )
      : [];

  const latestRoles =
    latest
      ? getTopItems(
          latest,
          "market_roles",
        )
      : [];

  const latestGaps =
    latest
      ? stringList(
          latest.priority_skill_gaps,
        )
      : [];

  const latestRecommendations =
    latest &&
    Array.isArray(
      latest.recommendations,
    )
      ? latest.recommendations
          .map((item) => {
            if (
              typeof item ===
              "string"
            ) {
              return item;
            }

            if (
              item &&
              typeof item ===
                "object"
            ) {
              const record =
                item as Record<
                  string,
                  unknown
                >;

              return (
                stringValue(
                  record.action,
                ) ||
                stringValue(
                  record.reason,
                ) ||
                stringValue(
                  record.title,
                )
              );
            }

            return "";
          })
          .filter(Boolean)
      : [];

  const latestRoleAlignment =
    numberValue(
      latestMarketSummary.role_alignment_to_target,
      numberValue(
        latestRecord.role_alignment_to_target,
      ),
    );

  const latestJobsAnalyzed =
    numberValue(
      latestRecord.jobs_analyzed,
      numberValue(
        latestRecord.result_count,
      ),
    );

  const marketDepth =
    stringValue(
      latestMarketSummary?.market_depth,
      latest
        ? latestJobsAnalyzed >=
          200
          ? "HIGH"
          : latestJobsAnalyzed >=
              50
            ? "MEDIUM"
            : "LOW"
        : "LOW",
    );

  const snapshotDate =
    formatDate(
      latestRecord.timestamp ??
        latestRecord.created_at ??
        latestRecord.updated_at,
    );

  return (
    <AppShell>
      <main className="min-h-screen p-5 text-white md:p-8">
        <div className="mx-auto max-w-7xl">
          {/* HEADER */}
          <header className="border-b border-white/10 pb-6">
            <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-cyan-300/80">
                  <TrendingUp
                    size={14}
                  />
                  Market intelligence
                </div>

                <h1 className="mt-2 text-4xl font-semibold tracking-tight">
                  Market Intelligence
                </h1>

                <p className="mt-3 max-w-3xl text-sm leading-6 text-white/65">
                  Review persisted market
                  snapshots, live-source
                  contribution counts, skill
                  demand and candidate-relative
                  signals derived from CareerPilot&apos;s
                  opportunity data.
                </p>
              </div>

              {snapshotDate && (
                <div className="rounded-2xl border border-white/10 bg-white/[0.025] px-4 py-3 text-right">
                  <div className="text-[10px] uppercase tracking-[0.16em] text-white/35">
                    Latest snapshot
                  </div>

                  <div className="mt-1 text-sm text-white/70">
                    {snapshotDate}
                  </div>
                </div>
              )}
            </div>
          </header>

          {/* TOP METRICS */}
          <section className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-5">
              <div className="flex items-center justify-between">
                <div className="text-xs uppercase tracking-[0.16em] text-white/45">
                  Snapshots
                </div>

                <Activity
                  size={16}
                  className="text-cyan-300/70"
                />
              </div>

              <div className="mt-3 text-3xl font-semibold">
                {items.length}
              </div>

              <p className="mt-2 text-xs leading-5 text-white/40">
                Persisted market observations.
              </p>
            </div>

            <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-5">
              <div className="flex items-center justify-between">
                <div className="text-xs uppercase tracking-[0.16em] text-white/45">
                  Opportunities analyzed
                </div>

                <BriefcaseBusiness
                  size={16}
                  className="text-cyan-300/70"
                />
              </div>

              <div className="mt-3 text-3xl font-semibold">
                {latestJobsAnalyzed}
              </div>

              <p className="mt-2 text-xs leading-5 text-white/40">
                From the latest persisted
                market snapshot.
              </p>
            </div>

            <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-5">
              <div className="flex items-center justify-between">
                <div className="text-xs uppercase tracking-[0.16em] text-white/45">
                  Market depth
                </div>

                <BarChart3
                  size={16}
                  className="text-cyan-300/70"
                />
              </div>

              <div className="mt-3 text-3xl font-semibold">
                {formatLabel(
                  marketDepth,
                )}
              </div>

              <p className="mt-2 text-xs leading-5 text-white/40">
                Based on the number of
                analyzed opportunities.
              </p>
            </div>

            <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-5">
              <div className="flex items-center justify-between">
                <div className="text-xs uppercase tracking-[0.16em] text-white/45">
                  Target alignment
                </div>

                <Target
                  size={16}
                  className="text-cyan-300/70"
                />
              </div>

              <div className="mt-3 text-3xl font-semibold">
                {latestRoleAlignment > 0
                  ? `${latestRoleAlignment}%`
                  : "—"}
              </div>

              <p className="mt-2 text-xs leading-5 text-white/40">
                Role alignment recorded in
                the latest market snapshot.
              </p>
            </div>
          </section>

          {/* SOURCE CONTRIBUTION */}
          <section className="mt-6 rounded-3xl border border-white/10 bg-white/[0.025] p-6">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-white/45">
                  <Globe2 size={14} />
                  Live source contribution
                </div>

                <h2 className="mt-2 text-xl font-semibold">
                  Latest opportunity sources
                </h2>

                <p className="mt-2 max-w-2xl text-sm leading-6 text-white/45">
                  Providers that contributed to
                  the latest persisted market
                  snapshot.
                </p>
              </div>

              <div className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-white/50">
                {latestSources.length} sources
              </div>
            </div>

            <div className="mt-5 flex flex-wrap gap-2">
              {latestSources.length > 0 ? (
                latestSources.map(
                  (source) => (
                    <span
                      key={source}
                      className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-white/65"
                    >
                      {formatLabel(
                        source,
                      )}
                    </span>
                  ),
                )
              ) : (
                <div className="rounded-2xl border border-white/8 bg-black/10 px-4 py-3 text-sm text-white/40">
                  Run a live opportunity
                  search to create a market
                  snapshot.
                </div>
              )}
            </div>
          </section>

          {/* MARKET SIGNALS */}
          {latest && (
            <>
              <section className="mt-6 grid gap-4 lg:grid-cols-2">
                <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
                  <div className="text-xs uppercase tracking-[0.16em] text-white/40">
                    Market skill demand
                  </div>

                  <h2 className="mt-2 text-xl font-semibold">
                    Most visible skills
                  </h2>

                  <div className="mt-5 flex flex-wrap gap-2">
                    {latestSkills.length >
                    0 ? (
                      latestSkills
                        .slice(0, 12)
                        .map((skill) => (
                          <span
                            key={skill}
                            className="rounded-full border border-cyan-400/15 bg-cyan-400/5 px-3 py-1.5 text-xs text-cyan-100/80"
                          >
                            {formatLabel(
                              skill,
                            )}
                          </span>
                        ))
                    ) : (
                      <p className="text-sm text-white/35">
                        No market skill
                        distribution was
                        recorded.
                      </p>
                    )}
                  </div>
                </div>

                <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
                  <div className="text-xs uppercase tracking-[0.16em] text-white/40">
                    Required skills
                  </div>

                  <h2 className="mt-2 text-xl font-semibold">
                    Frequently required
                  </h2>

                  <div className="mt-5 flex flex-wrap gap-2">
                    {latestRequiredSkills.length >
                    0 ? (
                      latestRequiredSkills
                        .slice(0, 12)
                        .map((skill) => (
                          <span
                            key={skill}
                            className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-white/65"
                          >
                            {formatLabel(
                              skill,
                            )}
                          </span>
                        ))
                    ) : (
                      <p className="text-sm text-white/35">
                        No required-skill
                        distribution was
                        recorded.
                      </p>
                    )}
                  </div>
                </div>
              </section>

              <section className="mt-4 grid gap-4 lg:grid-cols-2">
                <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
                  <div className="text-xs uppercase tracking-[0.16em] text-white/40">
                    Market roles
                  </div>

                  <h2 className="mt-2 text-xl font-semibold">
                    Observed role demand
                  </h2>

                  <div className="mt-5 space-y-2">
                    {latestRoles.length >
                    0 ? (
                      latestRoles
                        .slice(0, 10)
                        .map(
                          (
                            role,
                            index,
                          ) => (
                            <div
                              key={`${role}-${index}`}
                              className="flex items-center justify-between rounded-2xl border border-white/8 bg-black/10 px-4 py-3"
                            >
                              <span className="text-sm text-white/70">
                                {formatLabel(
                                  role,
                                )}
                              </span>

                              <span className="text-xs text-white/35">
                                Observed
                              </span>
                            </div>
                          ),
                        )
                    ) : (
                      <p className="text-sm text-white/35">
                        No role distribution
                        was recorded.
                      </p>
                    )}
                  </div>
                </div>

                <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
                  <div className="text-xs uppercase tracking-[0.16em] text-white/40">
                    Priority skill gaps
                  </div>

                  <h2 className="mt-2 text-xl font-semibold">
                    Candidate-relative gaps
                  </h2>

                  <div className="mt-5 space-y-2">
                    {latestGaps.length >
                    0 ? (
                      latestGaps
                        .slice(0, 10)
                        .map(
                          (
                            gap,
                            index,
                          ) => (
                            <div
                              key={`${gap}-${index}`}
                              className="flex items-center gap-3 rounded-2xl border border-amber-400/10 bg-amber-400/[0.03] px-4 py-3"
                            >
                              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-amber-400/10 text-xs text-amber-200/70">
                                {index +
                                  1}
                              </span>

                              <span className="text-sm text-white/70">
                                {formatLabel(
                                  gap,
                                )}
                              </span>
                            </div>
                          ),
                        )
                    ) : (
                      <p className="text-sm text-white/35">
                        No priority gaps were
                        recorded in this
                        snapshot.
                      </p>
                    )}
                  </div>
                </div>
              </section>

              {/* RECOMMENDATIONS */}
              <section className="mt-6 rounded-3xl border border-white/10 bg-white/[0.025] p-6">
                <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-white/40">
                  <Lightbulb size={14} />
                  Career recommendations
                </div>

                <h2 className="mt-2 text-xl font-semibold">
                  What the market signals suggest
                </h2>

                <div className="mt-5 grid gap-3 lg:grid-cols-2">
                  {latestRecommendations.length >
                  0 ? (
                    latestRecommendations
                      .slice(0, 8)
                      .map(
                        (
                          recommendation,
                          index,
                        ) => (
                          <div
                            key={`${recommendation}-${index}`}
                            className="rounded-2xl border border-white/8 bg-black/10 p-4"
                          >
                            <div className="flex items-start gap-3">
                              <CheckCircle2
                                size={18}
                                className="mt-0.5 shrink-0 text-emerald-300/70"
                              />

                              <div>
                                <div className="text-sm font-medium text-white/80">
                                  {recommendation}
                                </div>
                              </div>
                            </div>
                          </div>
                        ),
                      )
                  ) : (
                    <p className="text-sm text-white/35">
                      No recommendations were
                      recorded in this snapshot.
                    </p>
                  )}
                </div>
              </section>

              {/* SNAPSHOTS */}
              <section className="mt-6">
                <div className="mb-4 flex items-end justify-between">
                  <div>
                    <div className="text-xs uppercase tracking-[0.18em] text-white/40">
                      History
                    </div>

                    <h2 className="mt-2 text-xl font-semibold">
                      Persisted market snapshots
                    </h2>
                  </div>

                  <div className="text-xs text-white/35">
                    {items.length} recorded
                  </div>
                </div>

                <div className="space-y-3">
                  {items.map(
                    (
                      item,
                      index,
                    ) => {
                      const snapshotSources =
                        stringList(
                          item.sources,
                        );

                      const resultCount =
                        numberValue(
                          item.result_count,
                          numberValue(
                            item.jobs_analyzed,
                          ),
                        );

                      const query =
                        stringValue(
                          item.query,
                          "Market search",
                        );

                      const snapshotRoleAlignment =
                        numberValue(
                          getMarketSummary(
                            item,
                          )
                            .role_alignment_to_target,
                          numberValue(
                            item.role_alignment_to_target,
                          ),
                        );

                      const snapshotDepth =
                        stringValue(
                          getMarketSummary(
                            item,
                          )
                            .market_depth,
                        );

                      const snapshotGaps =
                        stringList(
                          item.priority_skill_gaps,
                        );

                      return (
                        <article
                          key={String(
                            item.id ??
                              `${index}-${query}`,
                          )}
                          className="rounded-3xl border border-white/10 bg-white/[0.025] p-5"
                        >
                          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                            <div>
                              <div className="flex flex-wrap items-center gap-2">
                                <span className="rounded-full border border-white/10 bg-white/[0.03] px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-white/40">
                                  Snapshot{" "}
                                  {index +
                                    1}
                                </span>

                                {snapshotDepth && (
                                  <span className="rounded-full border border-cyan-400/10 bg-cyan-400/5 px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-cyan-200/70">
                                    {formatLabel(
                                      snapshotDepth,
                                    )}
                                  </span>
                                )}
                              </div>

                              <h3 className="mt-3 text-lg font-semibold">
                                {query}
                              </h3>

                              <p className="mt-1 text-sm text-white/40">
                                {resultCount} opportunities
                                analyzed
                                {snapshotRoleAlignment >
                                0
                                  ? ` · ${snapshotRoleAlignment}% target-role alignment`
                                  : ""}
                              </p>
                            </div>

                            <button
                              type="button"
                              onClick={() =>
                                setSelectedSnapshot(
                                  item,
                                )
                              }
                              className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2.5 text-xs font-semibold text-white/70 transition hover:bg-white/[0.07] hover:text-white"
                            >
                              View details
                              <ChevronRight
                                size={14}
                              />
                            </button>
                          </div>

                          {snapshotSources.length >
                            0 && (
                            <div className="mt-4 flex flex-wrap gap-2">
                              {snapshotSources
                                .slice(0, 12)
                                .map(
                                  (
                                    source,
                                  ) => (
                                    <span
                                      key={`${index}-${source}`}
                                      className="rounded-full border border-white/8 px-2.5 py-1 text-[10px] uppercase tracking-[0.12em] text-white/35"
                                    >
                                      {formatLabel(
                                        source,
                                      )}
                                    </span>
                                  ),
                                )}

                              {snapshotSources.length >
                                12 && (
                                <span className="rounded-full border border-white/8 px-2.5 py-1 text-[10px] text-white/30">
                                  +
                                  {snapshotSources.length -
                                    12}{" "}
                                  more
                                </span>
                              )}
                            </div>
                          )}

                          {snapshotGaps.length >
                            0 && (
                            <div className="mt-4 flex flex-wrap gap-2">
                              {snapshotGaps
                                .slice(0, 6)
                                .map(
                                  (
                                    gap,
                                  ) => (
                                    <span
                                      key={`${index}-${gap}`}
                                      className="rounded-full border border-amber-400/10 bg-amber-400/[0.03] px-2.5 py-1 text-[10px] text-amber-200/60"
                                    >
                                      Gap:{" "}
                                      {formatLabel(
                                        gap,
                                      )}
                                    </span>
                                  ),
                                )}
                            </div>
                          )}
                        </article>
                      );
                    },
                  )}
                </div>
              </section>
            </>
          )}

          {/* EMPTY STATE */}
          {!latest && (
            <section className="mt-6 rounded-3xl border border-dashed border-white/10 bg-white/[0.02] p-10 text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03]">
                <BarChart3
                  size={22}
                  className="text-white/40"
                />
              </div>

              <h2 className="mt-5 text-xl font-semibold">
                No market snapshot yet
              </h2>

              <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-white/40">
                Run a live opportunity search
                to populate Market Intelligence
                with real source contributions,
                market demand and candidate-relative
                signals.
              </p>
            </section>
          )}
        </div>

        {/* DETAIL DRAWER */}
        {selectedSnapshot && (
          <div className="fixed inset-0 z-50">
            <button
              type="button"
              aria-label="Close market snapshot"
              onClick={() =>
                setSelectedSnapshot(
                  null,
                )
              }
              className="absolute inset-0 bg-black/70 backdrop-blur-sm"
            />

            <aside className="absolute right-0 top-0 h-full w-full max-w-2xl overflow-y-auto border-l border-white/10 bg-[#090b10] p-6 shadow-2xl">
              <div className="flex items-center justify-between border-b border-white/10 pb-4">
                <div>
                  <div className="text-xs uppercase tracking-[0.18em] text-white/40">
                    Market snapshot
                  </div>

                  <h2 className="mt-1 text-2xl font-semibold">
                    {stringValue(
                      selectedSnapshot.query,
                      "Market snapshot",
                    )}
                  </h2>
                </div>

                <button
                  type="button"
                  onClick={() =>
                    setSelectedSnapshot(
                      null,
                    )
                  }
                  className="rounded-xl border border-white/10 p-2 text-white/50 transition hover:bg-white/[0.06] hover:text-white"
                  aria-label="Close"
                >
                  <X size={18} />
                </button>
              </div>

              <div className="mt-6 space-y-5">
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-2xl border border-white/8 bg-white/[0.025] p-4">
                    <div className="text-[10px] uppercase tracking-[0.16em] text-white/35">
                      Opportunities
                    </div>

                    <div className="mt-2 text-2xl font-semibold">
                      {numberValue(
                        selectedSnapshot.result_count,
                        numberValue(
                          selectedSnapshot.jobs_analyzed,
                        ),
                      )}
                    </div>
                  </div>

                  <div className="rounded-2xl border border-white/8 bg-white/[0.025] p-4">
                    <div className="text-[10px] uppercase tracking-[0.16em] text-white/35">
                      Target alignment
                    </div>

                    <div className="mt-2 text-2xl font-semibold">
                      {numberValue(
                        getMarketSummary(
                          selectedSnapshot,
                        )
                          .role_alignment_to_target,
                        numberValue(
                          selectedSnapshot.role_alignment_to_target,
                        ),
                      ) > 0
                        ? `${numberValue(
                            getMarketSummary(
                              selectedSnapshot,
                            )
                              .role_alignment_to_target,
                            numberValue(
                              selectedSnapshot.role_alignment_to_target,
                            ),
                          )}%`
                        : "—"}
                    </div>
                  </div>
                </div>

                <div>
                  <div className="text-xs uppercase tracking-[0.16em] text-white/35">
                    Contributing sources
                  </div>

                  <div className="mt-3 flex flex-wrap gap-2">
                    {stringList(
                      selectedSnapshot.sources,
                    ).map(
                      (
                        source,
                      ) => (
                        <span
                          key={source}
                          className="rounded-full border border-white/8 bg-white/[0.03] px-3 py-1.5 text-xs text-white/60"
                        >
                          {formatLabel(
                            source,
                          )}
                        </span>
                      ),
                    )}
                  </div>
                </div>

                <div>
                  <div className="text-xs uppercase tracking-[0.16em] text-white/35">
                    Market skills
                  </div>

                  <div className="mt-3 flex flex-wrap gap-2">
                    {getTopItems(
                      selectedSnapshot,
                      "top_market_skills",
                    )
                      .slice(
                        0,
                        20,
                      )
                      .map(
                        (
                          skill,
                        ) => (
                          <span
                            key={skill}
                            className="rounded-full border border-cyan-400/10 bg-cyan-400/5 px-3 py-1.5 text-xs text-cyan-100/70"
                          >
                            {formatLabel(
                              skill,
                            )}
                          </span>
                        ),
                      )}
                  </div>
                </div>

                <div>
                  <div className="text-xs uppercase tracking-[0.16em] text-white/35">
                    Priority gaps
                  </div>

                  <div className="mt-3 flex flex-wrap gap-2">
                    {stringList(
                      selectedSnapshot.priority_skill_gaps,
                    )
                      .slice(
                        0,
                        15,
                      )
                      .map(
                        (
                          gap,
                        ) => (
                          <span
                            key={gap}
                            className="rounded-full border border-amber-400/10 bg-amber-400/[0.03] px-3 py-1.5 text-xs text-amber-200/65"
                          >
                            {formatLabel(
                              gap,
                            )}
                          </span>
                        ),
                      )}
                  </div>
                </div>

                <div>
                  <div className="text-xs uppercase tracking-[0.16em] text-white/35">
                    Recommendations
                  </div>

                  <div className="mt-3 space-y-2">
                    {Array.isArray(
                      selectedSnapshot.recommendations,
                    ) &&
                    selectedSnapshot.recommendations.length >
                      0 ? (
                      selectedSnapshot.recommendations
                        .map(
                          (
                            item,
                            index,
                          ) => {
                            if (
                              typeof item ===
                              "string"
                            ) {
                              return (
                                <div
                                  key={`${item}-${index}`}
                                  className="rounded-2xl border border-white/8 bg-white/[0.02] p-4 text-sm text-white/65"
                                >
                                  {item}
                                </div>
                              );
                            }

                            if (
                              item &&
                              typeof item ===
                                "object"
                            ) {
                              const record =
                                item as Record<
                                  string,
                                  unknown
                                >;

                              const text =
                                stringValue(
                                  record.action,
                                ) ||
                                stringValue(
                                  record.reason,
                                ) ||
                                stringValue(
                                  record.title,
                                );

                              if (
                                text
                              ) {
                                return (
                                  <div
                                    key={`${text}-${index}`}
                                    className="rounded-2xl border border-white/8 bg-white/[0.02] p-4 text-sm text-white/65"
                                  >
                                    {text}
                                  </div>
                                );
                              }
                            }

                            return null;
                          },
                        )
                    ) : (
                      <p className="text-sm text-white/35">
                        No recommendations
                        recorded.
                      </p>
                    )}
                  </div>
                </div>

                <div className="rounded-2xl border border-white/8 bg-white/[0.02] p-4">
                  <div className="text-[10px] uppercase tracking-[0.16em] text-white/30">
                    Evidence
                  </div>

                  <div className="mt-2 text-sm leading-6 text-white/50">
                    Market signals shown here
                    are derived from the persisted
                    snapshot and its recorded
                    opportunity pool.
                  </div>
                </div>
              </div>
            </aside>
          </div>
        )}
      </main>
    </AppShell>
  );
}