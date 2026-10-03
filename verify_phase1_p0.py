from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path.cwd()
F = ROOT / "frontend"
B = ROOT / "backend"

def text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(
        encoding="utf-8-sig",
    )

def check(
    number: int,
    title: str,
    condition: bool,
) -> bool:
    print(
        f"{number:03d} "
        f"{'PASS' if condition else 'FAIL'} "
        f"{title}"
    )
    return condition

layout = text(F / "app/layout.tsx")
globals_css = text(F / "app/globals.css")
next_config = text(F / "next.config.ts")
home = text(F / "app/page-client.tsx")
opp = text(F / "app/opportunities/OpportunitiesClient.tsx")
resume = text(F / "app/resume/ResumeClient.tsx")
twin = text(F / "app/career-twin/page.tsx")
dashboard = text(F / "app/dashboard/page.tsx")
agentic = text(F / "lib/agentic.ts")
api = text(F / "lib/api.ts")
config = text(F / "lib/config.ts")
shell = text(F / "components/AppShell.tsx")
workspace = text(F / "lib/workspace.ts")
session = text(B / "api/session.py")
main = text(B / "api/main.py")
ct = text(B / "api/career_twin.py")
backend_agentic = text(B / "api/agentic.py")
package = json.loads(
    text(F / "package.json") or "{}"
)

checks = []

checks.append(check(
    1,
    "browser title",
    "CareerPilot AI — Autonomous Career Operating System" in layout,
))

checks.append(check(
    2,
    "meta description",
    "AI-orchestrated career intelligence platform" in layout,
))

checks.append(check(
    3,
    "Arial removed",
    "Arial, Helvetica, sans-serif" not in globals_css,
))

checks.append(check(
    4,
    "api-user removed",
    "api-user" not in home + opp + twin + main + backend_agentic + ct,
))

checks.append(check(
    5,
    "single trace id",
    "crypto.randomUUID()" in home
    and "request_id: traceId" in home
    and "thread_id: traceId" in home,
))

checks.append(check(
    6,
    "persistent session",
    "careerpilot_session" in session
    and "set_cookie" in session,
))

checks.append(check(
    7,
    "projects are user-backed",
    "projects={projects}" in home
    or "candidateProjects" in home,
))

checks.append(check(
    8,
    "dashboard opportunities dynamic",
    "workspace.jobs.length" in dashboard,
))

checks.append(check(
    9,
    "dashboard strong matches dynamic",
    "strongMatches" in dashboard,
))

checks.append(check(
    10,
    "dashboard skills dynamic",
    "profile?.skills" in dashboard,
))

checks.append(check(
    11,
    "dashboard applications dynamic",
    "workspace.applications.length" in dashboard,
))

checks.append(check(
    12,
    "dashboard activity dynamic",
    "workspace.activity" in dashboard,
))

checks.append(check(
    13,
    "dynamic nav",
    "usePathname" in shell,
))

checks.append(check(
    14,
    "no hardcoded defaultSkills",
    "defaultSkills" not in opp,
))

checks.append(check(
    15,
    "experience years input",
    "experienceYears" in opp,
))

checks.append(check(
    16,
    "on-site mode",
    '"on-site"' in opp,
))

checks.append(check(
    17,
    "industries selector",
    "industries" in opp,
))

checks.append(check(
    18,
    "apply url validation",
    "isValidHttpUrl" in opp,
))

checks.append(check(
    19,
    "drawer CTA validation",
    "Apply unavailable" in opp,
))

checks.append(check(
    20,
    "search timeout",
    "DEFAULT_REQUEST_TIMEOUT_MS" in api,
))

checks.append(check(
    21,
    "agentic cancellation",
    "signal?: AbortSignal" in agentic,
))

checks.append(check(
    22,
    "resume timeout",
    "RESUME_REQUEST_TIMEOUT_MS" in api,
))

checks.append(check(
    23,
    "cache control",
    '"Cache-Control":' in api
    and '"Cache-Control":' in agentic,
))

checks.append(check(
    24,
    "salary target comparison",
    "BELOW_TARGET" in api,
))

checks.append(check(
    25,
    "safe evidence formatting",
    "safeEvidencePreview" in home,
))

checks.append(check(
    26,
    "workflow progress",
    "getAgentState" in home,
))

checks.append(check(
    27,
    "resume JobView",
    "type JobView" in resume,
))

checks.append(check(
    28,
    "expanded experience",
    "expandedExperience" in resume,
))

checks.append(check(
    29,
    "rejected file clears input",
    "event.target.value = """ in text(F / "app/resume/ResumeUpload.tsx"),
))

checks.append(check(
    30,
    "searched after successful response",
    "setSearched(true)" in opp,
))

