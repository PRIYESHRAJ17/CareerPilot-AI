
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "frontend" / "app" / "opportunities" / "page.tsx"

if not TARGET.exists():
    raise FileNotFoundError(f"Missing target file: {TARGET}")

text = TARGET.read_text(encoding="utf-8")

needle = """const defaultSkills = [
  "Python",
  "SQL",
  "DSA",
  "Git",
];
"""

replacement = """const defaultSkills = [
  "Python",
  "SQL",
  "DSA",
  "Git",
];

// Career intelligence coverage combines the 98-source knowledge
// corpus with the 2 existing live opportunity providers.
const TOTAL_CAREER_INTELLIGENCE_SOURCES = 100;
"""

if needle not in text:
    raise RuntimeError("Could not find defaultSkills block.")
text = text.replace(needle, replacement, 1)

old_grid = """<section className="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-4">"""
new_grid = """<section className="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-5">"""
if old_grid not in text:
    raise RuntimeError("Could not find stats grid.")
text = text.replace(old_grid, new_grid, 1)

job_card = """                <div className="rounded-2xl border border-white/8 bg-white/[0.025] p-5">
                  <div className="text-[11px] uppercase tracking-[0.17em] text-white/30">
                    Job sources
                  </div>
"""

coverage_card = """                <div className="rounded-2xl border border-white/8 bg-white/[0.025] p-5">
                  <div className="text-[11px] uppercase tracking-[0.17em] text-white/30">
                    Career intelligence
                  </div>

                  <div className="mt-2 text-3xl font-semibold">
                    {searched
                      ? TOTAL_CAREER_INTELLIGENCE_SOURCES
                      : "—"}
                  </div>

                  <div className="mt-1 text-xs text-white/35">
                    98 knowledge sources + 2 live providers
                  </div>
                </div>

""" + job_card

if job_card not in text:
    raise RuntimeError("Could not find Job sources card.")
text = text.replace(job_card, coverage_card, 1)

TARGET.write_text(text, encoding="utf-8")

print("CareerPilot opportunity source coverage UI updated.")
print("Live Job Sources remains 2.")
print("Career Intelligence total is now shown as 100.")
