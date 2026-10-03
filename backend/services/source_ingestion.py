from __future__ import annotations

import json
import re
import time
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import requests

from backend.services.source_retriever import (
    CareerSourceRegistry,
)


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = (
    Path(__file__).resolve().parent.parent
)

OUTPUT_PATH = (
    BASE_DIR
    / "data"
    / "career_source_documents.jsonl"
)

MANIFEST_PATH = (
    BASE_DIR
    / "data"
    / "career_source_ingestion_manifest.json"
)


# ---------------------------------------------------------------------------
# HTTP configuration
# ---------------------------------------------------------------------------

REQUEST_TIMEOUT = 25
READER_TIMEOUT = 45

MAX_DIRECT_ATTEMPTS = 3
MAX_READER_ATTEMPTS = 2

RETRYABLE_STATUS_CODES = {
    408,
    429,
    500,
    502,
    503,
    504,
}

READER_FALLBACK_STATUS_CODES = {
    403,
    429,
    451,
}

MIN_TEXT_LENGTH = 100

DIRECT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/142.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,"
        "text/plain;q=0.8,"
        "*/*;q=0.7"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
}

READER_HEADERS = {
    "User-Agent": (
        "CareerPilot-AI/Week5 "
        "(career-intelligence-research)"
    ),
    "Accept": "text/plain,text/markdown,*/*",
}


# ---------------------------------------------------------------------------
# HTML cleaner
# ---------------------------------------------------------------------------

class HTMLCleaner(HTMLParser):
    """
    Dependency-free HTML -> readable text.
    """

    SKIP_TAGS = {
        "script",
        "style",
        "noscript",
        "svg",
        "canvas",
        "iframe",
        "template",
    }

    BLOCK_TAGS = {
        "article",
        "aside",
        "blockquote",
        "br",
        "div",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "li",
        "main",
        "nav",
        "ol",
        "p",
        "section",
        "table",
        "td",
        "th",
        "tr",
        "ul",
    }

    def __init__(self) -> None:
        super().__init__(
            convert_charrefs=True
        )

        self.skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        normalized_tag = tag.lower()

        if normalized_tag in self.SKIP_TAGS:
            self.skip_depth += 1
            return

        if (
            normalized_tag in self.BLOCK_TAGS
            and self.skip_depth == 0
        ):
            self.parts.append("\n")

    def handle_endtag(
        self,
        tag: str,
    ) -> None:
        normalized_tag = tag.lower()

        if (
            normalized_tag in self.SKIP_TAGS
            and self.skip_depth > 0
        ):
            self.skip_depth -= 1
            return

        if (
            normalized_tag in self.BLOCK_TAGS
            and self.skip_depth == 0
        ):
            self.parts.append("\n")

    def handle_data(
        self,
        data: str,
    ) -> None:
        if self.skip_depth:
            return

        cleaned = re.sub(
            r"\s+",
            " ",
            data,
        ).strip()

        if cleaned:
            self.parts.append(cleaned)

    def get_text(self) -> str:
        return "\n".join(self.parts)


# ---------------------------------------------------------------------------
# Text normalization
# ---------------------------------------------------------------------------

def normalize_text(
    text: str,
) -> str:
    """
    Normalize extracted webpage/reader text.
    """

    text = text.replace(
        "\xa0",
        " ",
    )

    # Normalize spaces and tabs.
    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    # Normalize excessive newlines.
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    # Remove whitespace around line boundaries.
    text = re.sub(
        r" *\n *",
        "\n",
        text,
    )

    return text.strip()


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def chunk_text(
    text: str,
    chunk_size: int = 450,
    overlap: int = 75,
) -> list[str]:
    """
    Split text into overlapping word-based chunks.

    chunk_size:
        Maximum approximate words per chunk.

    overlap:
        Number of words shared between adjacent chunks.
    """

    if chunk_size <= 0:
        raise ValueError(
            "chunk_size must be greater than 0"
        )

    if overlap < 0:
        raise ValueError(
            "overlap cannot be negative"
        )

    if overlap >= chunk_size:
        raise ValueError(
            "overlap must be smaller than chunk_size"
        )

    words = text.split()

    if not words:
        return []

    chunks: list[str] = []

    start = 0

    while start < len(words):
        end = min(
            start + chunk_size,
            len(words),
        )

        chunk = " ".join(
            words[start:end]
        ).strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(words):
            break

        start = max(
            end - overlap,
            start + 1,
        )

    return chunks


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_html_text(
    html: str,
) -> str:
    """
    Convert HTML into readable plain text.
    """

    parser = HTMLCleaner()

    try:
        parser.feed(html)
        parser.close()
    except Exception:
        # HTMLParser can encounter malformed markup.
        # The partial parse is still useful.
        pass

    return normalize_text(
        parser.get_text()
    )


