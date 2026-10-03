from __future__ import annotations

import json
from pathlib import Path

from backend.services.semantic_retriever import career_semantic_retriever

QUERIES = [
    "software engineering interview preparation",
    "skills needed for software developer roles",
    "how to improve a resume for internships",
    "career paths in artificial intelligence",
    "how to evaluate and negotiate a job offer",
    "career readiness competencies for students",
    "finding internships and student opportunities",
    "data science skills and career outlook",
    "cybersecurity career skills",
    "learning and upskilling for technology careers",
]


def run() -> dict:
    rows = []
    for query in QUERIES:
        hits = career_semantic_retriever.search(query, top_k=5)
        rows.append(
            {
                "query": query,
                "result_count": len(hits),
                "source_count": len({h["source_id"] for h in hits}),
                "top_score": hits[0]["relevance"] if hits else 0.0,
                "top_sources": [h["source_id"] for h in hits[:3]],
            }
        )
    report = {
        "queries": len(rows),
        "queries_with_results": sum(r["result_count"] > 0 for r in rows),
        "avg_top_score": round(sum(r["top_score"] for r in rows) / len(rows), 4),
        "results": rows,
    }
    path = Path(__file__).resolve().parents[1] / "data" / "knowledge_retrieval_eval.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    run()
