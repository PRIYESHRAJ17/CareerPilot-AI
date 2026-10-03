1. Copy fix_careerpilot_final.py into the CareerPilot-AI repo root.
2. From the repo root run:
   python fix_careerpilot_final.py
3. For the existing deterministic LLM tests, temporarily force the provider to none:
   $env:LLM_PROVIDER = "none"
   python -m pytest -q
4. If all tests pass, run the agentic endpoint again.
