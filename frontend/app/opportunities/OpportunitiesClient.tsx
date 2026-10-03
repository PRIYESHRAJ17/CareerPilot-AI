"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Bookmark,
  BookmarkCheck,
  BriefcaseBusiness,
  Copy,
  Check,
  ExternalLink,
  Filter,
  Loader2,
  MapPin,
  Search,
  SlidersHorizontal,
  Sparkles,
  X,
} from "lucide-react";
import {
  searchJobs,
  type JobResult,
} from "@/lib/api";
import {
  isValidHttpUrl,
  normalizeConfidence,
} from "@/lib/config";
import { formatSalaryRange } from "@/lib/formatters";
import {
  saveSearchResults,
} from "@/lib/workspace";
import {
  normalizeCommaList,
} from "@/lib/validation";
import { apiJson } from "@/lib/apiClient";
import { deleteWorkspace, listWorkspace, saveWorkspace } from "@/lib/productWorkspace";

const WORK_MODES = [
  ["remote", "Remote"],
  ["hybrid", "Hybrid"],
  ["on-site", "On-site"],
];

const SUGGESTED_ROLES = [
  "AI Engineer",
  "Full Stack Developer",
  "Backend Engineer",
  "Data Scientist",
];

const SUGGESTED_LOCATIONS = [
  "Bangalore",
  "Remote",
  "Hyderabad",
  "Pune",
];

function sanitizeSalaryInput(value: string): string {
  return value.replace(/[^0-9.]/g, "").replace(/(\..*)\./g, "$1");
}

function salaryLabel(job: JobResult) {
  if (!job.salary_disclosed) {
    return "Undisclosed";
  }

  return formatSalaryRange(
    job.salary_min_lpa,
    job.salary_max_lpa,
    "INR",
    typeof navigator !== "undefined" ? navigator.language : "en-IN",
  );
}

