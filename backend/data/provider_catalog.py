"""
CareerPilot AI - First-party job source catalog.

This catalog contains candidate company-level ATS job-board endpoints.

Important:
    A catalog entry is NOT automatically LIVE.

Every candidate must pass the CareerPilot live verification pipeline:
    configuration
    -> adapter construction
    -> health
    -> real search
    -> real jobs
    -> normalization
    -> provenance
    -> usable URL
    -> freshness

The current target is 128 candidate endpoints.

Supported public ATS families:
    - Greenhouse
    - Lever
    - Ashby

The catalog deliberately treats each company's public job-board endpoint as
its own source endpoint. This gives CareerPilot genuine first-party coverage
while preserving source-level provenance.

Reference material used when curating candidates:
    - Greenhouse public Job Board API
    - Lever public Postings API
    - Ashby public Job Postings API

Runtime verification remains authoritative.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from backend.schemas.provider_fleet import ProviderDefinition


CATALOG_TARGET = 128


GREENHOUSE_CANDIDATES: tuple[str, ...] = (
    # Core tech / fintech
    "stripe",
    "figma",
    "anthropic",
    "robinhood",
    "brex",
    "databricks",
    "deepmind",
    "coinbase",
    "affirm",
    "block",
    "chime",
    "sofi",
    "upstart",
    "carta",
    "gusto",

    # Consumer / product / infrastructure
    "airbnb",
    "reddit",
    "pinterest",
    "discord",
    "cloudflare",
    "datadog",
    "amplitude",
    "vercel",
    "lyft",
    "doordashusa",
    "instacart",
    "roblox",
    "dropbox",
    "twilio",
    "okta",
    "mongodb",
    "elastic",
    "samsara",
    "verkada",
    "duolingo",
    "linkedin",
    "asana",
    "gitlab",
    "klaviyo",
    "rubrik",
    "toast",
    "twitch",
    "zscaler",
    "squarespace",
    "nextdoor",
    "oscar",
    "flexport",
    "checkr",
    "cockroachlabs",

    # AI / ML
    "xai",
    "scaleai",
    "togetherai",
    "gleanwork",
    "snorkelai",
    "assemblyai",
    "sambanovasystems",
    "tenstorrent",
    "lightmatter",

    # Autonomy / robotics
    "waymo",
    "nuro",
    "wayve",

    # Quant / trading
    "janestreet",
    "jumptrading",
    "imc",
    "optiverus",
    "drweng",
    "akunacapital",
    "point72",

    # Additional engineering / SaaS
    "airtable",
    "coreweave",
    "databento",
    "fastly",
    "figure",
    "fivetran",
    "grafanalabs",
    "imbue",
    "invisibletech",
    "knock",
    "labelbox",
    "lucidmotors",
    "mercury",
    "mixpanel",
    "motional",
    "netlify",
    "planetscale",
    "roku",
    "singlestore",
    "webflow",
    "yugabyte",

    # Additional established boards
    "notion",
    "loom",
    "miro",
    "retool",
    "linear",
    "hubspot",
    "gong",
    "outreach",
    "salesloft",
    "clari",
    "coda",
    "framer",
    "canva",
    "lattice",
    "cultureamp",
    "leapsome",
    "personio",
    "workato",
    "zapier",
    "hashicorp",
    "confluent",
    "sentry",
    "postman",
    "netlify",
    "digitalocean",
    "harness",
    "temporal",
    "stytch",
    "snyk",
    "celonis",
    "contentful",
    "segment",
    "abnormalsecurity",
    "wiz",
    "vectra",
    "anduril",
    "cohere",
    "modal",
    "baseten",
    "plaid",
    "marqeta",
    "ramp",
    "rippling",
    "deel",
    "remote",
    "moderntreasury",
    "column",
    "chainalysis",
    "alchemy",
    "consensys",
    "coursera",
    "masterclass",
    "chegg",
    "olo",
    "opendoor",
    "opentable",
    "faire",
    "eventbrite",
    "benchling",
    "ginkgobioworks",
    "tempus",
    "hims",
    "ro",
    "flatironhealth",
    "verily",
    "aurorainc",
    "cruise",
    "motional",
    "niantic",
    "calm",
    "headspace",
    "peloton",
    "strava",
    "hinge",
    "bumble",
    "cloudkitchens",
    "dutchie",
    "sonder",
    "hippo",
    "gopuff",
)


LEVER_CANDIDATES: tuple[str, ...] = (
    "anyscale",
    "palantir",
    "zoox",
    "spotify",
    "waabi",
    "wealthfront",
    "neon",
    "zilliz",
    "meesho",
    "fampay",
    "cred",
    "veeva",
    "swordhealth",
    "matchgroup",
    "samsara",
    "postman",
)


ASHBY_CANDIDATES: tuple[str, ...] = (
    # AI / AI infrastructure
    "openai",
    "perplexity",
    "cursor",
    "cohere",
    "cerebras",
    "harvey",
    "sierra",
    "decagon",
    "elevenlabs",
    "etched",
    "cognition",
    "deepgram",
    "fireworks",
    "suno",
    "midjourney",
    "poolside",
    "character",
    "runway",

    # Developer tools / infrastructure
    "Ashby",
    "notion",
    "ramp",
    "plaid",
    "snowflake",
    "replit",
    "supabase",
    "temporal",
    "modal",
    "linear",
    "sentry",
    "render",
    "railway",
    "benchling",

    # Consumer / autonomy / marketplaces
    "applied",
    "handshake",
    "substack",
    "thumbtack",
    "miro",

    # Additional live boards from recent public-board verification lists
    "airbyte",
    "astronomer",
    "baseten",
    "clerk",
    "clickhouse",
    "confluent",
    "docker",
    "inngest",
    "langchain",
    "llamaindex",
    "lumaai",
    "materialize",
    "nousresearch",
    "physicalintelligence",
    "pinecone",
    "posthog",
    "prefect",
    "reflectionai",
    "resend",
    "trychroma",
    "weaviate",
    "workos",
    "worldlabs",
    "zapier",
    "zed",

    # Additional public boards
    "linear",
    "vanta",
    "vercel",
    "warp",
    "watershed",
    "zip",
    "mercury",
    "deel",
    "replit",
    "neon",
    "hex",
    "browserbase",
    "modal",
)


_PLATFORM_ENDPOINTS: dict[str, dict[str, Any]] = {
    "greenhouse": {
        "endpoint_template": (
            "https://boards-api.greenhouse.io/v1/boards/"
            "{board}/jobs?content=true"
        ),
        "website_template": (
            "https://boards.greenhouse.io/{board}"
        ),
        "api_url": "https://boards-api.greenhouse.io",
        "supports_remote_filter": False,
        "supports_salary_filter": False,
    },
    "lever": {
        "endpoint_template": (
            "https://api.lever.co/v0/postings/"
            "{board}?mode=json"
        ),
        "website_template": (
            "https://jobs.lever.co/{board}"
        ),
        "api_url": "https://api.lever.co",
        "supports_remote_filter": False,
        "supports_salary_filter": False,
    },
    "ashby": {
        "endpoint_template": (
            "https://api.ashbyhq.com/posting-api/job-board/"
            "{board}"
        ),
        "website_template": (
            "https://jobs.ashbyhq.com/{board}"
        ),
        "api_url": "https://api.ashbyhq.com",
        "supports_remote_filter": False,
        "supports_salary_filter": True,
    },
}


def _supported_definition_fields() -> set[str]:
    """
    Discover ProviderDefinition fields without coupling the catalog to a
    specific Pydantic major version.
    """
    model_fields = getattr(
        ProviderDefinition,
        "model_fields",
        None,
    )

    if isinstance(model_fields, dict):
        return set(model_fields)

    legacy_fields = getattr(
        ProviderDefinition,
        "__fields__",
        None,
    )

    if isinstance(legacy_fields, dict):
        return set(legacy_fields)

    return set()


def _make_definition(
    *,
    platform: str,
    board: str,
    display_name: str | None = None,
    notes: str | None = None,
) -> ProviderDefinition:
    if platform not in _PLATFORM_ENDPOINTS:
        raise ValueError(
            f"Unsupported ATS platform: {platform}"
        )

    config = _PLATFORM_ENDPOINTS[platform]

    clean_board = str(board).strip()

    if not clean_board:
        raise ValueError(
            "Provider board slug cannot be empty."
        )

    definition_name = (
        f"ats_{platform}_{clean_board.lower()}"
    )

    payload: dict[str, Any] = {
        "name": definition_name,
        "display_name": (
            display_name
            or f"{clean_board} ({platform.title()})"
        ),
        "adapter_type": "ats_public",
        "endpoint": config["endpoint_template"].format(
            board=clean_board
        ),
        "category": "first_party_ats",
        "countries": ["GLOBAL"],
        "requires_credentials": False,
        "supports_paging": True,
        "supports_remote_filter": config[
            "supports_remote_filter"
        ],
        "supports_salary_filter": config[
            "supports_salary_filter"
        ],
        "website": config["website_template"].format(
            board=clean_board
        ),
        "api_url": config["api_url"],
        "enabled": True,
        "tags": [
            "first_party",
            "public",
            "ats",
            platform,
        ],
        "notes": (
            notes
            or (
                "Candidate source. "
                "Not counted as LIVE until CareerPilot "
                "real-world verification succeeds."
            )
        ),
        "adapter_config": {
            "platform": platform,
            "board": clean_board,
        },
    }

    supported_fields = (
        _supported_definition_fields()
    )

    if supported_fields:
        payload = {
            key: value
            for key, value in payload.items()
            if key in supported_fields
        }

    try:
        return ProviderDefinition(**payload)

    except TypeError as exc:
        # Useful compatibility path if the schema is changed later.
        reduced = {
            key: value
            for key, value in payload.items()
            if key in {
                "name",
                "display_name",
                "adapter_type",
                "endpoint",
                "category",
                "countries",
                "adapter_config",
            }
        }

        try:
            return ProviderDefinition(**reduced)
        except Exception:
            raise exc


def _round_robin_sources(
    sources: dict[str, tuple[str, ...]],
    target: int,
) -> list[tuple[str, str]]:
    """
    Select candidates fairly across ATS families.

    Instead of filling the entire catalog with Greenhouse first, sources are
    interleaved across platforms until the target count is reached.
    """
    if target <= 0:
        return []

    prepared = {
        platform: list(slugs)
        for platform, slugs in sources.items()
    }

    cursors = {
        platform: 0
        for platform in prepared
    }

    selected: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    platforms = list(prepared)

    while len(selected) < target:
        progress = False

        for platform in platforms:
            items = prepared[platform]
            cursor = cursors[platform]

            while cursor < len(items):
                slug = items[cursor]
                cursors[platform] += 1

                key = (
                    platform,
                    slug.lower(),
                )

                if key in seen:
                    continue

                seen.add(key)
                selected.append(
                    (
                        platform,
                        slug,
                    )
                )
                progress = True
                break

            if len(selected) >= target:
                break

        if not progress:
            break

    return selected


def build_provider_catalog(
    target: int = CATALOG_TARGET,
) -> list[ProviderDefinition]:
    """
    Build the current first-party ATS candidate catalog.

    The function returns at most `target` unique endpoints and refuses to
    silently return a smaller fleet unless the candidate pool genuinely does
    not contain enough unique entries.
    """
    target = int(target)

    if target <= 0:
        return []

    sources = {
        "greenhouse": GREENHOUSE_CANDIDATES,
        "lever": LEVER_CANDIDATES,
        "ashby": ASHBY_CANDIDATES,
    }

    selected = _round_robin_sources(
        sources,
        target,
    )

    definitions: list[ProviderDefinition] = []

    for platform, board in selected:
        definition = _make_definition(
            platform=platform,
            board=board,
        )
        definitions.append(definition)

    return definitions


def catalog_names(
    target: int = CATALOG_TARGET,
) -> list[str]:
    return [
        str(
            getattr(
                definition,
                "name",
                "",
            )
        )
        for definition in build_provider_catalog(
            target
        )
    ]


def catalog_summary(
    target: int = CATALOG_TARGET,
) -> dict[str, Any]:
    definitions = build_provider_catalog(
        target
    )

    platform_counts: Counter[str] = Counter()

    for definition in definitions:
        config = getattr(
            definition,
            "adapter_config",
            {},
        )

        platform = (
            config.get("platform")
            if isinstance(config, dict)
            else None
        )

        platform_counts[
            str(platform or "unknown")
        ] += 1

    return {
        "target": target,
        "candidate_count": len(
            definitions
        ),
        "unique_names": len(
            {
                getattr(
                    definition,
                    "name",
                    None,
                )
                for definition in definitions
            }
        ),
        "platform_counts": dict(
            platform_counts
        ),
    }


def iter_provider_catalog(
    target: int = CATALOG_TARGET,
):
    yield from build_provider_catalog(
        target
    )