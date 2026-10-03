import { Suspense } from "react";
import { AppShell } from "@/components/AppShell";
import OpportunitiesClient from "./OpportunitiesClient";

export default function Page() {
  return (
    <AppShell>
      <Suspense fallback={<div className="min-h-screen bg-[#080a0f] p-8 text-white/50">Loading opportunities...</div>}>
        <OpportunitiesClient />
      </Suspense>
    </AppShell>
  );
}
