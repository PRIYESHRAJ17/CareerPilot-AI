from __future__ import annotations

from typing import Any

from backend.services.semantic_retriever import career_semantic_retriever


class CareerKnowledgeTool:
    name = "search_career_knowledge"

    def invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
        query = str(payload.get("query", "")).strip()
        top_k = int(payload.get("top_k", 5) or 5)
        category = payload.get("category")
        evidence = career_semantic_retriever.search(
            query=query,
            top_k=max(1, min(top_k, 10)),
            category=category,
        )
        return {
            "query": query,
            "count": len(evidence),
            "evidence": evidence,
        }


career_knowledge_tool = CareerKnowledgeTool()


def search_career_knowledge(
    query: str,
    top_k: int = 5,
    category: str | None = None,
) -> dict[str, Any]:
    return career_knowledge_tool.invoke(
        {"query": query, "top_k": top_k, "category": category}
    )
