from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
F = ROOT / "frontend"
B = ROOT / "backend"

RESULTS: list[tuple[str, bool]] = []


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def check(name: str, condition: bool) -> None:
    RESULTS.append((name, condition))
    print(f"{len(RESULTS):03d} {'PASS' if condition else 'FAIL'} {name}")


api = text(F / "lib/api.ts")
client = text(F / "lib/apiClient.ts")
agentic = text(F / "lib/agentic.ts")
home = text(F / "app/page-client.tsx")
opp = text(F / "app/opportunities/OpportunitiesClient.tsx")
shell = text(F / "components/AppShell.tsx")
layout = text(F / "app/layout.tsx")
validation = text(F / "lib/validation.ts")
schemas = text(F / "lib/schemas.ts")
config = text(F / "lib/config.ts")
career_twin = text(F / "app/career-twin/page.tsx")
backend_session = text(B / "api/session.py")
backend_main = text(B / "api/main.py")
backend_ct = text(B / "api/career_twin.py")
package = text(F / "package.json")
next_config = text(F / "next.config.ts")
formatters = text(F / "lib/formatters.ts")
resume_structurer = text(B / "services/resume_structurer.py")

# P1 — API / security / architecture
check("P1 API central transport", "apiFetch" in client and "apiFetch" in api and "apiFetch" in agentic)
check("P1 no direct frontend fetch in API services", not re.search(r"\bfetch\(", api) and not re.search(r"\bfetch\(", agentic))
check("P1 422 field error handling", "Array.isArray(detail)" in client and "loc.slice(1)" in client)
check("P1 offline handling", "navigator.onLine === false" in client)
check("P1 idempotency", "X-Idempotency-Key" in client)
check("P1 retry-after handling", "Retry-After" in client and "429" in client)
check("P1 non-JSON error handling", "JSON.parse(text)" in client and "return text.slice(0, 1000)" in client)
check("P1 no localhost API fallback", '"http://127.0.0.1:8000"' not in api and '"http://localhost:8000"' not in api)
check("P1 credentials include", "credentials: \"include\"" in client)
check("P1 correlation IDs", "X-Correlation-ID" in client and "X-Request-ID" in client)
check("P1 runtime Zod schemas", "JobSearchResponseSchema" in schemas and "ResumeAnalysisResponseSchema" in schemas and "AgenticRunResponseSchema" in agentic)
check("P1 search response runtime parse", "JobSearchResponseSchema.parse" in api)
check("P1 agent response runtime parse", "AgenticRunResponseSchema.parse" in agentic)
check("P1 session middleware", (F / "middleware.ts").exists() and "careerpilot_session" in text(F / "middleware.ts"))
check("P1 session bootstrap", (F / "app/api/session/bootstrap/route.ts").exists())
check("P1 CSRF client", "X-CSRF-Token" in client)
check("P1 CSRF backend", "CSRF_COOKIE" in backend_main and "x-csrf-token" in backend_main)
check("P1 production session secret", "must be configured in production" in backend_session)
check("P1 scoped Career Twin operations", backend_ct.count("authenticated_candidate_id") >= 4)
check("P1 unified navigation", "usePathname" in shell and "aria-current" in shell and 'aria-label="Breadcrumb"' in shell)
check("P1 mobile navigation keyboard safety", 'event.key === "Escape"' in shell and 'event.key !== "Tab"' in shell)
for page in ["dashboard", "opportunities", "resume", "career-twin", "companies", "interviews", "applications", "career-plan", "settings"]:
    check(f"P1 AppShell {page}", "AppShell" in text(F / "app" / page / "page.tsx"))
check("P1 functional applications workspace", "Application Intelligence" not in text(F / "app/applications/page.tsx"))
check("P1 functional companies workspace", "Search companies" in text(F / "app/companies/page.tsx"))
check("P1 functional interviews workspace", "Review answer" in text(F / "app/interviews/page.tsx"))
check("P1 functional career plan", "Save goal" in text(F / "app/career-plan/page.tsx"))
check("P1 functional settings", "Save settings" in text(F / "app/settings/page.tsx"))
check("P1 dashboard dynamic metrics", "workspace.jobs.length" in text(F / "app/dashboard/page.tsx") and "workspace.applications.length" in text(F / "app/dashboard/page.tsx"))

