# CareerPilot Opportunity Coverage UI Patch

This patch updates only the existing Opportunities page.

It keeps:
- Job Sources = 2 (the live opportunity providers)

and adds:
- Career Intelligence = 100
- 98 knowledge sources + 2 live providers

Apply from the CareerPilot repository root:

```powershell
$env:PYTHONPATH = "."
python apply_career_intelligence_coverage.py
```

Restart the Next.js dev server or let hot reload update the page.