checks.append(check(
    31,
    "selected job preservation",
    "previousId" in opp,
))

checks.append(check(
    32,
    "home H1 spacing",
    'Your career,{" "}' in home,
))

checks.append(check(
    33,
    "opportunities heading spacing",
    "Live opportunities" in opp,
))

checks.append(check(
    34,
    "dashboard uses AppShell",
    "<AppShell>" in dashboard,
))

checks.append(check(
    35,
    "internal navigation uses Link",
    'from "next/link"' in shell,
))

checks.append(check(
    36,
    "Career Twin session auth",
    "/career-twin/session" in twin
    and "credentials:" in twin,
))

checks.append(check(
    37,
    "mobile Escape",
    'event.key === "Escape"' in shell,
))

checks.append(check(
    38,
    "drawer Escape",
    'event.key === "Escape"' in opp,
))

checks.append(check(
    39,
    "drawer focus trap",
    'event.key === "Tab"' in opp,
))

checks.append(check(
    40,
    "reset workspace",
    "Reset Workspace" in home,
))

checks.append(check(
    41,
    "input error clearing",
    "setError(null)" in home,
))

checks.append(check(
    42,
    "goal 2000 char max",
    "maxLength={2000}" in home,
))

checks.append(check(
    43,
    "skills dedupe",
    "normalizeCommaList" in home,
))

checks.append(check(
    44,
    "semantic form",
    "<form" in home,
))

checks.append(check(
    45,
    "accessible labels",
    "<label" in home,
))

checks.append(check(
    46,
    "theme functional",
    "ThemeToggle" in shell,
))

checks.append(check(
    47,
    "profile link functional",
    'href="/career-twin"' in shell,
))

checks.append(check(
    48,
    "profile card functional",
    "Career profile" in shell,
))

checks.append(check(
    49,
    "Menu/X hamburger",
    "<Menu" in shell and "<X" in shell,
))

checks.append(check(
    50,
    "memory pagination",
    "memoryLimit" in twin,
))

checks.append(check(
    51,
    "four stat cards",
    "xl:grid-cols-4" in dashboard,
))

checks.append(check(
    52,
    "resume type explicit",
    "[key: string]: unknown" not in api[
        api.find(
            "export interface ResumeIntelligenceResponse"
        ):
        api.find(
            "export interface ResumeAnalysisResponse"
        )
    ],
))

checks.append(check(
    53,
    "ATS type explicit",
    "[key: string]: unknown" not in api[
        api.find(
            "export interface ATSAnalysisResponse"
        ):
        api.find(
            "export interface JobResumeRequirement"
        )
    ],
))

checks.append(check(
    54,
    "strict validation status",
    '"FAILED"' in agentic,
))

checks.append(check(
    55,
    "strict evidence status",
    '"PARTIAL"' in agentic
    and '"UNSUPPORTED"' in agentic,
))

checks.append(check(
    56,
    "typed skill gaps",
    "interface SkillGap" in agentic,
))

checks.append(check(
    57,
    "typed rewrite candidates",
    "interface RewriteCandidate" in agentic,
))

checks.append(check(
    58,
    "typed errors",
    "interface WorkflowError" in agentic,
))

checks.append(check(
    59,
    "typed recommendations",
    "interface CareerRecommendation" in agentic,
))

checks.append(check(
    60,
    "typed next action",
    "interface NextAction" in agentic,
))

checks.append(check(
    61,
    "typed final validation",
    "interface FinalValidation" in agentic,
))

checks.append(check(
    62,
    "friendly API errors",
    "slice(0, 400)" in agentic,
))

checks.append(check(
    63,
    "security headers",
    all(
        key in next_config
        for key in (
            "Content-Security-Policy",
            "Strict-Transport-Security",
            "X-Frame-Options",
            "X-Content-Type-Options",
            "Referrer-Policy",
        )
    ),
))

checks.append(check(
    64,
    "poweredBy disabled",
    "poweredByHeader: false" in next_config,
))

checks.append(check(
    65,
    "ReactNode layout props",
    "{ children }: { children: ReactNode }" in layout,
))

checks.append(check(
    66,
    "CSS variables active",
    "var(--background)" in globals_css
    and "var(--foreground)" in globals_css,
))

checks.append(check(
    67,
    "real theme switching",
    "dataset.theme" in text(F / "lib/theme.tsx"),
))

checks.append(check(
    68,
    "package name/metadata",
    package.get("name")
    == "careerpilot-ai-frontend"
    and package.get("description"),
))

checks.append(check(
    69,
    "strict lint",
    package.get("scripts", {}).get(
        "lint",
    )
    == "eslint . --max-warnings 0",
))

