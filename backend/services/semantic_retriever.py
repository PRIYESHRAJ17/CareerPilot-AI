from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DOCS_PATH = DATA_DIR / "career_source_documents.jsonl"
EMBEDDINGS_PATH = DATA_DIR / "career_source_embeddings.npy"
INDEX_PATH = DATA_DIR / "career_source_semantic_index.json"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class CareerSemanticRetriever:
    def __init__(self, model_name: str = MODEL_NAME) -> None:
        self.model_name = model_name
        self._model: SentenceTransformer | None = None
        self._embeddings: np.ndarray | None = None
        self._records: list[dict[str, Any]] | None = None

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def build_index(self) -> dict[str, Any]:
        if not DOCS_PATH.exists():
            raise FileNotFoundError(f"Knowledge corpus not found: {DOCS_PATH}")

        records: list[dict[str, Any]] = []
        with DOCS_PATH.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    records.append(json.loads(line))

        if not records:
            raise ValueError("Knowledge corpus is empty")

        model = self._get_model()
        texts = [r["text"] for r in records]
        embeddings = model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            normalize_embeddings=True,
            convert_to_numpy=True,
        ).astype(np.float32)

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        np.save(EMBEDDINGS_PATH, embeddings)
        INDEX_PATH.write_text(
            json.dumps(
                {
                    "model": self.model_name,
                    "record_count": len(records),
                    "embedding_dimension": int(embeddings.shape[1]),
                    "source_count": len({r["source_id"] for r in records}),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        self._records = records
        self._embeddings = embeddings
        return {
            "records": len(records),
            "sources": len({r["source_id"] for r in records}),
            "dimension": int(embeddings.shape[1]),
            "model": self.model_name,
        }

    def _load(self) -> None:
        if self._records is not None and self._embeddings is not None:
            return
        if not EMBEDDINGS_PATH.exists() or not INDEX_PATH.exists():
            self.build_index()
            return
        records: list[dict[str, Any]] = []
        with DOCS_PATH.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        embeddings = np.load(EMBEDDINGS_PATH)
        if len(records) != len(embeddings):
            self.build_index()
            return
        self._records = records
        self._embeddings = embeddings.astype(np.float32)

    def search(
        self,
        query: str,
        top_k: int = 5,
        category: str | None = None,
        max_per_source: int = 2,
    ) -> list[dict[str, Any]]:
        query = query.strip()
        if not query:
            return []
        self._load()
        assert self._records is not None
        assert self._embeddings is not None

        model = self._get_model()
        q = model.encode(
            [query],
            normalize_embeddings=True,
            convert_to_numpy=True,
        )[0].astype(np.float32)
        scores = self._embeddings @ q
        order = np.argsort(-scores)

        results: list[dict[str, Any]] = []
        source_counts: dict[str, int] = {}
        for idx in order:
            record = self._records[int(idx)]
            if category and record.get("category") != category:
                continue
            sid = record["source_id"]
            if source_counts.get(sid, 0) >= max_per_source:
                continue
            source_counts[sid] = source_counts.get(sid, 0) + 1
            results.append(
                {
                    "evidence_id": record["chunk_id"],
                    "source_id": sid,
                    "publisher": record["publisher"],
                    "title": record["title"],
                    "category": record["category"],
                    "topics": record.get("topics", []),
                    "url": record["url"],
                    "resolved_url": record.get("resolved_url", record["url"]),
                    "retrieval_method": record.get("retrieval_method"),
                    "relevance": round(float(scores[int(idx)]), 6),
                    "text": record["text"],
                }
            )
            if len(results) >= top_k:
                break
        return results


career_semantic_retriever = CareerSemanticRetriever()
