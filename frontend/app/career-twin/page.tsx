export default function CareerTwinPage() {
  return (
    <main className="min-h-screen bg-[#080a0f] p-10 text-white">
      <div className="mx-auto max-w-5xl">
        <p className="text-xs uppercase tracking-[0.2em] text-white/30">
          CareerPilot Intelligence
        </p>

        <h1 className="mt-3 text-4xl font-semibold tracking-tight">
          Career Twin
        </h1>

        <p className="mt-4 max-w-2xl text-sm leading-6 text-white/45">
          Your evolving AI representation of skills, experience,
          goals, preferences and career readiness.
        </p>

        <div className="mt-10 grid gap-4 md:grid-cols-3">
          <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
            <div className="text-xs uppercase tracking-[0.16em] text-white/30">
              Skill profile
            </div>

            <div className="mt-3 text-xl font-semibold">
              Capability map
            </div>

            <p className="mt-2 text-sm leading-6 text-white/35">
              CareerPilot will continuously model your technical
              and professional capabilities.
            </p>
          </div>

          <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
            <div className="text-xs uppercase tracking-[0.16em] text-white/30">
              Career goals
            </div>

            <div className="mt-3 text-xl font-semibold">
              Target trajectory
            </div>

            <p className="mt-2 text-sm leading-6 text-white/35">
              Your target roles, industries and preferences will
              become part of the career model.
            </p>
          </div>

          <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
            <div className="text-xs uppercase tracking-[0.16em] text-white/30">
              Readiness
            </div>

            <div className="mt-3 text-xl font-semibold">
              Career readiness
            </div>

            <p className="mt-2 text-sm leading-6 text-white/35">
              CareerPilot will estimate where you are strongest and
              where targeted improvement can create the most impact.
            </p>
          </div>
        </div>

        <div className="mt-6 rounded-3xl border border-white/10 bg-white/[0.025] p-8">
          <div className="text-sm font-medium text-white/75">
            Your Career Twin
          </div>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-white/35">
            This will become the central profile layer used by the
            job, resume, interview and career-planning agents.
          </p>

          <div className="mt-6 inline-flex rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[10px] uppercase tracking-[0.16em] text-white/35">
            Coming in later weeks
          </div>
        </div>
      </div>
    </main>
  );
}