checks.append(check(
    70,
    "zod",
    "zod" in package.get(
        "dependencies",
        {},
    ),
))

checks.append(check(
    71,
    "lucide pinned",
    package.get("dependencies", {}).get(
        "lucide-react"
    )
    == "1.34.0",
))

checks.append(check(
    72,
    "node/npm engines",
    package.get("engines")
    == {
        "node": ">=20.9.0",
        "npm": ">=10.0.0",
    },
))

checks.append(check(
    73,
    "test script",
    package.get("scripts", {}).get(
        "test"
    )
    == "vitest run",
))

checks.append(check(
    74,
    "typecheck script",
    package.get("scripts", {}).get(
        "typecheck"
    )
    == "tsc --noEmit",
))

checks.append(check(
    75,
    "home server/client split",
    (F / "app/page.tsx").exists()
    and (
        F / "app/page-client.tsx"
    ).exists(),
))

checks.append(check(
    76,
    "opportunities split",
    (F / "app/opportunities/page.tsx").exists()
    and (
        F
        / "app/opportunities/OpportunitiesClient.tsx"
    ).exists(),
))

checks.append(check(
    77,
    "resume split",
    (F / "app/resume/page.tsx").exists()
    and (
        F / "app/resume/ResumeClient.tsx"
    ).exists()
    and (
        F / "app/resume/ResumeUpload.tsx"
    ).exists()
    and (
        F / "app/resume/ResumeScores.tsx"
    ).exists()
    and (
        F / "app/resume/ATSChecklist.tsx"
    ).exists()
    and (
        F / "app/resume/JobMatcher.tsx"
    ).exists()
    and (
        F / "app/resume/RewriteSuggestions.tsx"
    ).exists(),
))

checks.append(check(
    78,
    "central API config",
    "API_BASE_URL" in api
    and 'from "./config"' in api,
))

checks.append(check(
    79,
    "raw salary data",
    "salary_min_lpa" in opp,
))

checks.append(check(
    80,
    "compact undisclosed badge",
    "Undisclosed" in opp,
))

checks.append(check(
    81,
    "single-decimal salary regex",
    'replace(/(\\..*)\\./g, "$1")' in opp,
))

checks.append(check(
    82,
    "backend 10MB/413",
    "10 * 1024 * 1024" in main
    and "status_code=413" in main,
))

checks.append(check(
    83,
    "raw response error text",
    "response.text()" in agentic,
))

checks.append(check(
    84,
    "useMemo depends on result",
    "[result]" in home,
))

checks.append(check(
    85,
    "stable recommendation keys",
    "recommendation.id" in home,
))

checks.append(check(
    86,
    "stable skeleton keys",
    "skeleton-" in opp,
))

checks.append(check(
    87,
    "stable source/job identity",
    "${job.source}:${job.source_job_id}" in opp,
))

checks.append(check(
    88,
    "recommendation badge spacing",
    "min-w-[1.5rem]" in home
    and "px-1" in home,
))

checks.append(check(
    89,
    "retry null-safe",
    "result?.retry_count ?? 0" in home,
))

checks.append(check(
    90,
    "tools null-safe",
    "(result.tools_used ?? []).length" in home
    or "(result.tools_used ?? [])" in home,
))

checks.append(check(
    91,
    "readiness clamped",
    "clampScore" in config,
))

checks.append(check(
    92,
    "friendly human status labels",
    "friendlyStatus" in home,
))

checks.append(check(
    93,
    "loading status in header",
    "friendlyStatus(result?.status, loading)" in home,
))

checks.append(check(
    94,
    "canonical lifecycle states",
    all(
        value in agentic
        for value in (
            "PENDING",
            "DISPATCHED",
            "AGENT_EXECUTION",
            "VALIDATING",
            "COMPLETED",
            "PARTIAL",
            "FAILED",
        )
    ),
))

checks.append(check(
    95,
    "evidence ellipsis rule",
    "text.length <= 360" in home,
))

checks.append(check(
    96,
    "empty delegation safe",
    "?.delegation_trace?.length" in home,
))

checks.append(check(
    97,
    "mobile/result auto-scroll",
    "scrollIntoView" in home,
))

checks.append(check(
    98,
    "CP avatar fallback",
    '"CP"' in opp,
))

checks.append(check(
    99,
    "filter location before join",
    "filter(Boolean).join" in opp,
))

checks.append(check(
    100,
    "confidence normalization",
    "normalizeConfidence" in api
    and "normalizeConfidence" in opp,
))

passed = sum(
    1
    for value in checks
    if value
)

print()
print(
    f"P0 machine gate: {passed}/100"
)

raise SystemExit(
    0
    if passed == 100
    else 1
)
