"""
CareerPilot AI - Bulk Live Job Source Verification.

This command verifies the curated first-party ATS provider catalog against
real provider endpoints.

IMPORTANT:
    Catalog membership does NOT mean LIVE.

A provider becomes LIVE only after passing:
    1. definition validation
    2. adapter construction
    3. configuration validation
    4. health check
    5. real job retrieval
    6. normalization
    7. provider provenance
    8. usable job URL
    9. freshness validation

Usage:
    python -m backend.tools.verify_job_sources

Examples:
    python -m backend.tools.verify_job_sources --limit 10
    python -m backend.tools.verify_job_sources --query "backend engineer"
    python -m backend.tools.verify_job_sources --location "India"
    python -m backend.tools.verify_job_sources --concurrency 12
    python -m backend.tools.verify_job_sources --target 128
    python -m backend.tools.verify_job_sources --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from backend.data.provider_catalog import (
    CATALOG_TARGET,
    build_provider_catalog,
    catalog_summary,
)
from backend.services.provider_fleet import ProviderFleet
from backend.services.provider_verifier import (
    ProviderFleetVerifier,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Bulk-verify CareerPilot's real first-party "
            "job-source catalog."
        )
    )

    parser.add_argument(
        "--query",
        default="software engineer",
        help=(
            "Real search query used against each provider."
        ),
    )

    parser.add_argument(
        "--location",
        default="remote",
        help=(
            "Real location used against each provider."
        ),
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help=(
            "Maximum number of jobs requested per provider."
        ),
    )

    parser.add_argument(
        "--freshness-days",
        type=int,
        default=180,
        help=(
            "Maximum accepted age of freshness evidence."
        ),
    )

    parser.add_argument(
        "--concurrency",
        type=int,
        default=8,
        help=(
            "Maximum providers checked concurrently."
        ),
    )

    parser.add_argument(
        "--target",
        type=int,
        default=CATALOG_TARGET,
        help=(
            "Number of catalog candidates to verify."
        ),
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help=(
            "Print the complete JSON verification result."
        ),
    )

    parser.add_argument(
        "--output",
        default=(
            "backend/data/provider_verification.json"
        ),
        help=(
            "Path for the detailed verification report."
        ),
    )

    return parser


def print_catalog_header(
    *,
    target: int,
    summary: dict[str, Any],
) -> None:
    print()
    print("=" * 96)
    print("CAREERPILOT AI — PROVIDER CATALOG")
    print("=" * 96)

    print(
        f"Candidate target : {target}"
    )

    print(
        f"Candidate count  : "
        f"{summary['candidate_count']}"
    )

    print(
        f"Unique names     : "
        f"{summary['unique_names']}"
    )

    print(
        f"Platform counts  : "
        f"{summary['platform_counts']}"
    )

    print("=" * 96)
    print()


def print_verification_summary(
    summary: Any,
) -> None:
    payload = summary.to_dict()

    print()
    print("=" * 96)
    print("CAREERPILOT AI — LIVE PROVIDER VERIFICATION")
    print("=" * 96)

    print(
        f"Total candidates : {summary.total}"
    )

    print(
        f"LIVE             : {summary.live}"
    )

    print(
        f"CONFIGURED       : {summary.configured}"
    )

    print(
        f"DEGRADED         : {summary.degraded}"
    )

    print(
        f"OFFLINE          : {summary.offline}"
    )

    print(
        f"UNVERIFIED       : {summary.unverified}"
    )

    print(
        f"REJECTED         : {summary.rejected}"
    )

    print()

    print(
        f"LIVE percentage  : "
        f"{payload['live_percentage']:.2f}%"
    )

    print()

    print(
        f"Jobs returned    : "
        f"{summary.jobs_returned}"
    )

    print(
        f"Jobs normalized  : "
        f"{summary.jobs_normalized}"
    )

    print(
        f"With provenance  : "
        f"{summary.jobs_with_provenance}"
    )

    print(
        f"With URL         : "
        f"{summary.jobs_with_url}"
    )

    print(
        f"Fresh evidence   : "
        f"{summary.fresh_jobs}"
    )

    print("=" * 96)
    print()

    print(
        f"{'Provider':<38}"
        f"{'Adapter':<14}"
        f"{'State':<14}"
        f"{'Jobs':>7}"
        f"{'Norm':>7}"
        f"{'Fresh':>8}"
        f"{'Latency':>11}"
        f"  Message"
    )

    print("-" * 140)

    for result in sorted(
        summary.results,
        key=lambda item: (
            item.state.value,
            item.name.lower(),
        ),
    ):
        message = (
            result.message or ""
        ).strip()

        if len(message) > 48:
            message = (
                message[:45]
                + "..."
            )

        print(
            f"{result.name[:37]:<38}"
            f"{result.adapter_type[:13]:<14}"
            f"{result.state.value:<14}"
            f"{result.jobs_returned:>7}"
            f"{result.jobs_normalized:>7}"
            f"{result.fresh_jobs:>8}"
            f"{result.latency_ms:>9.1f}ms"
            f"  {message}"
        )

    print()


def write_report(
    path: str,
    payload: dict[str, Any],
) -> None:
    destination = Path(path)

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def main() -> int:
    args = build_parser().parse_args()

    # --------------------------------------------------------------
    # 1. Build curated provider catalog
    # --------------------------------------------------------------
    try:
        definitions = build_provider_catalog(
            target=args.target,
        )

        catalog_info = catalog_summary(
            target=args.target,
        )

    except Exception as exc:
        print(
            f"Could not build provider catalog: {exc}",
            file=sys.stderr,
        )
        return 2

    if not definitions:
        print(
            "Provider catalog is empty.",
            file=sys.stderr,
        )
        return 2

    if len(definitions) != args.target:
        print(
            (
                "Provider catalog size mismatch: "
                f"expected {args.target}, "
                f"got {len(definitions)}"
            ),
            file=sys.stderr,
        )
        return 2

    print_catalog_header(
        target=args.target,
        summary=catalog_info,
    )

    # --------------------------------------------------------------
    # 2. Construct ProviderFleet from the actual catalog.
    #
    # The current ProviderFleet contract requires definitions in its
    # constructor, so the 128 catalog entries become the fleet itself.
    # --------------------------------------------------------------
    try:
        fleet = ProviderFleet(
            definitions
        )

    except Exception as exc:
        print(
            f"Could not initialize provider fleet: {exc}",
            file=sys.stderr,
        )
        return 3

    # --------------------------------------------------------------
    # 3. Construct real bulk verifier
    # --------------------------------------------------------------
    verifier = ProviderFleetVerifier(
        fleet,
        query=args.query,
        location=args.location,
        limit=args.limit,
        freshness_days=args.freshness_days,
        concurrency=args.concurrency,
    )

    # --------------------------------------------------------------
    # 4. Verify every catalog definition against the real endpoint
    # --------------------------------------------------------------
    try:
        summary = verifier.verify_all(
            definitions
        )

    except KeyboardInterrupt:
        print(
            "\nVerification interrupted.",
            file=sys.stderr,
        )
        return 130

    except Exception as exc:
        print(
            f"Bulk verification failed: {exc}",
            file=sys.stderr,
        )
        return 4

    # --------------------------------------------------------------
    # 5. Build complete report
    # --------------------------------------------------------------
    payload = summary.to_dict()

    payload["catalog"] = {
        "target": args.target,
        "candidate_count": len(
            definitions
        ),
        "platform_counts": catalog_info[
            "platform_counts"
        ],
    }

    payload["verification_parameters"] = {
        "query": args.query,
        "location": args.location,
        "limit": args.limit,
        "freshness_days": (
            args.freshness_days
        ),
        "concurrency": args.concurrency,
    }

    payload["admission_policy"] = {
        "configured_is_not_live": True,
        "live_requires_real_jobs": True,
        "live_requires_normalization": True,
        "live_requires_provenance": True,
        "live_requires_job_url": True,
        "live_requires_freshness": True,
    }

    write_report(
        args.output,
        payload,
    )

    # --------------------------------------------------------------
    # 6. Output result
    # --------------------------------------------------------------
    if args.json:
        print(
            json.dumps(
                payload,
                indent=2,
                ensure_ascii=False,
            )
        )

    else:
        print_verification_summary(
            summary
        )

        print(
            f"Detailed report saved to: "
            f"{args.output}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )