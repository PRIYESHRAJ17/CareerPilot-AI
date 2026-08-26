"use client";

import {
  BriefcaseBusiness,
  Building2,
  CalendarDays,
  ChevronDown,
  CircleUserRound,
  FileText,
  Gauge,
  LayoutDashboard,
  MessageSquareText,
  Moon,
  Search,
  Settings,
  Sparkles,
  Target,
  UserRound,
} from "lucide-react";

const navItems = [
  {
    label: "Dashboard",
    icon: LayoutDashboard,
    active: false,
  },
  {
    label: "Opportunities",
    icon: BriefcaseBusiness,
    active: true,
  },
  {
    label: "Career Twin",
    icon: Target,
    active: false,
  },
  {
    label: "Resume",
    icon: FileText,
    active: false,
  },
  {
    label: "Companies",
    icon: Building2,
    active: false,
  },
  {
    label: "Interviews",
    icon: MessageSquareText,
    active: false,
  },
  {
    label: "Applications",
    icon: CalendarDays,
    active: false,
  },
];

const quickStats = [
  {
    label: "Live opportunities",
    value: "15",
    detail: "Across 2 sources",
  },
  {
    label: "Strong matches",
    value: "6",
    detail: "80+ compatibility",
  },
  {
    label: "New today",
    value: "9",
    detail: "Fresh listings",
  },
];

const opportunities = [
  {
    company: "PhonePe",
    role: "Software Engineer — Backend",
    location: "Bangalore",
    mode: "On-site",
    score: 92,
    decision: "Strong match",
    sourceCount: 1,
    skills: ["Python", "SQL", "Backend"],
  },
  {
    company: "Suki",
    role: "Software Engineer III — Backend",
    location: "Bangalore",
    mode: "On-site",
    score: 84,
    decision: "Good match",
    sourceCount: 1,
    skills: ["Python", "APIs", "Backend"],
  },
  {
    company: "ABB",
    role: "Software Engineer",
    location: "Bangalore",
    mode: "Hybrid",
    score: 81,
    decision: "Good match",
    sourceCount: 1,
    skills: ["Software", "Engineering", "Git"],
  },
];