def _looks_like_html(
    content_type: str,
    text: str,
) -> bool:
    """
    Determine whether a response should be treated as HTML.
    """

    content_type = (
        content_type or ""
    ).lower()

    if (
        "text/html" in content_type
        or "application/xhtml+xml"
        in content_type
    ):
        return True

    stripped = text.lstrip().lower()

    return (
        stripped.startswith("<!doctype html")
        or stripped.startswith("<html")
        or "<body" in stripped[:2000]
    )


def _is_meaningful_text(
    text: str,
) -> bool:
    """
    Prevent successful HTTP responses with no useful readable content
    from being counted as successful ingestion.
    """

    if not text:
        return False

    normalized = normalize_text(text)

    if len(normalized) < MIN_TEXT_LENGTH:
        return False

    # Count actual alphanumeric characters.
    alphanumeric = re.sub(
        r"[^A-Za-z0-9]+",
        "",
        normalized,
    )

    return len(alphanumeric) >= 50


def _reader_url(
    source_url: str,
) -> str:
    """
    Convert a public source URL into a Jina Reader URL.

    Example:
        https://example.com/page
    becomes:
        https://r.jina.ai/https://example.com/page
    """

    return (
        "https://r.jina.ai/"
        + source_url
    )


# ---------------------------------------------------------------------------
# Reader fallback
# ---------------------------------------------------------------------------

def _fetch_with_reader(
    source_url: str,
    original_status: int | None,
) -> dict[str, Any] | None:
    """
    Retrieve a public webpage through a text-reading fallback.

    This is primarily used for sites that reject normal HTTP clients
    with 403/429/451 responses.
    """

    reader_url = _reader_url(
        source_url
    )

    last_error: str | None = None

    for attempt in range(
        1,
        MAX_READER_ATTEMPTS + 1,
    ):
        try:
            response = requests.get(
                reader_url,
                headers=READER_HEADERS,
                timeout=READER_TIMEOUT,
                allow_redirects=True,
            )

            if response.ok:
                text = normalize_text(
                    response.text
                )

                if _is_meaningful_text(
                    text
                ):
                    return {
                        "source": None,
                        "resolved_url": source_url,
                        "http_status": (
                            original_status
                            if original_status
                            is not None
                            else response.status_code
                        ),
                        "content_type": (
                            "text/plain"
                        ),
                        "text": text,
                        "retrieval_method": (
                            "reader_fallback"
                        ),
                    }

                last_error = (
                    "Reader returned "
                    "empty/insufficient text"
                )

            else:
                last_error = (
                    f"Reader HTTP "
                    f"{response.status_code}"
                )

        except requests.RequestException as exc:
            last_error = str(exc)

        if attempt < MAX_READER_ATTEMPTS:
            time.sleep(
                1.5 * attempt
            )

    return None


# ---------------------------------------------------------------------------
# Direct source fetch
# ---------------------------------------------------------------------------

