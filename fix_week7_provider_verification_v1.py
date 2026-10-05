from pathlib import Path

ROOT = Path(__file__).resolve().parent
VERIFIER = ROOT / 'backend' / 'services' / 'provider_verifier.py'
TEST = ROOT / 'backend' / 'test_provider_verifier_fallback.py'

text = VERIFIER.read_text(encoding='utf-8')

# 1) Add trace state once, idempotently.
if 'self.last_search_attempt' not in text:
    anchor = '''        self.concurrency = max(\n            1,\n            min(\n                int(concurrency),\n                32,\n            ),\n        )\n'''
    if anchor not in text:
        raise SystemExit('Expected concurrency block not found in provider_verifier.py')
    text = text.replace(anchor, anchor + '''        self.last_search_attempt: dict[str, Any] = {\n            "query": self.query,\n            "location": self.location,\n            "attempts": [],\n        }\n''', 1)

# 2) Replace the narrow single-search verifier with query/location fallbacks.
old = '''    async def _search(\n        self,\n        source: Any,\n    ) -> Any:\n        search = getattr(\n            source,\n            "search",\n            None,\n        )\n\n        if search is None:\n            raise RuntimeError(\n                "Provider source does not implement search()."\n            )\n\n        try:\n            value = search(\n                query=self.query,\n                location=self.location,\n                limit=self.limit,\n            )\n        except TypeError:\n            try:\n                value = search(\n                    self.query,\n                    self.location,\n                    self.limit,\n                )\n            except TypeError:\n                value = search(\n                    self.query\n                )\n\n        if inspect.isawaitable(\n            value\n        ):\n            return await value\n\n        return value\n'''
new = '''    async def _search(\n        self,\n        source: Any,\n    ) -> Any:\n        search = getattr(\n            source,\n            "search",\n            None,\n        )\n\n        if search is None:\n            raise RuntimeError(\n                "Provider source does not implement search()."\n            )\n\n        # Provider verification must not classify a healthy employer board as\n        # degraded merely because one narrow query/location pair has no match.\n        # Keep the requested query first, then broaden only for verification.\n        attempts = [\n            (self.query, self.location),\n            ("engineer", ""),\n            ("developer", ""),\n            ("software", ""),\n            ("data", ""),\n            ("product", ""),\n            ("", ""),\n        ]\n        seen: set[tuple[str, str]] = set()\n        attempt_log: list[dict[str, Any]] = []\n\n        for query, location in attempts:\n            pair = (str(query or "").strip(), str(location or "").strip())\n            if pair in seen:\n                continue\n            seen.add(pair)\n\n            try:\n                try:\n                    value = search(\n                        query=pair[0],\n                        location=pair[1],\n                        limit=self.limit,\n                    )\n                except TypeError:\n                    try:\n                        value = search(\n                            pair[0],\n                            pair[1],\n                            self.limit,\n                        )\n                    except TypeError:\n                        value = search(pair[0])\n\n                if inspect.isawaitable(value):\n                    value = await value\n\n                count = len(self._coerce_sequence(value))\n                attempt_log.append({\n                    "query": pair[0],\n                    "location": pair[1],\n                    "jobs_returned": count,\n                })\n\n                if count > 0:\n                    self.last_search_attempt = {\n                        "query": pair[0],\n                        "location": pair[1],\n                        "attempts": attempt_log,\n                    }\n                    return value\n            except Exception as exc:\n                attempt_log.append({\n                    "query": pair[0],\n                    "location": pair[1],\n                    "error": str(exc),\n                })\n\n        self.last_search_attempt = {\n            "query": self.query,\n            "location": self.location,\n            "attempts": attempt_log,\n        }\n        return []\n'''
if old in text:
    text = text.replace(old, new, 1)
elif 'progressively broader' not in text and 'Provider verification must not classify' not in text:
    raise SystemExit('Expected _search block not found; refusing unsafe patch.')

# 3) Persist which fallback actually supplied evidence.
needle = '''            result.evidence[\n                "normalization"\n            ] = {\n'''
if needle in text and 'result.evidence[\n                "search"\n            ]' not in text:
    text = text.replace(needle, '''            result.evidence[\n                "search"\n            ] = dict(self.last_search_attempt)\n\n            result.evidence[\n                "normalization"\n            ] = {\n''', 1)

VERIFIER.write_text(text, encoding='utf-8')

# 4) Add a regression test proving fallback search is actually used.
if not TEST.exists():
    TEST.write_text('''from __future__ import annotations\n\nfrom datetime import datetime, timezone\nfrom types import SimpleNamespace\n\nfrom backend.services.provider_verifier import (\n    ProviderFleetVerifier,\n    ProviderVerificationState,\n)\n\n\ndef make_definition():\n    return SimpleNamespace(\n        name="fallback_live",\n        display_name="Fallback Live",\n        adapter_type="json",\n    )\n\n\nclass FallbackSource:\n    name = "fallback_live"\n    display_name = "Fallback Live"\n    category = "test"\n    requires_credentials = False\n    credential_env_vars = []\n\n    def validate_configuration(self):\n        return True\n\n    def health_check(self):\n        return {"healthy": True, "status": "healthy"}\n\n    def search(self, query, location, limit=5):\n        if query == "software engineer" and location == "remote":\n            return []\n        return [{\n            "title": "Engineer",\n            "company": "CareerPilot Test",\n            "location": ["New York"],\n            "url": "https://example.com/jobs/fallback",\n            "posted_at": datetime.now(timezone.utc).isoformat(),\n            "metadata": {"provider_name": "fallback_live"},\n        }]\n\n    def normalize(self, item):\n        return item\n\n\nclass FakeFleet:\n    def build_source(self, definition):\n        return FallbackSource()\n\n    def list_definitions(self):\n        return [make_definition()]\n\n\ndef test_verifier_uses_broader_search_when_primary_is_empty():\n    verifier = ProviderFleetVerifier(\n        FakeFleet(),\n        query="software engineer",\n        location="remote",\n    )\n\n    result = verifier.verify(make_definition())\n\n    assert result.state is ProviderVerificationState.LIVE\n    assert result.jobs_returned == 1\n    assert result.evidence["search"]["query"] == "engineer"\n    assert result.evidence["search"]["location"] == ""\n    assert len(result.evidence["search"]["attempts"]) >= 2\n''', encoding='utf-8')

print('Provider verification fallback patch complete.')
print('Updated:', VERIFIER)
print('Added:', TEST)
print('Next: python -m pytest -q backend/test_provider_verifier.py backend/test_provider_verifier_fallback.py')
print('Then: python -m backend.tools.verify_job_sources --target 128 --concurrency 16 --json')