export default function Home() {
  return (
    <main className="min-h-screen bg-[#080a0f] text-white">
      <div className="flex min-h-screen">
        {/* Sidebar */}
        <aside className="hidden w-[260px] shrink-0 border-r border-white/8 bg-[#0b0e14] lg:flex lg:flex-col">
          <div className="flex h-20 items-center gap-3 border-b border-white/8 px-6">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white text-black">
              <Sparkles size={18} strokeWidth={2.2} />
            </div>

            <div>
              <div className="text-[15px] font-semibold tracking-tight">
                CareerPilot
              </div>
              <div className="text-[10px] uppercase tracking-[0.22em] text-white/35">
                AI Career OS
              </div>
            </div>
          </div>

          <div className="px-4 pt-6">
            <div className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-[0.2em] text-white/30">
              Workspace
            </div>

            <nav className="space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon;

                return (
                  <button
                    key={item.label}
                    className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm transition ${
                      item.active
                        ? "bg-white text-black shadow-[0_10px_30px_rgba(255,255,255,0.07)]"
                        : "text-white/55 hover:bg-white/5 hover:text-white"
                    }`}
                  >
                    <Icon size={17} />
                    <span>{item.label}</span>

                    {item.label === "Career Twin" && (
                      <span className="ml-auto rounded-full bg-white/8 px-2 py-0.5 text-[9px] uppercase tracking-wider text-white/35">
                        Soon
                      </span>
                    )}
                  </button>
                );
              })}
            </nav>
          </div>

          <div className="mt-auto border-t border-white/8 p-4">
            <button className="flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm text-white/50 hover:bg-white/5 hover:text-white">
              <Settings size={17} />
              Settings
            </button>

            <div className="mt-3 flex items-center gap-3 rounded-2xl border border-white/8 bg-white/[0.03] p-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/10">
                <UserRound size={16} />
              </div>

              <div className="min-w-0">
                <div className="truncate text-sm font-medium">
                  Your Career Profile
                </div>
                <div className="text-[11px] text-white/35">
                  4 skills tracked
                </div>
              </div>

              <ChevronDown
                className="ml-auto text-white/30"
                size={15}
              />
            </div>
          </div>
        </aside>

        {/* Main workspace */}
        <section className="flex min-w-0 flex-1 flex-col">
          {/* Header */}
          <header className="flex h-20 items-center justify-between border-b border-white/8 px-5 md:px-8">
            <div className="flex min-w-0 items-center gap-3">
              <div className="lg:hidden">
                <button className="rounded-xl border border-white/10 p-2.5">
                  <Gauge size={18} />
                </button>
              </div>

              <div>
                <div className="text-[11px] uppercase tracking-[0.2em] text-white/30">
                  Opportunities
                </div>
                <h1 className="text-xl font-semibold tracking-tight md:text-2xl">
                  Find roles worth your time.
                </h1>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button className="hidden rounded-xl border border-white/10 p-2.5 text-white/55 transition hover:bg-white/5 hover:text-white sm:block">
                <Moon size={17} />
              </button>

              <button className="rounded-xl border border-white/10 p-2.5 text-white/55 transition hover:bg-white/5 hover:text-white">
                <CircleUserRound size={17} />
              </button>
            </div>
          </header>

          {/* Content */}
          <div className="flex-1 overflow-y-auto">
            <div className="mx-auto max-w-[1500px] px-5 py-6 md:px-8 md:py-8">
              {/* Hero/search */}
              <div className="overflow-hidden rounded-[28px] border border-white/10 bg-[radial-gradient(circle_at_top_right,rgba(255,255,255,0.10),transparent_35%),linear-gradient(135deg,#11151d,#0b0d12)] p-6 md:p-8">
                <div className="max-w-3xl">
                  <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[10px] uppercase tracking-[0.18em] text-white/55">
                    <Sparkles size={12} />
                    Career intelligence
                  </div>

                  <h2 className="text-3xl font-semibold leading-tight tracking-[-0.03em] md:text-5xl">
                    Search the market.
                    <br />
                    <span className="text-white/45">
                      Understand where you fit.
                    </span>
                  </h2>

                  <p className="mt-4 max-w-2xl text-sm leading-6 text-white/45 md:text-base">
                    CareerPilot combines live job discovery with
                    candidate-specific matching, skill-gap analysis and
                    explainable recommendations.
                  </p>
                </div>

                <div className="mt-7 grid gap-3 lg:grid-cols-[1.5fr_1fr_1fr_auto]">
                  <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-black/20 px-4 py-3.5">
                    <Search
                      size={18}
                      className="shrink-0 text-white/35"
                    />
                    <div>
                      <div className="text-[10px] uppercase tracking-wider text-white/30">
                        Role
                      </div>
                      <div className="mt-0.5 text-sm text-white/80">
                        Software Engineer
                      </div>
                    </div>
                  </div>

                  <div className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3.5">
                    <div className="text-[10px] uppercase tracking-wider text-white/30">
                      Location
                    </div>
                    <div className="mt-0.5 text-sm text-white/80">
                      Bangalore
                    </div>
                  </div>

                  <div className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3.5">
                    <div className="text-[10px] uppercase tracking-wider text-white/30">
                      Minimum salary
                    </div>
                    <div className="mt-0.5 text-sm text-white/80">
                      ₹6 LPA
                    </div>
                  </div>

                  <button className="rounded-2xl bg-white px-6 py-3.5 text-sm font-semibold text-black transition hover:bg-white/90">
                    Find matches
                  </button>
                </div>
              </div>

              {/* Stats */}
              <div className="mt-6 grid gap-3 md:grid-cols-3">
                {quickStats.map((stat) => (
                  <div
                    key={stat.label}
                    className="rounded-2xl border border-white/8 bg-white/[0.025] p-5"
                  >
                    <div className="text-[11px] uppercase tracking-[0.17em] text-white/30">
                      {stat.label}
                    </div>
                    <div className="mt-2 text-3xl font-semibold tracking-tight">
                      {stat.value}
                    </div>
                    <div className="mt-1 text-xs text-white/35">
                      {stat.detail}
                    </div>
                  </div>
                ))}
              </div>

              {/* Opportunities */}
              <div className="mt-8">
                <div className="flex items-end justify-between gap-4">
                  <div>
                    <div className="text-[11px] uppercase tracking-[0.2em] text-white/30">
                      Recommended
                    </div>
                    <h3 className="mt-1 text-xl font-semibold tracking-tight">
                      Opportunities for you
                    </h3>
                  </div>

                  <button className="text-xs font-medium text-white/45 hover:text-white">
                    View all
                  </button>
                </div>

                <div className="mt-4 space-y-3">
                  {opportunities.map((job) => (
                    <article
                      key={`${job.company}-${job.role}`}
                      className="group rounded-[24px] border border-white/8 bg-white/[0.02] p-5 transition hover:border-white/15 hover:bg-white/[0.035]"
                    >
                      <div className="flex flex-col gap-5 xl:flex-row xl:items-center">
                        <div className="flex min-w-0 flex-1 items-start gap-4">
                          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.04] text-sm font-semibold">
                            {job.company
                              .slice(0, 2)
                              .toUpperCase()}
                          </div>

                          <div className="min-w-0">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="text-[11px] uppercase tracking-[0.16em] text-white/30">
                                {job.company}
                              </span>

                              <span className="rounded-full border border-white/8 px-2 py-0.5 text-[9px] uppercase tracking-wider text-white/30">
                                {job.sourceCount} source
                              </span>
                            </div>

                            <h4 className="mt-1 truncate text-base font-semibold">
                              {job.role}
                            </h4>

                            <div className="mt-2 flex flex-wrap gap-2 text-xs text-white/35">
                              <span>{job.location}</span>
                              <span>•</span>
                              <span>{job.mode}</span>
                            </div>

                            <div className="mt-3 flex flex-wrap gap-2">
                              {job.skills.map((skill) => (
                                <span
                                  key={skill}
                                  className="rounded-full bg-white/5 px-2.5 py-1 text-[10px] text-white/45"
                                >
                                  {skill}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center justify-between gap-4 xl:justify-end">
                          <div className="min-w-[110px]">
                            <div className="text-[10px] uppercase tracking-[0.18em] text-white/30">
                              Match
                            </div>

                            <div className="mt-1 flex items-baseline gap-1">
                              <span className="text-3xl font-semibold tracking-tight">
                                {job.score}
                              </span>
                              <span className="text-xs text-white/30">
                                /100
                              </span>
                            </div>

                            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/8">
                              <div
                                className="h-full rounded-full bg-white"
                                style={{
                                  width: `${job.score}%`,
                                }}
                              />
                            </div>
                          </div>

                          <div className="text-right">
                            <div className="text-[10px] uppercase tracking-[0.16em] text-white/30">
                              Recommendation
                            </div>

                            <div className="mt-1 text-sm font-medium text-white/80">
                              {job.decision}
                            </div>
                          </div>

                          <button className="rounded-xl border border-white/10 px-4 py-2.5 text-xs font-medium text-white/70 transition group-hover:border-white/20 group-hover:text-white">
                            Analyze
                          </button>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}