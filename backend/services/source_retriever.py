from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import requests


DATA_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "career_sources.json"
)


class HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag.lower() in {
            "script",
            "style",
            "noscript",
            "svg",
        }:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if (
            tag.lower()
            in {"script", "style", "noscript", "svg"}
            and self._skip_depth > 0
        ):
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return

        clean = re.sub(
            r"\s+",
            " ",
            data,
        ).strip()

        if clean:
            self.parts.append(clean)

    def text(self) -> str:
        return "\n".join(self.parts)


class CareerSourceRegistry:

    def __init__(
        self,
        data_path: Path = DATA_PATH,
    ) -> None:

        if not data_path.exists():
            raise FileNotFoundError(
                f"Source dataset not found: {data_path}"
            )

        with data_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            payload = json.load(file)

        self.dataset = payload
        self.sources: list[dict[str, Any]] = (
            payload["sources"]
        )

        expected = payload["additional_sources"]

        if len(self.sources) != expected:
            raise ValueError(
                f"Expected {expected} sources, "
                f"found {len(self.sources)}."
            )

        urls = [
            source["url"]
            for source in self.sources
        ]

        if len(urls) != len(set(urls)):
            raise ValueError(
                "Duplicate source URLs detected."
            )

    def count(self) -> int:
        return len(self.sources)

    def get(
        self,
        source_id: str,
    ) -> dict[str, Any] | None:

        for source in self.sources:
            if source["id"] == source_id:
                return source

        return None

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {
            token
            for token in re.findall(
                r"[a-z0-9]+",
                text.lower(),
            )
            if len(token) >= 3
        }

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:

        query_tokens = self._tokens(query)

        if not query_tokens:
            return []

        ranked: list[
            tuple[float, dict[str, Any]]
        ] = []

        for source in self.sources:

            searchable_text = " ".join(
                [
                    source["publisher"],
                    source["title"],
                    source["category"],
                    " ".join(
                        source.get(
                            "topics",
                            [],
                        )
                    ),
                ]
            )

            source_tokens = self._tokens(
                searchable_text
            )

            overlap = len(
                query_tokens
                & source_tokens
            )

            title_bonus = (
                2.0
                if query.lower()
                in source["title"].lower()
                else 0.0
            )

            score = (
                float(overlap)
                + title_bonus
            )

            if score > 0:
                ranked.append(
                    (
                        score,
                        source,
                    )
                )

        ranked.sort(
            key=lambda item: (
                -item[0],
                item[1]["id"],
            )
        )

        return [
            source
            for _, source
            in ranked[:top_k]
        ]


class CareerSourceRetriever(
    CareerSourceRegistry
):

    USER_AGENT = (
        "CareerPilot-AI/Week5"
    )

    TIMEOUT = 15

    def fetch(
        self,
        source: dict[str, Any],
    ) -> dict[str, Any]:

        response = requests.get(
            source["url"],
            headers={
                "User-Agent": self.USER_AGENT,
            },
            timeout=self.TIMEOUT,
            allow_redirects=True,
        )

        response.raise_for_status()

        parser = (
            HTMLTextExtractor()
        )

        parser.feed(
            response.text
        )

        content = parser.text()

        return {
            **source,
            "resolved_url": response.url,
            "http_status": response.status_code,
            "content": content,
            "content_length": len(
                content
            ),
        }

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        fetch_content: bool = False,
    ) -> list[dict[str, Any]]:

        matches = self.search(
            query=query,
            top_k=top_k,
        )

        if not fetch_content:
            return matches

        results: list[
            dict[str, Any]
        ] = []

        for source in matches:
            try:

                results.append(
                    self.fetch(
                        source
                    )
                )

            except requests.RequestException as exc:

                results.append(
                    {
                        **source,
                        "fetch_error": str(
                            exc
                        ),
                    }
                )

        return results