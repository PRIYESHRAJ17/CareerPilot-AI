from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.services.semantic_retriever import career_semantic_retriever
from backend.services.source_retriever import CareerSourceRegistry

router = APIRouter(prefix="/knowledge", tags=["Career Knowledge"])


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=10)
    category: str | None = None


@router.get("/sources")
def list_sources() -> dict[str, Any]:
    registry = CareerSourceRegistry()
    return {"count": registry.count(), "sources": registry.sources}


@router.post("/search")
def search_knowledge(request: KnowledgeSearchRequest) -> dict[str, Any]:
    try:
        evidence = career_semantic_retriever.search(
            query=request.query,
            top_k=request.top_k,
            category=request.category,
        )
        return {
            "query": request.query,
            "count": len(evidence),
            "evidence": evidence,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Knowledge search failed: {exc}") from exc


@router.post("/rebuild")
def rebuild_knowledge_index() -> dict[str, Any]:
    try:
        return career_semantic_retriever.build_index()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Knowledge index build failed: {exc}") from exc
