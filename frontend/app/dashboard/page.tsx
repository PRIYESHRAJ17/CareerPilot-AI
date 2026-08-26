export default function DashboardPage() {
  return (
    <main className="min-h-screen bg-[#080a0f] p-10 text-white">
      <div className="mx-auto max-w-6xl">
        <p className="text-xs uppercase tracking-[0.2em] text-white/30">
          CareerPilot Overview
        </p>

        <div className="mt-3 flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div>
            <h1 className="text-4xl font-semibold tracking-tight">
              Your Career Command Center
            </h1>

            <p className="mt-4 max-w-2xl text-sm leading-6 text-white/45">
              A unified view of your opportunities, career readiness,
              applications and next best actions.
            </p>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3">
            <div className="text-[10px] uppercase tracking-[0.16em] text-white/30">
              Profile status
            </div>

            <div className="mt-1 text-sm font-medium text-white/80">
              Foundation profile
            </div>
          </div>
        </div>

        {/* Overview cards */}
        <div className="mt-10 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
            <div className="text-xs uppercase tracking-[0.16em] text-white/30">
              Opportunities
            </div>

            <div className="mt-3 text-3xl font-semibold">
              15
            </div>

            <p className="mt-2 text-sm text-white/35">
              Live roles matched across connected sources.
            </p>
          </div>

          <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
            <div className="text-xs uppercase tracking-[0.16em] text-white/30">
              Strong matches
            </div>

            <div className="mt-3 text-3xl font-semibold">
              6
            </div>

            <p className="mt-2 text-sm text-white/35">
              Opportunities currently scoring 80+.
            </p>
          </div>

          <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
            <div className="text-xs uppercase tracking-[0.16em] text-white/30">
              Skill signals
            </div>

            <div className="mt-3 text-3xl font-semibold">
              4
            </div>

            <p className="mt-2 text-sm text-white/35">
              Skills currently represented in your profile.
            </p>
          </div>

          <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
            <div className="text-xs uppercase tracking-[0.16em] text-white/30">
              Applications
            </div>

            <div className="mt-3 text-3xl font-semibold">
              0
            </div>

            <p className="mt-2 text-sm text-white/35">
              Your application workspace is ready to grow.
            </p>
          </div>
        </div>

        {/* Main dashboard */}
        <div className="mt-6 grid gap-4 xl:grid-cols-[1.4fr_1fr]">
          <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-7">
            <div className="text-xs uppercase tracking-[0.16em] text-white/30">
              Next best action
            </div>

            <h2 className="mt-3 text-2xl font-semibold">
              Explore your strongest opportunities
            </h2>

            <p className="mt-3 max-w-2xl text-sm leading-6 text-white/40">
              CareerPilot will eventually prioritize what you should
              do next based on your goals, match quality, deadlines,
              skill gaps and career trajectory.
            </p>

            <a
              href="/opportunities"
              className="mt-6 inline-flex rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-black transition hover:bg-white/90"
            >
              Open opportunities
            </a>
          </section>

          <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-7">
            <div className="text-xs uppercase tracking-[0.16em] text-white/30">
              Career trajectory
            </div>

            <h2 className="mt-3 text-2xl font-semibold">
              Building your Career Twin
            </h2>

            <p className="mt-3 text-sm leading-6 text-white/40">
              Your profile, goals and market signals will eventually
              power a continuously evolving career model.
            </p>

            <a
              href="/career-twin"
              className="mt-6 inline-flex rounded-xl border border-white/10 px-4 py-2.5 text-sm font-medium text-white/70 transition hover:border-white/20 hover:text-white"
            >
              View Career Twin
            </a>
          </section>
        </div>

        {/* Activity */}
        <section className="mt-6 rounded-3xl border border-white/10 bg-white/[0.025] p-7">
          <div className="text-xs uppercase tracking-[0.16em] text-white/30">
            Recent activity
          </div>

          <div className="mt-5 space-y-3">
            <div className="rounded-2xl border border-white/8 bg-black/10 p-4">
              <div className="text-sm font-medium">
                Live job intelligence connected
              </div>

              <div className="mt-1 text-xs text-white/35">
                Adzuna and Jooble are currently feeding the
                opportunity engine.
              </div>
            </div>

            <div className="rounded-2xl border border-white/8 bg-black/10 p-4">
              <div className="text-sm font-medium">
                Hybrid matching active
              </div>

              <div className="mt-1 text-xs text-white/35">
                Deterministic and semantic evidence are being combined
                for job recommendations.
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}