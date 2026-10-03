from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIRED = [
    "backend/api/session.py",
    "backend/api/workspace.py",
    "backend/api/providers.py",
    "backend/services/workspace_store.py",
    "frontend/app/auth/page.tsx",
    "frontend/app/saved-jobs/page.tsx",
    "frontend/app/packets/page.tsx",
    "frontend/app/networking/page.tsx",
    "frontend/app/alerts/page.tsx",
    "frontend/app/market/page.tsx",
    "frontend/app/providers/page.tsx",
    "docs/WEEK7_PHASE6_PRODUCT_IMPLEMENTATION.md",
]

for relative in REQUIRED:
    path = ROOT / relative
    if not path.exists():
        raise SystemExit(f"PHASE6 FAIL: missing {relative}")

checks = {
    "sign-up": (ROOT / "backend/api/session.py").read_text().find('router.post("/signup"') >= 0,
    "login": (ROOT / "backend/api/session.py").read_text().find('router.post("/login"') >= 0,
    "logout": (ROOT / "backend/api/session.py").read_text().find('router.post("/logout"') >= 0,
    "workspace-state": (ROOT / "backend/api/workspace.py").read_text().find('router.get("/state"') >= 0,
    "browser-clipper": (ROOT / "backend/api/workspace.py").read_text().find('router.post("/browser-clip"') >= 0,
    "provider-control": (ROOT / "backend/api/providers.py").read_text().find('router.get("/catalog"') >= 0,
    "agent-run-persistence": '"agent-runs"' in (ROOT / "backend/api/agentic.py").read_text(),
    "server-backed-search-state": '"/workspace/market"' in (ROOT / "frontend/lib/workspace.ts").read_text(),
}

failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("PHASE6 FAIL: " + ", ".join(failed))

print(f"PHASE6 IMPLEMENTATION GATE: PASS ({len(checks)}/{len(checks)} static integration checks)")
