from pathlib import Path

ROOT = Path(__file__).resolve().parent

def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"Patch anchor not found in {path}: {old[:80]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")

# --- state.py ---
state = ROOT / "backend/graph/state.py"
replace_once(state,
'    tool_trace: list[ToolTraceEntry]\n',
'    tool_trace: list[ToolTraceEntry]\n\n    career_knowledge_evidence: list[dict[str, Any]]\n')
replace_once(state,
'        tool_trace=[],\n',
'        tool_trace=[],\n\n        career_knowledge_evidence=[],\n')

# --- agentic schema ---
schema = ROOT / "backend/schemas/agentic.py"
replace_once(schema,
'    tools_used: List[str] = Field(\n        default_factory=list\n    )\n\n    delegation_trace',
'    tools_used: List[str] = Field(\n        default_factory=list\n    )\n\n    career_knowledge_evidence: List[Dict[str, Any]] = Field(\n        default_factory=list\n    )\n\n    delegation_trace')

# --- agentic API response ---
api = ROOT / "backend/api/agentic.py"
replace_once(api,
'        tools_used=_serialize(\n            state.get("tools_used") or []\n        ),\n\n        delegation_trace',
'        tools_used=_serialize(\n            state.get("tools_used") or []\n        ),\n\n        career_knowledge_evidence=_serialize(\n            state.get("career_knowledge_evidence") or []\n        ),\n\n        delegation_trace')

# --- recommendation agent enrichment ---
rec = ROOT / "backend/agents/recommendation_agent.py"
replace_once(rec,
'from typing import Any, Dict, List\n\n',
'from typing import Any, Dict, List\n\nfrom backend.tools.knowledge_tools import career_knowledge_tool\n\n')
replace_once(rec,
'        updated_state = dict(state)\n\n',
'        updated_state = dict(state)\n\n        knowledge_result = career_knowledge_tool.invoke({\n            "query": state.get("user_goal", ""),\n            "top_k": 5,\n        })\n        updated_state["career_knowledge_evidence"] = (\n            knowledge_result.get("evidence", [])\n        )\n        knowledge_trace = list(updated_state.get("tool_trace", []) or [])\n        knowledge_trace.append({\n            "tool": "search_career_knowledge",\n            "agent": self.name,\n            "status": "completed",\n            "result_count": knowledge_result.get("count", 0),\n        })\n        updated_state["tool_trace"] = knowledge_trace\n\n')

# --- validation agent evidence gate ---
val = ROOT / "backend/agents/validation_agent.py"
replace_once(val,
'        validation_results.append(\n            {\n                "check": "recommendations",\n                "status": (\n                    "PASS"\n                    if recommendation_validation["valid"]\n                    else "FAIL"\n                ),\n                "result": recommendation_validation,\n            }\n        )\n\n        # ========================================================\n        # 4. OVERALL DECISION',
'        validation_results.append(\n            {\n                "check": "recommendations",\n                "status": (\n                    "PASS"\n                    if recommendation_validation["valid"]\n                    else "FAIL"\n                ),\n                "result": recommendation_validation,\n            }\n        )\n\n        knowledge_evidence = state.get("career_knowledge_evidence") or []\n        knowledge_valid = bool(knowledge_evidence)\n        knowledge_check = {\n            "valid": knowledge_valid,\n            "evidence_count": len(knowledge_evidence),\n            "source_count": len({x.get("source_id") for x in knowledge_evidence if isinstance(x, dict) and x.get("source_id")}),\n            "issues": [] if knowledge_valid else ["No career knowledge evidence was retrieved."],\n        }\n        validation_results.append({\n            "check": "career_knowledge_evidence",\n            "status": "PASS" if knowledge_valid else "FAIL",\n            "result": knowledge_check,\n        })\n\n        # ========================================================\n        # 4. OVERALL DECISION')

print("CareerPilot knowledge implementation patches applied.")
