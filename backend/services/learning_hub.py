from __future__ import annotations

import re
from typing import Any

LEARNING_PROVIDERS: tuple[dict[str, Any], ...] = (
    {"id": "microsoft-learn", "name": "Microsoft Learn", "url": "https://learn.microsoft.com/training/", "search_url": "https://learn.microsoft.com/training/?terms={query}", "category": "official"},
    {"id": "aws-skill-builder", "name": "AWS Skill Builder", "url": "https://skillbuilder.aws/", "search_url": "https://skillbuilder.aws/search?search={query}", "category": "official"},
    {"id": "github-skills", "name": "GitHub Skills", "url": "https://skills.github.com/", "search_url": "https://skills.github.com/", "category": "official"},
    {"id": "google-cloud", "name": "Google Cloud Skills Boost", "url": "https://www.cloudskillsboost.google/", "search_url": "https://www.cloudskillsboost.google/catalog?keywords={query}", "category": "official"},
    {"id": "freecodecamp", "name": "freeCodeCamp", "url": "https://www.freecodecamp.org/learn/", "search_url": "https://www.freecodecamp.org/news/search/?query={query}", "category": "community"},
    {"id": "coursera", "name": "Coursera", "url": "https://www.coursera.org/", "search_url": "https://www.coursera.org/search?query={query}", "category": "learning"},
    {"id": "edx", "name": "edX", "url": "https://www.edx.org/", "search_url": "https://www.edx.org/search?q={query}", "category": "learning"},
)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.strip().lower()).strip("-") or "skill"


def recommendations(skills: list[str], *, limit: int = 12) -> list[dict[str, Any]]:
    normalized = [skill.strip() for skill in skills if skill.strip()]
    result: list[dict[str, Any]] = []
    for skill in normalized[:8]:
        for provider in LEARNING_PROVIDERS:
            result.append({
                "id": f"{provider['id']}:{_slug(skill)}",
                "skill": skill,
                "provider": provider["name"],
                "url": provider["search_url"].format(query=skill.replace(" ", "+")),
                "provider_url": provider["url"],
                "category": provider["category"],
            })
            if len(result) >= limit:
                return result
    return result