# P2 — boundaries, accessibility, state, mobile and performance
check("P2 search input trimming", "role.trim().length < 2" in opp and "location.trim()" in opp)
check("P2 salary upper bound", "salary > 500" in opp)
check("P2 Zod input boundary schema", "max(2000)" in validation and "max(500)" in validation)
check("P2 goal schema applied", "GoalSchema.safeParse" in home)
check("P2 skip link", 'href="#main-content"' in layout and 'id="main-content"' in home and "skip-link" in text(F / "app/globals.css"))
check("P2 async search announcements", 'aria-live="polite"' in opp)
check("P2 form landmark", "<form" in home and "<form" in opp)
check("P2 viewport safety", "maximumScale: 1" in layout)
check("P2 touch target safety", "min-h-11" in opp)
check("P2 semantic labels", 'htmlFor="opportunity-role"' in opp and 'htmlFor="opportunity-location"' in opp)
check("P2 responsive grid foundation", "md:grid-cols" in opp and "lg:grid-cols" in opp)
check("P2 local workspace synchronization", "careerpilot:workspace" in text(F / "lib/workspace.ts"))
check("P2 focus trap", 'event.key !== "Tab"' in shell and "focusable" in shell)
check("P2 active navigation route", "pathname.startsWith" in shell)

# P3 — design/code quality, resume resilience and job intelligence
check("P3 locale-aware formatters", "Intl.NumberFormat" in formatters and "Intl.DateTimeFormat" in formatters)
check("P3 relative timestamps", "formatRelativeTime" in career_twin)
check("P3 no literal icon glyphs in opportunities", not any(ch in opp for ch in "✓△↗"))
check("P3 resume date range resilience", "(?:Present|Current|Now)" in resume_structurer and "(?:Jan(?:uary)?" in resume_structurer)
check("P3 consistent CSS theme tokens", "var(--background)" in text(F / "app/globals.css") and "var(--foreground)" in text(F / "app/globals.css"))
check("P3 shared formatter boundary", "formatSalaryRange" in opp)
check("P3 component-oriented resume architecture", all(name in text(F / "app/resume/ResumeClient.tsx") for name in ["ResumeUpload", "ResumeScores", "ATSChecklist", "JobMatcher", "RewriteSuggestions"]))
check("P3 functional source evidence UI", "Opportunity Intelligence" in opp and "aria-modal=\"true\"" in opp)

# P4 — tests, builds, observability and operations
check("P4 Vitest config", (F / "vitest.config.ts").exists())
check("P4 unit test suite", (F / "tests/formatters.test.ts").exists() and (F / "tests/validation.test.ts").exists())
check("P4 Playwright harness", (F / "playwright.config.ts").exists() and (F / "e2e/smoke.spec.ts").exists())
check("P4 CI workflow", (F / ".github/workflows/ci.yml").exists())
check("P4 standalone build", 'output: "standalone"' in next_config)
check("P4 optimized package imports", "optimizePackageImports" in next_config)
check("P4 frontend health", (F / "app/api/health/route.ts").exists())
check("P4 PWA manifest", (F / "app/manifest.ts").exists())
check("P4 error boundary", (F / "app/error.tsx").exists() and (F / "app/global-error.tsx").exists())
check("P4 telemetry endpoint", (F / "app/api/telemetry/route.ts").exists())
check("P4 telemetry client", "reportTelemetry" in text(F / "lib/telemetry.ts"))
check("P4 web vitals observer", "largest-contentful-paint" in text(F / "components/WebVitals.tsx"))
check("P4 package metadata consistent", '"name": "careerpilot-ai-frontend"' in package and '"typecheck": "tsc --noEmit"' in package)
check("P4 formatter testability", all(name in formatters for name in ["formatCurrency", "formatDateTime", "formatRelativeTime"]))
check("P4 pre-commit hygiene", (ROOT / ".pre-commit-config.yaml").exists())

passed = sum(ok for _, ok in RESULTS)
print(f"\nPHASE2_5 ROOT-CAUSE GATE: {passed}/{len(RESULTS)}")
raise SystemExit(0 if passed == len(RESULTS) else 1)