def fetch_source(
    source: dict[str, Any],
) -> dict[str, Any]:
    """
    Fetch one career-intelligence source.

    Strategy:

    1. Try direct HTTP request with browser-like headers.
    2. Retry transient failures.
    3. If the site blocks the request with 403/429/451,
       use the reader fallback.
    4. If the source is a PDF, use the reader fallback.
    5. Reject empty/meaningless pages.
    """

    url = source["url"]

    last_error: str | None = None
    last_status: int | None = None

    for attempt in range(
        1,
        MAX_DIRECT_ATTEMPTS + 1,
    ):
        try:
            response = requests.get(
                url,
                headers=DIRECT_HEADERS,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True,
            )

            last_status = (
                response.status_code
            )

            content_type = (
                response.headers.get(
                    "content-type",
                    "",
                )
                .lower()
            )

            # -------------------------------------------------------
            # Blocked by origin server
            # -------------------------------------------------------

            if (
                response.status_code
                in READER_FALLBACK_STATUS_CODES
            ):
                reader_result = (
                    _fetch_with_reader(
                        url,
                        response.status_code,
                    )
                )

                if reader_result:
                    reader_result[
                        "source"
                    ] = source

                    return reader_result

                last_error = (
                    f"HTTP {response.status_code}; "
                    "reader fallback failed"
                )

                break

            # -------------------------------------------------------
            # Retry transient server errors
            # -------------------------------------------------------

            if (
                response.status_code
                in RETRYABLE_STATUS_CODES
            ):
                last_error = (
                    f"HTTP "
                    f"{response.status_code}"
                )

                if attempt < MAX_DIRECT_ATTEMPTS:
                    time.sleep(
                        1.5 * attempt
                    )
                    continue

                break

            # -------------------------------------------------------
            # Permanent HTTP errors such as 404
            # -------------------------------------------------------

            response.raise_for_status()

            # -------------------------------------------------------
            # PDF
            # -------------------------------------------------------

            if (
                "application/pdf"
                in content_type
            ):
                reader_result = (
                    _fetch_with_reader(
                        url,
                        response.status_code,
                    )
                )

                if reader_result:
                    reader_result[
                        "source"
                    ] = source

                    return reader_result

                raise RuntimeError(
                    "PDF source could not be "
                    "converted to readable text"
                )

            # -------------------------------------------------------
            # HTML / text
            # -------------------------------------------------------

            raw_text = response.text

            if _looks_like_html(
                content_type,
                raw_text,
            ):
                text = _extract_html_text(
                    raw_text
                )
            else:
                text = normalize_text(
                    raw_text
                )

            # -------------------------------------------------------
            # Empty content
            # -------------------------------------------------------

            if not _is_meaningful_text(
                text
            ):
                reader_result = (
                    _fetch_with_reader(
                        url,
                        response.status_code,
                    )
                )

                if reader_result:
                    reader_result[
                        "source"
                    ] = source

                    return reader_result

                raise RuntimeError(
                    "Source returned "
                    "insufficient readable text"
                )

            return {
                "source": source,
                "resolved_url": response.url,
                "http_status": (
                    response.status_code
                ),
                "content_type": content_type,
                "text": text,
                "retrieval_method": (
                    "direct"
                ),
            }

        except requests.Timeout as exc:
            last_error = (
                f"Timeout: {exc}"
            )

            if attempt < MAX_DIRECT_ATTEMPTS:
                time.sleep(
                    1.5 * attempt
                )
                continue

        except requests.ConnectionError as exc:
            last_error = (
                f"Connection error: {exc}"
            )

            if attempt < MAX_DIRECT_ATTEMPTS:
                time.sleep(
                    1.5 * attempt
                )
                continue

        except requests.HTTPError as exc:
            last_error = str(exc)

            # 404 and similar permanent errors
            # should not be retried endlessly.
            break

        except Exception as exc:
            last_error = str(exc)
            break

    # ---------------------------------------------------------------
    # Last fallback for network/timeouts
    # ---------------------------------------------------------------

    if (
        last_status is None
        or last_status
        in READER_FALLBACK_STATUS_CODES
        or (
            last_error
            and (
                "Timeout" in last_error
                or "Connection error"
                in last_error
            )
        )
    ):
        reader_result = (
            _fetch_with_reader(
                url,
                last_status,
            )
        )

        if reader_result:
            reader_result[
                "source"
            ] = source

            return reader_result

    raise RuntimeError(
        last_error
        or "Unable to retrieve source"
    )


# ---------------------------------------------------------------------------
# One-source ingestion
# ---------------------------------------------------------------------------

def ingest_one_source(
    source: dict[str, Any],
) -> dict[str, Any]:
    """
    Fetch, clean and chunk a single source.
    """

    fetched_at = datetime.now(
        timezone.utc
    ).isoformat()

    try:
        result = fetch_source(
            source
        )

        chunks = chunk_text(
            result["text"]
        )

        if not chunks:
            raise RuntimeError(
                "Source produced zero text chunks"
            )

        records: list[
            dict[str, Any]
        ] = []

        for index, chunk in enumerate(
            chunks
        ):
            records.append(
                {
                    "source_id": source["id"],
                    "chunk_id": (
                        f'{source["id"]}-'
                        f'{index + 1:04d}'
                    ),
                    "chunk_index": index,
                    "publisher": (
                        source["publisher"]
                    ),
                    "title": (
                        source["title"]
                    ),
                    "category": (
                        source["category"]
                    ),
                    "topics": (
                        source.get(
                            "topics",
                            [],
                        )
                    ),
                    "url": source["url"],
                    "resolved_url": (
                        result[
                            "resolved_url"
                        ]
                    ),
                    "retrieval_method": (
                        result.get(
                            "retrieval_method",
                            "unknown",
                        )
                    ),
                    "fetched_at": fetched_at,
                    "http_status": (
                        result[
                            "http_status"
                        ]
                    ),
                    "content_type": (
                        result[
                            "content_type"
                        ]
                    ),
                    "word_count": len(
                        chunk.split()
                    ),
                    "text": chunk,
                }
            )

        return {
            "source_id": source["id"],
            "status": "SUCCESS",
            "url": source["url"],
            "chunk_count": len(records),
            "records": records,
            "error": None,
            "retrieval_method": (
                result.get(
                    "retrieval_method",
                    "unknown",
                )
            ),
        }

    except Exception as exc:
        return {
            "source_id": source["id"],
            "status": "FAILED",
            "url": source["url"],
            "chunk_count": 0,
            "records": [],
            "error": str(exc),
            "retrieval_method": None,
        }


