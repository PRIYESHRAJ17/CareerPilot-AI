from __future__ import annotations

from typing import Any


def validate_knowledge_evidence(evidence: Any) -> dict[str, Any]:
    issues: list[str] = []
    if not isinstance(evidence, list) or not evidence:
        issues.append("No career knowledge evidence was retrieved.")
        return {"valid": False, "issues": issues, "evidence_count": 0, "source_count": 0}

    valid_items = []
    for item in evidence:
        if not isinstance(item, dict):
            issues.append("Evidence item has invalid structure.")
            continue
        required = ("evidence_id", "source_id", "title", "url", "text")
        missing = [k for k in required if not str(item.get(k, "")).strip()]
        if missing:
            issues.append(f"Evidence item missing fields: {', '.join(missing)}")
            continue
        if len(str(item["text"]).split()) < 20:
            issues.append(f"Evidence {item['evidence_id']} is too short.")
            continue
        valid_items.append(item)

    sources = {item["source_id"] for item in valid_items}
    if len(valid_items) < 2:
        issues.append("At least two evidence chunks are required for grounded output.")

    return {
        "valid": not issues,
        "issues": issues,
        "evidence_count": len(valid_items),
        "source_count": len(sources),
        "valid_evidence": valid_items,
    }
