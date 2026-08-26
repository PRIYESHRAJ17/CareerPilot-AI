export default function CompaniesPage() {
  return (
    <main className="min-h-screen bg-[#080a0f] p-10 text-white">
      <div className="mx-auto max-w-5xl">
        <p className="text-xs uppercase tracking-[0.2em] text-white/30">
          CareerPilot Intelligence
        </p>

        <h1 className="mt-3 text-4xl font-semibold tracking-tight">
          Companies
        </h1>

        <p className="mt-4 max-w-2xl text-sm leading-6 text-white/45">
          Understand companies beyond job descriptions with
          structured insights into roles, teams, growth, culture
          and career fit.
        </p>

        <div className="mt-10 grid gap-4 md:grid-cols-3">
          <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
            <div className="text-xs uppercase tracking-[0.16em] text-white/30">
              Company profile
            </div>

            <div className="mt-3 text-xl font-semibold">
              Intelligence layer
            </div>

            <p className="mt-2 text-sm leading-6 text-white/35">
              CareerPilot will combine company information and
              opportunity data into a unified company view.
            </p>
          </div>

          <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
            <div className="text-xs uppercase tracking-[0.16em] text-white/30">
              Career fit
            </div>

            <div className="mt-3 text-xl font-semibold">
              Is this company right for you?
            </div>

            <p className="mt-2 text-sm leading-6 text-white/35">
              Compare your goals, skills and preferences against the
              opportunities and environment offered by a company.
            </p>
          </div>

          <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
            <div className="text-xs uppercase tracking-[0.16em] text-white/30">
              Market signals
            </div>

            <div className="mt-3 text-xl font-semibold">
              Opportunity trends
            </div>

            <p className="mt-2 text-sm leading-6 text-white/35">
              Future versions will surface hiring trends, role demand
              and other career-relevant market signals.
            </p>
          </div>
        </div>

        <div className="mt-6 rounded-3xl border border-white/10 bg-white/[0.025] p-8">
          <div className="text-sm font-medium text-white/75">
            Company Intelligence
          </div>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-white/35">
            This workspace will become the company-research layer
            powering CareerPilot's opportunity and career decisions.
          </p>

          <div className="mt-6 inline-flex rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[10px] uppercase tracking-[0.16em] text-white/35">
            Coming in later weeks
          </div>
        </div>
      </div>
    </main>
  );
}