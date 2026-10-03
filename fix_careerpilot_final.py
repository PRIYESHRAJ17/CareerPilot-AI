from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Fix agentic API: provide a minimal candidate profile when only user_goal is supplied.
api_path = ROOT / 'backend' / 'api' / 'agentic.py'
text = api_path.read_text(encoding='utf-8')
old = '''        if request.candidate_profile is not None:\n            state["candidate_profile"] = (\n                request.candidate_profile\n            )\n\n        if request.resume_base64:\n'''
new = '''        if request.candidate_profile is not None:\n            state["candidate_profile"] = (\n                request.candidate_profile\n            )\n        else:\n            # A bare career question still needs a minimal candidate\n            # context so the existing Candidate -> Strategy ->\n            # Recommendation -> Validation workflow can execute.\n            state["candidate_profile"] = {\n                "candidate_id": "agentic-user",\n                "name": "CareerPilot User",\n                "headline": request.user_goal,\n                "skills": [],\n                "technical_skills": [],\n                "soft_skills": [],\n                "years_of_experience": 0.0,\n                "education": [],\n                "certifications": [],\n                "projects": [],\n                "preferred_locations": [],\n                "preferred_work_modes": [],\n                "metadata": {},\n                "career_goal": {\n                    "target_roles": [request.user_goal],\n                    "target_industries": [],\n                    "target_locations": [],\n                    "minimum_salary_lpa": None,\n                    "preferred_work_modes": [],\n                    "target_timeline_months": None,\n                },\n            }\n\n        if request.resume_base64:\n'''
if old not in text:
    raise SystemExit('Agentic API patch anchor not found.')
api_path.write_text(text.replace(old, new, 1), encoding='utf-8')

print('Final CareerPilot agentic fix applied.')