# ---------------------------------------------------------------------------
# Full ingestion
# ---------------------------------------------------------------------------

def ingest_all_sources(
    max_workers: int = 8,
) -> dict[str, Any]:
    """
    Ingest every source in the CareerPilot source registry.
    """

    registry = CareerSourceRegistry()

    sources = registry.sources

    results: list[
        dict[str, Any]
    ] = []

    print(
        ""
    )
    print(
        "========================================"
    )
    print(
        "CareerPilot Week 5 Source Ingestion"
    )
    print(
        "========================================"
    )
    print(
        f"Sources to ingest: {len(sources)}"
    )
    print(
        f"Workers: {max_workers}"
    )
    print(
        ""
    )

    # ---------------------------------------------------------------
    # Concurrent ingestion
    # ---------------------------------------------------------------

    with ThreadPoolExecutor(
        max_workers=max_workers
    ) as executor:

        future_map = {
            executor.submit(
                ingest_one_source,
                source,
            ): source
            for source in sources
        }

        for future in as_completed(
            future_map
        ):
            source = future_map[
                future
            ]

            try:
                result = (
                    future.result()
                )

            except Exception as exc:
                result = {
                    "source_id": (
                        source["id"]
                    ),
                    "status": "FAILED",
                    "url": source["url"],
                    "chunk_count": 0,
                    "records": [],
                    "error": str(exc),
                    "retrieval_method": None,
                }

            results.append(
                result
            )

            method = (
                result.get(
                    "retrieval_method"
                )
                or "none"
            )

            print(
                f'[{result["status"]}] '
                f'{result["source_id"]} '
                f'→ '
                f'{result["chunk_count"]} chunks '
                f'[{method}]'
            )

    # ---------------------------------------------------------------
    # Stable ordering
    # ---------------------------------------------------------------

    results.sort(
        key=lambda item: item[
            "source_id"
        ]
    )

    successful = [
        item
        for item in results
        if item["status"] == "SUCCESS"
    ]

    failed = [
        item
        for item in results
        if item["status"] == "FAILED"
    ]

    # ---------------------------------------------------------------
    # Ensure data directory exists
    # ---------------------------------------------------------------

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------------
    # Write JSONL chunks
    # ---------------------------------------------------------------

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:

        for result in results:
            for record in result[
                "records"
            ]:
                file.write(
                    json.dumps(
                        record,
                        ensure_ascii=False,
                    )
                    + "\n"
                )

    # ---------------------------------------------------------------
    # Retrieval statistics
    # ---------------------------------------------------------------

    retrieval_methods: dict[
        str,
        int,
    ] = {}

    for item in successful:
        method = (
            item.get(
                "retrieval_method"
            )
            or "unknown"
        )

        retrieval_methods[
            method
        ] = (
            retrieval_methods.get(
                method,
                0,
            )
            + 1
        )

    # ---------------------------------------------------------------
    # Manifest
    # ---------------------------------------------------------------

    manifest = {
        "dataset": (
            "CareerPilot AI Week 5 "
            "Source Ingestion"
        ),
        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "expected_sources": len(
            sources
        ),
        "successful_sources": len(
            successful
        ),
        "failed_sources": len(
            failed
        ),
        "total_chunks": sum(
            item[
                "chunk_count"
            ]
            for item in results
        ),
        "retrieval_methods": (
            retrieval_methods
        ),
        "failed": [
            {
                "source_id": item[
                    "source_id"
                ],
                "url": item["url"],
                "error": item["error"],
            }
            for item in failed
        ],
    }

    MANIFEST_PATH.write_text(
        json.dumps(
            manifest,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # ---------------------------------------------------------------
    # Final console summary
    # ---------------------------------------------------------------

    print("")
    print(
        "========================================"
    )
    print(
        "CareerPilot Week 5 Ingestion Complete"
    )
    print(
        "========================================"
    )
    print(
        f"Expected sources : "
        f"{manifest['expected_sources']}"
    )
    print(
        f"Successful        : "
        f"{manifest['successful_sources']}"
    )
    print(
        f"Failed            : "
        f"{manifest['failed_sources']}"
    )
    print(
        f"Total chunks      : "
        f"{manifest['total_chunks']}"
    )
    print(
        f"Retrieval methods : "
        f"{json.dumps(retrieval_methods)}"
    )

    if failed:
        print("")
        print(
            "Failed sources:"
        )

        for item in failed:
            print(
                f'  {item["source_id"]} '
                f'→ {item["error"]}'
            )

    print(
        ""
    )

    return manifest