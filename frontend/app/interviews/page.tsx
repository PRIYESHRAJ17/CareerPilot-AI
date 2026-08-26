export default function InterviewsPage() {
  return (
    <main className="min-h-screen bg-[#080a0f] p-10 text-white">
      <div className="mx-auto max-w-5xl">
        <p className="text-xs uppercase tracking-[0.2em] text-white/30">
          CareerPilot Intelligence
        </p>

        <h1 className="mt-3 text-4xl font-semibold tracking-tight">
          Interviews
        </h1>

        <p className="mt-4 max-w-2xl text-sm leading-6 text-white/45">
          Prepare for interviews with role-specific questions,
          adaptive practice, feedback and readiness analysis.
        </p>

        <div className="mt-10 grid gap-4 md:grid-cols-3">
          <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
            <div className="text-xs uppercase tracking-[0.16em] text-white/30">
              Preparation
            </div>

            <div className="mt-3 text-xl font-semibold">
              Role-specific practice
            </div>

            <p className="mt-2 text-sm leading-6 text-white/35">
              CareerPilot will generate interview preparation based
              on the role, company and candidate profile.
            </p>
          </div>

          <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
            <div className="text-xs uppercase tracking-[0.16em] text-white/30">
              Mock interview
            </div>

            <div className="mt-3 text-xl font-semibold">
              Adaptive interview agent
            </div>

            <p className="mt-2 text-sm leading-6 text-white/35">
              Practice conversations will adapt based on your
              answers, strengths and weaknesses.
            </p>
          </div>

          <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
            <div className="text-xs uppercase tracking-[0.16em] text-white/30">
              Readiness
            </div>

            <div className="mt-3 text-xl font-semibold">
              Interview readiness
            </div>

            <p className="mt-2 text-sm leading-6 text-white/35">
              CareerPilot will identify weak areas and recommend the
              highest-impact preparation before an interview.
            </p>
          </div>
        </div>

        <div className="mt-6 rounded-3xl border border-white/10 bg-white/[0.025] p-8">
          <div className="text-sm font-medium text-white/75">
            Interview Intelligence
          </div>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-white/35">
            This workspace will become the adaptive interview layer
            of CareerPilot, connected directly to your career profile
            and target opportunities.
          </p>

          <div className="mt-6 inline-flex rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[10px] uppercase tracking-[0.16em] text-white/35">
            Coming in later weeks
          </div>
        </div>
      </div>
    </main>
  );
}