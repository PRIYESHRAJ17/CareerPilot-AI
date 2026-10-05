from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
REQ = ROOT / "requirements.txt"
PACKAGE = "pypdf==6.19.0"

text = REQ.read_text(encoding="utf-8")
lines = text.splitlines()

if not any(line.strip().lower().startswith("pypdf==") for line in lines):
    if text and not text.endswith("\n"):
        text += "\n"
    text += f"{PACKAGE}\n"
    REQ.write_text(text, encoding="utf-8")
    print(f"PATCH requirements.txt: added {PACKAGE}")
else:
    print("SKIP requirements.txt: pypdf already declared")

subprocess.run([sys.executable, "-m", "pip", "install", PACKAGE], check=True)

import pypdf  # noqa: E402
print(f"INSTALLED pypdf={pypdf.__version__}")

print("\nBackend dependency repair complete.")
print("Next: python -m pytest -q")
