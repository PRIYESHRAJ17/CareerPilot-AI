export default function SettingsPage() {
  return (
    <main className="min-h-screen bg-[#080a0f] p-10 text-white">
      <div className="mx-auto max-w-5xl">
        <p className="text-xs uppercase tracking-[0.2em] text-white/30">
          CareerPilot Workspace
        </p>

        <h1 className="mt-3 text-4xl font-semibold tracking-tight">
          Settings
        </h1>

        <p className="mt-4 max-w-2xl text-sm leading-6 text-white/45">
          Control your CareerPilot profile, preferences, privacy,
          notifications and connected services.
        </p>

        <div className="mt-10 space-y-4">
          <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-7">
            <div className="text-xs uppercase tracking-[0.16em] text-white/30">
              Career preferences
            </div>

            <h2 className="mt-2 text-xl font-semibold">
              Your search and career preferences
            </h2>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-white/35">
              Future settings will control target roles, locations,
              salary expectations, work modes, experience level and
              career goals.
            </p>
          </section>

          <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-7">
            <div className="text-xs uppercase tracking-[0.16em] text-white/30">
              Privacy
            </div>

            <h2 className="mt-2 text-xl font-semibold">
              Career data & privacy
            </h2>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-white/35">
              Resume data, career profiles and application information
              will be handled through dedicated privacy and security
              controls as the platform evolves.
            </p>
          </section>

          <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-7">
            <div className="text-xs uppercase tracking-[0.16em] text-white/30">
              Automation
            </div>

            <h2 className="mt-2 text-xl font-semibold">
              Notifications & automations
            </h2>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-white/35">
              Future controls will let you manage job alerts,
              application reminders, interview workflows and other
              CareerPilot automations.
            </p>
          </section>

          <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-7">
            <div className="text-xs uppercase tracking-[0.16em] text-white/30">
              Integrations
            </div>

            <h2 className="mt-2 text-xl font-semibold">
              Connected services
            </h2>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-white/35">
              CareerPilot will eventually manage integrations with
              job sources, calendars, email, automation workflows
              and other career tools from this workspace.
            </p>
          </section>
        </div>

        <div className="mt-6 inline-flex rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[10px] uppercase tracking-[0.16em] text-white/35">
          Foundation workspace
        </div>
      </div>
    </main>
  );
}