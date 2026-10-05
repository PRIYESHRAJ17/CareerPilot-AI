import { Suspense } from "react";

import { AppShell } from "@/components/AppShell";
import ResumeClient from "./ResumeClient";

export default function ResumePage() {
  return (
    <AppShell>
      <Suspense
        fallback={
          <div className="p-8 text-sm text-white/50">
            Loading resume intelligence...
          </div>
        }
      >
        <ResumeClient />
      </Suspense>
    </AppShell>
  );
}