export default function OpportunitiesClient() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [role, setRole] = useState(
    () => searchParams.get("role") || searchParams.get("q") || "Software Engineer",
  );

  const [location, setLocation] = useState(
    () => searchParams.get("loc") || searchParams.get("location") || "",
  );

  const [experienceYears, setExperienceYears] = useState(0);

  const [minimumSalary, setMinimumSalary] = useState(
    () => searchParams.get("salary") || "",
  );

  const [skills, setSkills] = useState("");
  const [industries, setIndustries] = useState("");

  const [workModes, setWorkModes] = useState<string[]>([
    "remote",
    "hybrid",
    "on-site",
  ]);

  const [jobs, setJobs] = useState<JobResult[]>([]);
  const [selectedJob, setSelectedJob] = useState<JobResult | null>(null);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [careerTwinReady, setCareerTwinReady] = useState(false);

  // Sorting & Filtering
  const [sortBy, setSortBy] = useState<"match_desc" | "salary_desc" | "company_asc" | "title_asc">("match_desc");
  const [quickFilter, setQuickFilter] = useState<"all" | "remote" | "salary" | "strong" | "saved">("all");
  const [visibleCount, setVisibleCount] = useState(8);

  // Bookmarks
  const [bookmarkedIds, setBookmarkedIds] = useState<string[]>(() => {
    if (typeof window === "undefined") return [];
    try {
      return JSON.parse(window.localStorage.getItem("careerpilot.bookmarks") || "[]");
    } catch { return []; }
  });

  const [copiedLink, setCopiedLink] = useState(false);
  const [copiedBrief, setCopiedBrief] = useState(false);

  const lastSelectedId = useRef<string | null>(null);
  const searchController = useRef<AbortController | null>(null);
  const drawerCloseRef = useRef<HTMLButtonElement | null>(null);

  // Sync state into URL query
  const syncUrl = useCallback((jobId?: string | null) => {
    const params = new URLSearchParams();
    if (role.trim()) params.set("role", role.trim());
    if (location.trim()) params.set("location", location.trim());
    if (minimumSalary.trim()) params.set("salary", minimumSalary.trim());
    const id = jobId !== undefined ? jobId : selectedJob?.source_job_id;
    if (id) params.set("jobId", id);
    router.replace(`?${params.toString()}`, { scroll: false });
  }, [role, location, minimumSalary, selectedJob, router]);

  useEffect(() => {
    listWorkspace("saved-jobs").then((items) => {
      const ids = items.map((item) => String(item.source_job_id ?? item.id ?? "")).filter(Boolean);
      setBookmarkedIds(ids);
      window.localStorage.setItem("careerpilot.bookmarks", JSON.stringify(ids));
    }).catch(() => undefined);
  }, []);

  useEffect(() => {
    apiJson<{ profile?: { skills?: unknown } }>("/career-twin/session")
      .then((data) => {
        const values = data?.profile?.skills;
        if (Array.isArray(values) && values.length) {
          setSkills(
            values
              .filter((value): value is string => typeof value === "string")
              .join(", "),
          );
        }
        setCareerTwinReady(true);
      })
      .catch(() => setCareerTwinReady(false));
  }, []);

  // Auto-select job from URL query param on mount or update
  useEffect(() => {
    const targetJobId = searchParams.get("jobId");
    if (targetJobId && jobs.length) {
      const match = jobs.find((j) => j.source_job_id === targetJobId);
      if (match && selectedJob?.source_job_id !== targetJobId) {
        window.requestAnimationFrame(() => {
          setSelectedJob(match);
          lastSelectedId.current = `${match.source}:${match.source_job_id}`;
        });
      }
    }
  }, [jobs, searchParams, selectedJob]);

  // Drawer accessibility & keyboard trap
  useEffect(() => {
    if (!selectedJob) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        setSelectedJob(null);
        syncUrl(null);
        return;
      }

      if (event.key === "Tab") {
        const drawer = document.getElementById("opportunity-drawer");
        if (!drawer) return;

        const focusable = Array.from(
          drawer.querySelectorAll<HTMLElement>(
            'a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])',
          ),
        );
        if (!focusable.length) return;

        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    };

    document.addEventListener("keydown", onKeyDown);
    drawerCloseRef.current?.focus();

    return () => {
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [selectedJob, syncUrl]);

  function toggleMode(value: string) {
    setWorkModes((current) =>
      current.includes(value)
        ? current.filter((item) => item !== value)
        : [...current, value],
    );
  }

  function toggleBookmark(job: JobResult) {
    const id = job.source_job_id;
    const isSaved = bookmarkedIds.includes(id);
    setBookmarkedIds((prev) => {
      const next = isSaved ? prev.filter((item) => item !== id) : [...prev, id];
      window.localStorage.setItem("careerpilot.bookmarks", JSON.stringify(next));
      return next;
    });
    if (isSaved) {
      void deleteWorkspace("saved-jobs", `${job.source}:${job.source_job_id}`);
    } else {
      void saveWorkspace("saved-jobs", { ...job, saved_at: new Date().toISOString() }, `${job.source}:${job.source_job_id}`);
    }
  }

  function copyJobLink(job: JobResult) {
    if (typeof window === "undefined") return;
    const url = `${window.location.origin}/opportunities?jobId=${encodeURIComponent(job.source_job_id)}`;
    navigator.clipboard.writeText(url).then(() => {
      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 2000);
    });
  }

  function copyJobBrief(job: JobResult) {
    if (typeof window === "undefined") return;
    const brief = `${job.title} at ${job.company}\nLocation: ${(job.location || []).join(", ") || "Remote/Unspecified"}\nCompensation: ${salaryLabel(job)}\nMatch Score: ${Math.round(job.match_score ?? 0)}%\n\nWhy matched:\n${job.explanation || "Direct alignment with candidate profile."}`;
    navigator.clipboard.writeText(brief).then(() => {
      setCopiedBrief(true);
      setTimeout(() => setCopiedBrief(false), 2000);
    });
  }

  async function submitSearch() {
    if (role.trim().length < 2) {
      setError("Please enter at least 2 characters for the target role.");
      return;
    }

    const salary = minimumSalary.trim() ? Number(minimumSalary) : undefined;
    if (salary !== undefined && (!Number.isFinite(salary) || salary > 500)) {
      setError("Minimum salary must be between 0 and 500 LPA.");
      return;
    }

    searchController.current?.abort();
    const controller = new AbortController();
    searchController.current = controller;

    const previousId = selectedJob
      ? `${selectedJob.source}:${selectedJob.source_job_id}`
      : lastSelectedId.current;

    setLoading(true);
    setError("");
    setVisibleCount(8);

    try {
      const response = await searchJobs(
        {
          role: role.trim(),
          location: location.trim() || undefined,
          experience_years: experienceYears,
          minimum_salary_lpa: salary,
          preferred_work_modes: workModes,
          skills: normalizeCommaList(skills),
          target_industries: normalizeCommaList(industries),
        },
        controller.signal,
      );

      setJobs(response.results);
      setSearched(true);
      syncUrl(null);

      saveSearchResults(
        response.results,
        response.source_summary?.sources ?? [],
      );

      if (previousId) {
        const preserved =
          response.results.find(
            (job) => `${job.source}:${job.source_job_id}` === previousId,
          ) ?? null;

        setSelectedJob(preserved);
        lastSelectedId.current = previousId;
      }
    } catch (caught) {
      if (caught instanceof DOMException && caught.name === "AbortError") {
        return;
      }

      setError(
        caught instanceof Error
          ? caught.message
          : "CareerPilot could not complete the search.",
      );
    } finally {
      setLoading(false);
      searchController.current = null;
    }
  }

  // Filter & Sort calculation
  const filteredAndSortedJobs = useMemo(() => {
    let list = [...jobs];

    if (quickFilter === "remote") {
      list = list.filter((j) => j.remote || (j.location || []).some(l => l.toLowerCase().includes("remote")));
    } else if (quickFilter === "salary") {
      list = list.filter((j) => j.salary_disclosed);
    } else if (quickFilter === "strong") {
      list = list.filter((j) => (j.match_score ?? 0) >= 70 || j.decision === "APPLY_NOW" || j.decision === "GOOD_MATCH");
    } else if (quickFilter === "saved") {
      list = list.filter((j) => bookmarkedIds.includes(j.source_job_id));
    }

    list.sort((a, b) => {
      if (sortBy === "match_desc") return (b.match_score ?? 0) - (a.match_score ?? 0);
      if (sortBy === "salary_desc") return (b.salary_max_lpa ?? b.salary_min_lpa ?? 0) - (a.salary_max_lpa ?? a.salary_min_lpa ?? 0);
      if (sortBy === "company_asc") return a.company.localeCompare(b.company);
      if (sortBy === "title_asc") return a.title.localeCompare(b.title);
      return 0;
    });

    return list;
  }, [jobs, quickFilter, sortBy, bookmarkedIds]);

  const visibleJobs = useMemo(() => {
    return filteredAndSortedJobs.slice(0, visibleCount);
  }, [filteredAndSortedJobs, visibleCount]);

  return (
    <main className="min-h-screen bg-[#080a0f] p-5 text-white md:p-8">
      <div className="mx-auto max-w-7xl">
        <header className="border-b border-white/10 pb-7">
          <div className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
            <div>
              <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-white/60">
                <BriefcaseBusiness size={14} />
                Opportunity Intelligence
              </div>

              <h1 className="mt-3 text-4xl font-semibold tracking-tight">
                Live opportunities
              </h1>

              <p className="mt-3 max-w-2xl text-sm leading-6 text-white/70">
                Search the market. Understand where you fit. Search across connected job sources using your active Career Twin profile.
              </p>
            </div>

            <div className="rounded-2xl border border-white/10 px-4 py-3 text-xs text-white/70">
              {careerTwinReady ? "Career Twin connected" : "Career Twin not yet loaded"}
            </div>
          </div>

          {/* Quick Suggestion Chips */}
          <div className="mt-5 flex flex-wrap items-center gap-2 pt-2">
            <span className="text-xs text-white/50">Popular:</span>
            {SUGGESTED_ROLES.map((suggested) => (
              <button
                key={suggested}
                type="button"
                onClick={() => {
                  setRole(suggested);
                  setError("");
                }}
                className={`rounded-lg border px-2.5 py-1 text-xs transition ${
                  role === suggested
                    ? "border-cyan-400/50 bg-cyan-400/10 text-cyan-200"
                    : "border-white/10 bg-white/[0.02] text-white/70 hover:border-white/20"
                }`}
              >
                {suggested}
              </button>
            ))}
            <span className="ml-2 text-xs text-white/50">Locations:</span>
            {SUGGESTED_LOCATIONS.map((loc) => (
              <button
                key={loc}
                type="button"
                onClick={() => {
                  setLocation(loc);
                  setError("");
                }}
                className={`rounded-lg border px-2.5 py-1 text-xs transition ${
                  location === loc
                    ? "border-cyan-400/50 bg-cyan-400/10 text-cyan-200"
                    : "border-white/10 bg-white/[0.02] text-white/70 hover:border-white/20"
                }`}
              >
                {loc}
              </button>
            ))}
          </div>
        </header>

        <form
          className="mt-6 rounded-3xl border border-white/10 bg-white/[0.025] p-5"
          onSubmit={(event) => {
            event.preventDefault();
            void submitSearch();
          }}
        >
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <label htmlFor="opportunity-role" className="text-xs text-white/60">
              Role
              <input
                id="opportunity-role"
                value={role}
                onChange={(event) => {
                  setRole(event.target.value);
                  setError("");
                }}
                className="mt-2 w-full rounded-xl border border-white/10 bg-black/10 px-3 py-2.5 text-sm outline-none focus:border-white/30"
              />
            </label>

            <label htmlFor="opportunity-location" className="text-xs text-white/60">
              Location
              <input
                id="opportunity-location"
                value={location}
                placeholder="e.g. Bangalore, Remote"
                onChange={(event) => {
                  setLocation(event.target.value);
                  setError("");
                }}
                className="mt-2 w-full rounded-xl border border-white/10 bg-black/10 px-3 py-2.5 text-sm outline-none focus:border-white/30"
              />
            </label>

            <label htmlFor="opportunity-experience" className="text-xs text-white/60">
              Experience years
              <input
                id="opportunity-experience"
                type="number"
                min={0}
                step={0.1}
                value={experienceYears}
                onChange={(event) => {
                  setExperienceYears(Math.max(0, Number(event.target.value || 0)));
                  setError("");
                }}
                className="mt-2 w-full rounded-xl border border-white/10 bg-black/10 px-3 py-2.5 text-sm outline-none focus:border-white/30"
              />
            </label>

            <label htmlFor="opportunity-salary" className="text-xs text-white/60">
              Minimum salary (LPA)
              <input
                id="opportunity-salary"
                inputMode="decimal"
                value={minimumSalary}
                placeholder="e.g. 15"
                onChange={(event) => {
                  setMinimumSalary(sanitizeSalaryInput(event.target.value));
                  setError("");
                }}
                className="mt-2 w-full rounded-xl border border-white/10 bg-black/10 px-3 py-2.5 text-sm outline-none focus:border-white/30"
              />
            </label>

            <label htmlFor="opportunity-skills" className="text-xs text-white/60">
              Skills
              <input
                id="opportunity-skills"
                value={skills}
                onChange={(event) => {
                  setSkills(event.target.value);
                  setError("");
                }}
                placeholder="Python, SQL, React"
                className="mt-2 w-full rounded-xl border border-white/10 bg-black/10 px-3 py-2.5 text-sm outline-none focus:border-white/30"
              />
            </label>

            <label htmlFor="opportunity-industries" className="text-xs text-white/60">
              Industries
              <input
                id="opportunity-industries"
                value={industries}
                onChange={(event) => {
                  setIndustries(event.target.value);
                  setError("");
                }}
                placeholder="Leave empty for cross-industry"
                className="mt-2 w-full rounded-xl border border-white/10 bg-black/10 px-3 py-2.5 text-sm outline-none focus:border-white/30"
              />
            </label>
          </div>

          <div className="mt-5">
            <div className="mb-2 text-xs text-white/60">Work mode</div>
            <div className="flex flex-wrap gap-2">
              {WORK_MODES.map(([value, label]) => (
                <label
                  key={value}
                  className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.02] px-3 py-2 text-xs text-white/70 hover:border-white/20"
                >
                  <input
                    type="checkbox"
                    checked={workModes.includes(value)}
                    onChange={() => toggleMode(value)}
                  />
                  {label}
                </label>
              ))}
            </div>
          </div>

          <div className="sr-only" aria-live="polite">
            {loading ? "Searching opportunities..." : searched ? `${jobs.length} opportunities loaded.` : ""}
          </div>

          {error && (
            <div className="mt-5 rounded-2xl border border-red-400/15 bg-red-400/[0.04] p-4 text-sm text-red-100/90">
              {error}
            </div>
          )}

          <div className="mt-5 flex justify-end">
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-xl bg-white px-5 py-2.5 text-xs font-semibold text-black transition hover:bg-white/90 disabled:opacity-50"
            >
              {loading ? <Loader2 size={15} className="animate-spin" /> : <Search size={15} />}
              {loading ? "Searching..." : "Search market"}
            </button>
          </div>
        </form>

        {/* Sort & Filter Toolbar */}
        {jobs.length > 0 && (
          <div className="mt-6 flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-white/10 bg-white/[0.02] p-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="flex items-center gap-1.5 text-xs text-white/50">
                <Filter size={13} />
                Filter:
              </span>
              {[
                ["all", "All"],
                ["remote", "Remote only"],
                ["salary", "Disclosed salary"],
                ["strong", "Top matches (70%+)"],
                ["saved", `Saved (${bookmarkedIds.length})`],
              ].map(([key, label]) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => {
                    setQuickFilter(key as typeof quickFilter);
                    setVisibleCount(8);
                  }}
                  className={`rounded-lg border px-2.5 py-1 text-xs transition ${
                    quickFilter === key
                      ? "border-white/30 bg-white/10 text-white"
                      : "border-white/10 bg-white/[0.01] text-white/60 hover:border-white/20"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2">
              <span className="flex items-center gap-1.5 text-xs text-white/50">
                <SlidersHorizontal size={13} />
                Sort:
              </span>
              <select
                aria-label="Sort opportunities"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
                className="rounded-lg border border-white/10 bg-black/20 px-2.5 py-1 text-xs text-white/80 outline-none"
              >
                <option value="match_desc">Highest Match Score</option>
                <option value="salary_desc">Highest Salary</option>
                <option value="company_asc">Company (A–Z)</option>
                <option value="title_asc">Role Title (A–Z)</option>
              </select>
            </div>
          </div>
        )}

        {/* Opportunities List */}
        <section className="mt-6">
          {!searched && !loading ? (
            <div className="rounded-3xl border border-dashed border-white/10 p-10 text-center text-sm text-white/50">
              Search to populate live canonical opportunities.
            </div>
          ) : loading ? (
            <div className="space-y-3">
              {Array.from({ length: 6 }, (_, index) => (
                <div
                  key={`skeleton-${index}`}
                  className="h-32 animate-pulse rounded-3xl border border-white/8 bg-white/[0.02]"
                />
              ))}
            </div>
          ) : filteredAndSortedJobs.length === 0 ? (
            <div className="rounded-3xl border border-dashed border-white/10 p-8 text-center text-sm text-white/50">
              No opportunities match the selected filters. Try changing filters or refining your query.
            </div>
          ) : (
            <div className="space-y-3">
              {visibleJobs.map((job) => {
                const isBookmarked = bookmarkedIds.includes(job.source_job_id);

                return (
                  <article
                    key={`${job.source}-${job.source_job_id}`}
                    aria-labelledby={`job-title-${job.source_job_id}`}
                    className="rounded-3xl border border-white/10 bg-white/[0.025] p-5 transition hover:border-white/20"
                  >
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedJob(job);
                          lastSelectedId.current = `${job.source}:${job.source_job_id}`;
                          syncUrl(job.source_job_id);
                        }}
                        className="min-w-0 flex-1 text-left"
                      >
                        <div className="flex items-start gap-4">
                          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.04] text-xs font-semibold">
                            {job.company?.slice(0, 2).toUpperCase() || "CP"}
                          </div>

                          <div className="min-w-0">
                            <div className="text-xs uppercase tracking-[0.18em] text-white/60">
                              {job.company}
                            </div>

                            <h2 id={`job-title-${job.source_job_id}`} className="mt-1 truncate text-lg font-semibold">
                              {job.title}
                            </h2>

                            <div className="mt-2 flex flex-wrap gap-3 text-xs text-white/60">
                              <span>
                                <MapPin size={12} className="mr-1 inline" />
                                {(job.location || []).filter(Boolean).join(", ") || "Location not specified"}
                              </span>

                              <span>{salaryLabel(job)}</span>
                            </div>
                          </div>
                        </div>
                      </button>

                      <div className="flex items-center gap-3">
                        <button
                          type="button"
                          aria-label={isBookmarked ? "Remove bookmark" : "Save opportunity"}
                          onClick={() => toggleBookmark(job)}
                          className={`rounded-xl border p-2 transition ${
                            isBookmarked
                              ? "border-cyan-400/40 bg-cyan-400/10 text-cyan-300"
                              : "border-white/10 text-white/40 hover:text-white/80"
                          }`}
                        >
                          {isBookmarked ? <BookmarkCheck size={16} /> : <Bookmark size={16} />}
                        </button>

                        <span className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs font-medium text-white/80">
                          {Math.round(job.match_score ?? 0)}% match
                        </span>

                        <button
                          type="button"
                          aria-label={`Analyze match for ${job.title} at ${job.company}`}
                          onClick={() => {
                            setSelectedJob(job);
                            lastSelectedId.current = `${job.source}:${job.source_job_id}`;
                            syncUrl(job.source_job_id);
                          }}
                          className="rounded-xl border border-white/10 px-3.5 py-2 text-xs font-medium text-white/80 transition hover:bg-white/10"
                        >
                          Analyze
                        </button>

                        {isValidHttpUrl(job.apply_url) ? (
                          <a
                            href={job.apply_url}
                            target="_blank"
                            rel="noreferrer"
                            aria-label={`Apply for ${job.title} at ${job.company} (opens in new tab)`}
                            className="inline-flex items-center gap-1.5 rounded-xl bg-white px-3.5 py-2 text-xs font-semibold text-black transition hover:bg-white/90"
                          >
                            Apply
                            <ExternalLink size={12} />
                          </a>
                        ) : (
                          <button
                            type="button"
                            disabled
                            className="rounded-xl border border-white/10 px-3 py-2 text-xs text-white/50"
                          >
                            Apply unavailable
                          </button>
                        )}
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          )}

          {/* Pagination Load More Button */}
          {visibleCount < filteredAndSortedJobs.length && (
            <div className="mt-8 flex flex-col items-center justify-center gap-2">
              <p className="text-xs text-white/50">
                Showing {visibleJobs.length} of {filteredAndSortedJobs.length} opportunities
              </p>
              <button
                type="button"
                onClick={() => setVisibleCount((prev) => prev + 8)}
                className="rounded-xl border border-white/15 bg-white/[0.03] px-6 py-2.5 text-xs font-semibold text-white/80 transition hover:bg-white/10"
              >
                Load more opportunities
              </button>
            </div>
          )}
        </section>

        {/* Intelligence Drawer */}
        {selectedJob && (
          <div
            id="opportunity-drawer"
            role="dialog"
            aria-modal="true"
            aria-label={`Opportunity analysis for ${selectedJob.title}`}
            className="fixed inset-0 z-50 flex justify-end bg-black/70 backdrop-blur-sm"
          >
            <aside className="relative flex h-full w-full max-w-xl flex-col overflow-y-auto border-l border-white/10 bg-[#0d1017] p-6 shadow-2xl">
              <div className="flex items-center justify-between border-b border-white/10 pb-4">
                <span className="text-xs uppercase tracking-[0.2em] text-white/50">
                  Opportunity Analysis
                </span>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => copyJobLink(selectedJob)}
                    className="inline-flex items-center gap-1.5 rounded-xl border border-white/10 px-3 py-1.5 text-xs text-white/70 transition hover:bg-white/5"
                  >
                    {copiedLink ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
                    {copiedLink ? "Link copied" : "Copy link"}
                  </button>

                  <button
                    ref={drawerCloseRef}
                    type="button"
                    aria-label="Close analysis"
                    onClick={() => {
                      setSelectedJob(null);
                      syncUrl(null);
                    }}
                    className="min-h-11 min-w-11 rounded-xl border border-white/10 p-2 text-white/70 transition hover:text-white"
                  >
                    <X size={16} />
                  </button>
                </div>
              </div>

              <div className="mt-6 flex items-start gap-4">
                <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.04] text-sm font-semibold">
                  {selectedJob.company?.slice(0, 2).toUpperCase() || "CP"}
                </div>

                <div>
                  <h2 className="text-xl font-semibold">{selectedJob.title}</h2>
                  <div className="mt-1 text-sm text-white/60">{selectedJob.company}</div>
                  <div className="mt-2 text-xs text-white/50">
                    {(selectedJob.location || []).filter(Boolean).join(", ") || "Location not specified"}
                  </div>
                </div>
              </div>

              <section className="mt-6 rounded-3xl border border-white/10 bg-white/[0.025] p-5">
                <div className="text-xs uppercase tracking-[0.16em] text-white/50">Match fit</div>
                <div className="mt-2 text-5xl font-semibold">{Math.round(selectedJob.match_score ?? 0)}%</div>
                <div className="mt-1 text-xs text-white/50">
                  {normalizeConfidence(selectedJob.confidence)}% confidence score
                </div>
              </section>

              <section className="mt-5 rounded-3xl border border-white/10 bg-white/[0.025] p-5">
                <div className="text-xs uppercase tracking-[0.16em] text-white/50">Why this opportunity</div>
                <p className="mt-3 text-sm leading-7 text-white/70">
                  {selectedJob.explanation || "CareerPilot matched role, skill, experience, location and salary evidence."}
                </p>
              </section>

              <section className="mt-5 rounded-3xl border border-white/10 bg-white/[0.025] p-5">
                <div className="text-xs uppercase tracking-[0.16em] text-white/50">Compensation</div>
                <div className="mt-3 text-sm text-white/80">{salaryLabel(selectedJob)}</div>
                {selectedJob.salary_status === "BELOW_TARGET" && (
                  <div className="mt-2 text-xs text-amber-200/90">Below the requested minimum salary target.</div>
                )}
              </section>

              <div className="mt-6 flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={() => {
                    if (typeof window !== "undefined") {
                      const loc = Array.isArray(selectedJob.location) ? selectedJob.location.join(", ") : String(selectedJob.location);
                      const brief = `${selectedJob.title} at ${selectedJob.company}\nLocation: ${loc}\nSalary: ${formatSalaryRange(selectedJob.salary_min_lpa, selectedJob.salary_max_lpa)}\n\nMatched Skills:\n${(selectedJob.matched_skills ?? []).join(", ")}\n\nDetails:\n${selectedJob.explanation || ""}\n${selectedJob.salary_evidence || ""}`;
                      window.sessionStorage.setItem("careerpilot.target_jd", brief);
                      router.push(`/resume?role=${encodeURIComponent(selectedJob.title)}&company=${encodeURIComponent(selectedJob.company)}`);
                    }
                  }}
                  className="inline-flex items-center gap-1.5 rounded-xl border border-cyan-500/30 bg-cyan-500/10 px-4 py-2.5 text-xs font-medium text-cyan-300 transition hover:bg-cyan-500/20"
                >
                  <Sparkles size={13} />
                  Match with resume
                </button>

                <button
                  type="button"
                  onClick={() => copyJobBrief(selectedJob)}
                  className="rounded-xl border border-white/10 px-4 py-2.5 text-xs text-white/80 transition hover:bg-white/5"
                >
                  {copiedBrief ? "Summary copied!" : "Copy job summary"}
                </button>

                {isValidHttpUrl(selectedJob.apply_url) ? (
                  <a
                    href={selectedJob.apply_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-2 rounded-xl bg-white px-5 py-2.5 text-xs font-semibold text-black transition hover:bg-white/90"
                  >
                    Apply on company website
                    <ExternalLink size={13} />
                  </a>
                ) : (
                  <button
                    type="button"
                    disabled
                    className="rounded-xl border border-white/10 px-4 py-2.5 text-xs text-white/50"
                  >
                    Direct apply unavailable
                  </button>
                )}
              </div>
            </aside>
          </div>
        )}
      </div>
    </main>
  );
}
