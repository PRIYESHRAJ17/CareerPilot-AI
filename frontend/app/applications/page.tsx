export default function ApplicationsPage() {
  return (
    <main className="min-h-screen bg-[#080a0f] p-10 text-white">
      <div className="mx-auto max-w-5xl">
        <p className="text-xs uppercase tracking-[0.2em] text-white/30">
          CareerPilot Workspace
        </p>

        <h1 className="mt-3 text-4xl font-semibold tracking-tight">
          Applications
        </h1>

        <p className="mt-4 max-w-2xl text-sm leading-6 text-white/45">
          Track applications, interview stages, follow-ups and outcomes
          across your career journey.
        </p>

        <div className="mt-10 rounded-3xl border border-white/10 bg-white/[0.025] p-8">
          <div className="text-sm font-medium text-white/70">
            Application Intelligence
          </div>

          <div className="mt-2 text-sm text-white/35">
            This workspace will become active as CareerPilot adds
            application tracking and automation.
          </div>

          <div className="mt-6 inline-flex rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[10px] uppercase tracking-[0.16em] text-white/35">
            Coming in later weeks
          </div>
        </div>
      </div>
    </main>
  );
}