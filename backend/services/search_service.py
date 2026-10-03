from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from backend.api.models import (
    JobResult,
    MatchBreakdown,
    SalarySummary,
    SourceRecord,
    SourceSummary,
)

from backend.connectors.adzuna import AdzunaConnector
from backend.connectors.base import JobSource
from backend.connectors.jooble import JoobleConnector
from backend.connectors.themuse import TheMuseConnector
from backend.connectors.usajobs import USAJobsConnector

from backend.data.provider_catalog import (
    CATALOG_TARGET,
    build_provider_catalog,
)

from backend.schemas.candidate import CandidateProfile

from backend.services.career_gap_intelligence import (
    CareerGapIntelligence,
)

from backend.services.career_twin import (
    get_or_create,
)

from backend.services.career_twin_job_intelligence import (
    CareerTwinJobIntelligence,
)

from backend.services.career_twin_market_intelligence import (
    CareerTwinMarketIntelligence,
)

from backend.services.career_twin_opportunity_pipeline import (
    CareerTwinOpportunityPipeline,
)

from backend.services.career_twin_timeline import (
    CareerTwinTimeline,
)

from backend.services.deduplication import JobDeduplicator
from backend.services.final_matcher import FinalMatchEngine
from backend.services.job_aggregator import JobAggregator
from backend.services.job_filter import JobFilter
from backend.services.provider_fleet import ProviderFleet
from backend.services.requirements_extractor import (
    JobRequirementsExtractor,
)
from backend.services.salary_intelligence import (
    SalaryIntelligence,
)


class CareerSearchService:
    """
    Production CareerPilot opportunity pipeline.

    Architecture:

        Provider verification
              ↓
        LIVE provider admission
              ↓
        Adzuna + Jooble + verified ATS fleet
              ↓
        Concurrent aggregation
              ↓
        Same-source deduplication
              ↓
        Cross-source deduplication
              ↓
        Salary intelligence
              ↓
        Candidate filtering
              ↓
        Requirements extraction
              ↓
        Hybrid candidate/job matching
              ↓
        Career Twin personalization
              ↓
        Live-market requirement intelligence
              ↓
        Career-gap intelligence
              ↓
        Career timeline
              ↓
        Source-aware response
              ↓
        Final ranking

    Important architectural rule:

        Core job discovery remains independent of Career Twin.

    Career Twin is an enrichment + feedback layer. A Career Twin
    failure must never make the production opportunity search fail.
    """

    BASELINE_PROVIDER_NAMES = {
        "adzuna",
        "jooble",
    }

    PROVIDER_VERIFICATION_FILE = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "provider_verification.json"
    )

    def __init__(
        self,
        sources: Optional[List[JobSource]] = None,
    ) -> None:

        # --------------------------------------------------
        # Provider telemetry
        # --------------------------------------------------

        self.total_catalog_candidates = 0
        self.verified_live_provider_count = 0
        self.connected_provider_count = 0

        # --------------------------------------------------
        # Career Twin request telemetry
        # --------------------------------------------------

        self.last_career_twin_intelligence: List[
            Dict[str, Any]
        ] = []

        self.last_requirement_aggregation: Dict[
            str,
            Any,
        ] = {}

        self.last_market_intelligence: Dict[
            str,
            Any,
        ] = {}

        self.last_career_gap_intelligence: Dict[
            str,
            Any,
        ] = {}

        self.last_career_timeline: Dict[
            str,
            Any,
        ] = {}

        self.last_career_twin_sync: Dict[
            str,
            Any,
        ] = {}

        self.career_twin_errors: List[
            Dict[str, Any]
        ] = []

        # --------------------------------------------------
        # Build production provider set
        # --------------------------------------------------

        configured_sources = (
            sources
            if sources is not None
            else self._build_production_sources()
        )

        self.aggregator = JobAggregator(
            sources=configured_sources
        )

        self.connected_provider_count = len(
            configured_sources
        )

        # --------------------------------------------------
        # Core opportunity pipeline
        # --------------------------------------------------

        self.deduplicator = JobDeduplicator()

        self.salary_intelligence = (
            SalaryIntelligence()
        )

        self.filter = JobFilter()

        self.requirements_extractor = (
            JobRequirementsExtractor()
        )

        self.match_engine = FinalMatchEngine()

        # --------------------------------------------------
        # Career Twin opportunity intelligence
        # --------------------------------------------------

        self.career_twin_pipeline = (
            CareerTwinOpportunityPipeline()
        )

        self.career_twin_job_intelligence = (
            CareerTwinJobIntelligence()
        )

        self.career_twin_market_intelligence = (
            CareerTwinMarketIntelligence()
        )

        self.career_gap_intelligence = (
            CareerGapIntelligence()
        )

        self.career_timeline = (
            CareerTwinTimeline()
        )

        # --------------------------------------------------
        # Provider admission state
        # --------------------------------------------------

        self.provider_admission_state = (
            self._build_provider_admission_state(
                configured_sources
            )
        )

    # ======================================================
    # PRODUCTION PROVIDER FLEET
    # ======================================================

    def _build_production_sources(
        self,
    ) -> List[JobSource]:
        """
        Build CareerPilot's production provider fleet.

        Baseline:
            - Adzuna
            - Jooble

        Verified fleet:
            - Only providers whose persisted verification
              state is LIVE.

        The 128-provider verification process is NOT
        executed during a normal user search.
        """

        # --------------------------------------------------
        # Baseline providers
        # --------------------------------------------------

        baseline_sources: List[JobSource] = [
            AdzunaConnector(
                country="in"
            ),
            JoobleConnector(),
            TheMuseConnector(),
        ]

        # USAJOBS is a credentialed official government API. Only admit it
        # when the operator has configured the required API key + user-agent.
        if __import__("os").getenv("USAJOBS_API_KEY") and __import__("os").getenv("USAJOBS_USER_AGENT"):
            baseline_sources.append(USAJobsConnector())

        # --------------------------------------------------
        # Load verified LIVE provider names
        # --------------------------------------------------

        live_provider_names = (
            self._load_live_provider_names()
        )

        if not live_provider_names:
            return baseline_sources

        # --------------------------------------------------
        # Build canonical provider catalog
        # --------------------------------------------------

        try:
            definitions = build_provider_catalog(
                target=CATALOG_TARGET
            )

        except Exception as exc:

            print(
                "[CareerSearchService] "
                "Provider catalog build failed: "
                f"{exc}"
            )

            return baseline_sources

        self.total_catalog_candidates = len(
            definitions
        )

        # --------------------------------------------------
        # Build provider fleet
        # --------------------------------------------------

        try:
            fleet = ProviderFleet(
                definitions
            )

        except Exception as exc:

            print(
                "[CareerSearchService] "
                "Provider fleet construction failed: "
                f"{exc}"
            )

            return baseline_sources

        # --------------------------------------------------
        # Admit LIVE providers only
        # --------------------------------------------------

        live_sources: List[
            JobSource
        ] = []

        for definition in definitions:

            provider_name = str(
                getattr(
                    definition,
                    "name",
                    "",
                )
                or ""
            ).strip()

            if not provider_name:
                continue

            if (
                provider_name
                not in live_provider_names
            ):
                continue

            try:

                source = fleet.build_source(
                    definition
                )

                if source is None:
                    continue

                live_sources.append(
                    source
                )

            except Exception as exc:

                print(
                    "[CareerSearchService] "
                    f"Skipping provider "
                    f"{provider_name}: "
                    f"{exc}"
                )

        self.verified_live_provider_count = (
            len(live_sources)
        )

        print(
            "[CareerSearchService] "
            f"Verified LIVE providers connected: "
            f"{self.verified_live_provider_count}"
        )

        return (
            baseline_sources
            + live_sources
        )

    # ======================================================
    # LOAD LIVE PROVIDERS
    # ======================================================

    def _load_live_provider_names(
        self,
    ) -> Set[str]:
        """
        Load provider names whose persisted verifier state
        is LIVE.
        """

        path = (
            self.PROVIDER_VERIFICATION_FILE
        )

        if not path.exists():

            print(
                "[CareerSearchService] "
                "Provider verification report not found. "
                "Using baseline providers only."
            )

            return set()

        try:

            with path.open(
                "r",
                encoding="utf-8",
            ) as handle:

                payload = json.load(
                    handle
                )

        except Exception as exc:

            print(
                "[CareerSearchService] "
                "Could not read provider verification "
                f"report: {exc}"
            )

            return set()

        rows = self._extract_verification_rows(
            payload
        )

        live_names: Set[str] = set()

        for row in rows:

            if not isinstance(
                row,
                dict,
            ):
                continue

            name = (
                row.get("name")
                or row.get("provider")
                or row.get("source")
                or row.get("provider_name")
            )

            state = (
                row.get("state")
                or row.get("status")
            )

            nested_verification = row.get(
                "verification"
            )

            if (
                not state
                and isinstance(
                    nested_verification,
                    dict,
                )
            ):

                state = (
                    nested_verification.get(
                        "state"
                    )
                    or nested_verification.get(
                        "status"
                    )
                )

            if not name or not state:
                continue

            if (
                str(state)
                .strip()
                .upper()
                == "LIVE"
            ):

                live_names.add(
                    str(name).strip()
                )

        print(
            "[CareerSearchService] "
            f"Verified LIVE providers loaded: "
            f"{len(live_names)}"
        )

        return live_names

    # ======================================================
    # VERIFICATION REPORT PARSING
    # ======================================================

    @classmethod
    def _extract_verification_rows(
        cls,
        payload: Any,
    ) -> List[Dict[str, Any]]:
        """
        Extract provider verification rows from the
        persisted report.

        Supports list-based and mapping-based report layouts.
        """

        if not isinstance(
            payload,
            dict,
        ):
            return []

        rows: List[
            Dict[str, Any]
        ] = []

        # --------------------------------------------------
        # Standard list containers
        # --------------------------------------------------

        for key in (
            "results",
            "providers",
            "verifications",
            "items",
            "entries",
        ):

            value = payload.get(
                key
            )

            if not isinstance(
                value,
                list,
            ):
                continue

            rows.extend(
                item
                for item in value
                if isinstance(
                    item,
                    dict,
                )
            )

        if rows:
            return rows

        # --------------------------------------------------
        # Nested containers
        # --------------------------------------------------

        for key in (
            "verification",
            "provider_verification",
            "data",
        ):

            value = payload.get(
                key
            )

            if isinstance(
                value,
                dict,
            ):

                nested_rows = (
                    cls._extract_verification_rows(
                        value
                    )
                )

                if nested_rows:
                    rows.extend(
                        nested_rows
                    )

        if rows:
            return rows

        # --------------------------------------------------
        # Mapping-style report
        # --------------------------------------------------

        for key, value in payload.items():

            if not isinstance(
                value,
                dict,
            ):
                continue

            state = (
                value.get("state")
                or value.get("status")
            )

            if state:

                rows.append(
                    {
                        "name": key,
                        **value,
                    }
                )

        return rows

    # ======================================================
    # PROVIDER ADMISSION STATUS
    # ======================================================

    @staticmethod
    def _build_provider_admission_state(
        sources: List[JobSource],
    ) -> Dict[str, str]:

        state: Dict[
            str,
            str,
        ] = {}

        for source in sources:

            source_name = str(
                getattr(
                    source,
                    "name",
                    source.__class__.__name__,
                )
            )

            if (
                source_name
                in CareerSearchService.BASELINE_PROVIDER_NAMES
            ):

                state[
                    source_name
                ] = "BASELINE"

            else:

                state[
                    source_name
                ] = "LIVE_VERIFIED"

        return state

    # ======================================================
    # PROVIDER STATUS
    # ======================================================

    def get_provider_status(
        self,
    ) -> Dict[str, Any]:
        """
        Runtime provider-fleet diagnostics.
        """

        live_verified = [
            name
            for name, state
            in self.provider_admission_state.items()
            if state
            == "LIVE_VERIFIED"
        ]

        baseline = [
            name
            for name, state
            in self.provider_admission_state.items()
            if state
            == "BASELINE"
        ]

        return {
            "catalog_candidates": (
                self.total_catalog_candidates
            ),

            "verified_live": (
                len(live_verified)
            ),

            "baseline": (
                len(baseline)
            ),

            "connected": (
                self.connected_provider_count
            ),

            "providers": dict(
                self.provider_admission_state
            ),
        }

    # ======================================================
    # CAREER TWIN TELEMETRY
    # ======================================================

    def get_career_twin_intelligence(
        self,
    ) -> Dict[str, Any]:
        """
        Return the complete Career Twin intelligence generated by
        the most recent search request.
        """

        return {
            "market_intelligence": dict(
                self.last_market_intelligence
            ),

            "career_gap_intelligence": dict(
                self.last_career_gap_intelligence
            ),

            "career_twin_sync": dict(
                self.last_career_twin_sync
            ),

            "career_timeline": dict(
                self.last_career_timeline
            ),

            "requirement_aggregation": dict(
                self.last_requirement_aggregation
            ),

            "career_twin_opportunities_analyzed": len(
                self.last_career_twin_intelligence
            ),

            "career_twin_errors": list(
                self.career_twin_errors
            ),
        }

    # ======================================================
    # SEARCH
    # ======================================================

    def search(
        self,
        candidate: CandidateProfile,
        query: str,
        location: Optional[str] = None,
    ) -> List[JobResult]:

        # --------------------------------------------------
        # Reset request-scoped intelligence
        # --------------------------------------------------

        self.last_career_twin_intelligence = []

        self.last_requirement_aggregation = {}

        self.last_market_intelligence = {}

        self.last_career_gap_intelligence = {}

        self.last_career_timeline = {}

        self.last_career_twin_sync = {}

        self.career_twin_errors = []

        # --------------------------------------------------
        # 1. Broad multi-provider discovery
        # --------------------------------------------------

        metadata = candidate.metadata if isinstance(candidate.metadata, dict) else {}
        provider_preferences = metadata.get("provider_preferences") or {}
        enabled_provider_names = [
            str(name) for name, value in provider_preferences.items()
            if not isinstance(value, dict) or bool(value.get("enabled", True))
        ]
        raw_jobs = self.aggregator.search(
            query=query,
            location=location,
            limit_per_source=30,
            _enabled_providers=enabled_provider_names or None,
        )

        # --------------------------------------------------
        # 2. Cross-source canonical deduplication
        # --------------------------------------------------

        canonical_jobs = (
            self.deduplicator.deduplicate(
                raw_jobs
            )
        )

        # --------------------------------------------------
        # 3. Salary intelligence
        # --------------------------------------------------

        enriched_jobs = [
            self.salary_intelligence.enrich(
                job
            )
            for job in canonical_jobs
        ]

        # --------------------------------------------------
        # 4. Hard filtering
        # --------------------------------------------------

        filtered_jobs = self.filter.filter(
            enriched_jobs,
            candidate,
        )

        # --------------------------------------------------
        # 5. Career Twin market feedback
        #
        # This happens AFTER hard filtering so the persistent
        # Career Twin only learns from opportunities CareerPilot
        # considers usable for this search context.
        # --------------------------------------------------

        candidate_id = str(
            candidate.candidate_id
            or "agentic-user"
        )

        career_twin = get_or_create(
            candidate_id
        )

        try:

            self.last_market_intelligence = (
                self.career_twin_market_intelligence
                .analyze(
                    candidate=candidate,
                    jobs=filtered_jobs,
                    career_twin=career_twin,
                )
            )

            # ----------------------------------------------
            # Persist market intelligence into Career Twin
            # ----------------------------------------------

            self.last_career_twin_sync = (
                self.career_twin_market_intelligence
                .sync_to_career_twin(
                    candidate=candidate,
                    candidate_intelligence={},
                    analysis=(
                        self.last_market_intelligence
                    ),
                )
            )

            # ----------------------------------------------
            # Persist gap history
            # ----------------------------------------------

            self.career_gap_intelligence.record_snapshot(
                candidate_id=candidate_id,
                analysis=(
                    self.last_market_intelligence
                ),
            )

            self.last_career_gap_intelligence = (
                self.career_gap_intelligence
                .build_current_gap_state(
                    candidate_id
                )
            )

            # ----------------------------------------------
            # Persist career timeline event
            # ----------------------------------------------

            synced_twin = (
                self.last_career_twin_sync.get(
                    "career_twin"
                )
                or {}
            )

            if isinstance(
                synced_twin,
                dict,
            ):

                career_twin_version = (
                    synced_twin.get(
                        "version"
                    )
                )

            else:
                career_twin_version = getattr(
                    synced_twin,
                    "version",
                    None,
                )

            priority_gaps = list(
                self.last_market_intelligence.get(
                    "priority_skill_gaps",
                    [],
                )
                or []
            )

            self.career_timeline.record(
                candidate_id=candidate_id,
                event_type=(
                    "MARKET_GAP_DETECTED"
                ),
                summary=(
                    f"CareerPilot analyzed "
                    f"{self.last_market_intelligence.get('jobs_analyzed', 0)} "
                    "live opportunities and detected "
                    f"{len(priority_gaps)} priority market skill gaps."
                ),
                source="live_job_market",
                evidence=[
                    {
                        "jobs_analyzed": (
                            self.last_market_intelligence.get(
                                "jobs_analyzed",
                                0,
                            )
                        ),
                        "priority_skill_gaps": (
                            priority_gaps
                        ),
                        "top_market_skills": (
                            self.last_market_intelligence.get(
                                "top_market_skills",
                                [],
                            )
                        ),
                    }
                ],
                metadata={
                    "new_gaps": (
                        self.last_career_gap_intelligence.get(
                            "new_gaps",
                            [],
                        )
                    ),
                    "resolved_gaps": (
                        self.last_career_gap_intelligence.get(
                            "resolved_gaps",
                            [],
                        )
                    ),
                    "persistent_gaps": (
                        self.last_career_gap_intelligence.get(
                            "persistent_gaps",
                            [],
                        )
                    ),
                },
                career_twin_version=(
                    career_twin_version
                ),
            )

            self.last_career_timeline = (
                self.career_timeline.build_timeline(
                    candidate_id,
                    career_twin=synced_twin,
                )
            )

        except Exception as exc:

            self.career_twin_errors.append(
                {
                    "stage": (
                        "market_feedback"
                    ),
                    "candidate_id": (
                        candidate_id
                    ),
                    "error": (
                        f"{type(exc).__name__}: {exc}"
                    ),
                }
            )

            print(
                "[CareerSearchService] "
                "Career Twin market feedback failed: "
                f"{exc}"
            )

        # --------------------------------------------------
        # 6. Matching + Career Twin personalization
        # --------------------------------------------------

        results: List[
            JobResult
        ] = []

        for job in filtered_jobs:

            requirements = (
                self.requirements_extractor.extract(
                    job
                )
            )

            # ----------------------------------------------
            # Base hybrid match
            # ----------------------------------------------

            match = self.match_engine.evaluate(
                candidate=candidate,
                job=job,
                requirements=requirements,
            )

            # ----------------------------------------------
            # Career Twin opportunity personalization
            # ----------------------------------------------

            try:

                career_twin_result = (
                    self.career_twin_pipeline.enrich(
                        candidate=candidate,
                        job=job,
                        requirements=requirements,
                        base_match=match,
                    )
                )

                career_twin_analysis = (
                    career_twin_result[
                        "career_twin_analysis"
                    ]
                )

                personalized_match = (
                    career_twin_result[
                        "personalized_match"
                    ]
                )

                self.last_career_twin_intelligence.append(
                    {
                        "source": job.source,

                        "source_job_id": (
                            job.source_job_id
                        ),

                        "company": job.company,

                        "title": job.title,

                        "analysis": (
                            career_twin_analysis
                        ),
                    }
                )

            except Exception as exc:

                career_twin_analysis = {}

                personalized_match = {
                    "personalized_score": (
                        match.final_score
                    ),

                    "decision": (
                        match.decision
                    ),

                    "personalized_confidence": (
                        match.confidence
                    ),

                    "strengths": list(
                        match.strengths
                    ),

                    "explanation": (
                        match.explanation
                    ),
                }

                error_record = {
                    "stage": (
                        "opportunity_personalization"
                    ),

                    "source": job.source,

                    "source_job_id": (
                        job.source_job_id
                    ),

                    "company": job.company,

                    "title": job.title,

                    "error": (
                        f"{type(exc).__name__}: {exc}"
                    ),
                }

                self.career_twin_errors.append(
                    error_record
                )

                print(
                    "[CareerSearchService] "
                    "Career Twin opportunity enrichment "
                    "failed for "
                    f"{job.company} / {job.title}: "
                    f"{exc}"
                )

            # ----------------------------------------------
            # Sources
            # ----------------------------------------------

            sources = (
                job.sources
                if job.sources
                else [job.source]
            )

            source_count = (
                job.source_count
                if job.sources
                else 1
            )

            source_records: List[
                SourceRecord
            ] = []

            for raw_record in (
                job.source_records
                or []
            ):

                source_records.append(
                    SourceRecord(
                        source=str(
                            raw_record.get(
                                "source",
                                "",
                            )
                        ),

                        source_job_id=str(
                            raw_record.get(
                                "source_job_id",
                                "",
                            )
                        ),

                        company=str(
                            raw_record.get(
                                "company",
                                job.company,
                            )
                        ),

                        title=str(
                            raw_record.get(
                                "title",
                                job.title,
                            )
                        ),

                        location=list(
                            raw_record.get(
                                "location",
                                job.location,
                            )
                            or []
                        ),

                        remote=bool(
                            raw_record.get(
                                "remote",
                                False,
                            )
                        ),

                        employment_type=(
                            raw_record.get(
                                "employment_type"
                            )
                        ),

                        apply_url=str(
                            raw_record.get(
                                "apply_url",
                                "",
                            )
                        ),

                        source_url=str(
                            raw_record.get(
                                "source_url",
                                "",
                            )
                        ),

                        salary_min_lpa=(
                            raw_record.get(
                                "salary_min_lpa"
                            )
                        ),

                        salary_max_lpa=(
                            raw_record.get(
                                "salary_max_lpa"
                            )
                        ),

                        salary_currency=str(
                            raw_record.get(
                                "salary_currency",
                                "INR",
                            )
                        ),

                        salary_status=str(
                            raw_record.get(
                                "salary_status",
                                "UNDISCLOSED",
                            )
                        ),

                        salary_confidence=float(
                            raw_record.get(
                                "salary_confidence",
                                0.0,
                            )
                            or 0.0
                        ),

                        salary_evidence=(
                            raw_record.get(
                                "salary_evidence"
                            )
                        ),

                        posted_at=(
                            raw_record.get(
                                "posted_at"
                            )
                        ),
                    )
                )

            # ----------------------------------------------
            # Fallback source record
            # ----------------------------------------------

            if not source_records:

                source_records.append(
                    SourceRecord(
                        source=job.source,

                        source_job_id=(
                            job.source_job_id
                        ),

                        company=job.company,

                        title=job.title,

                        location=job.location,

                        remote=job.remote,

                        employment_type=(
                            job.employment_type
                        ),

                        apply_url=(
                            job.apply_url
                        ),

                        source_url=(
                            job.source_url
                        ),

                        salary_min_lpa=(
                            job.salary.min_lpa
                        ),

                        salary_max_lpa=(
                            job.salary.max_lpa
                        ),

                        salary_currency=(
                            job.salary.currency
                        ),

                        salary_status=str(
                            job.metadata.get(
                                "salary_status",
                                "UNDISCLOSED",
                            )
                        ),

                        salary_confidence=float(
                            job.metadata.get(
                                "salary_confidence",
                                0.0,
                            )
                            or 0.0
                        ),

                        salary_evidence=(
                            job.metadata.get(
                                "salary_evidence"
                            )
                        ),

                        posted_at=(
                            job.posted_at
                        ),
                    )
                )

            # ----------------------------------------------
            # Salary
            # ----------------------------------------------

            salary_min = (
                job.salary.min_lpa
            )

            salary_max = (
                job.salary.max_lpa
            )

            salary_disclosed = (
                salary_min is not None
                or salary_max is not None
            )

            salary_confidence = float(
                job.metadata.get(
                    "salary_confidence",
                    0.0,
                )
                or 0.0
            )

            salary_evidence = (
                job.metadata.get(
                    "salary_evidence"
                )
            )

            candidate_minimum = (
                candidate
                .career_goal
                .minimum_salary_lpa
            )

            if not salary_disclosed:

                salary_status = (
                    "UNDISCLOSED"
                )

            elif candidate_minimum is None:

                salary_status = (
                    "MEETS_TARGET"
                )

            elif (
                salary_min is not None
                and salary_min
                >= candidate_minimum
            ):

                salary_status = (
                    "MEETS_TARGET"
                )

            elif (
                salary_min is None
                and salary_max is not None
                and salary_max
                >= candidate_minimum
            ):

                salary_status = (
                    "MEETS_TARGET"
                )

            else:

                salary_status = (
                    "BELOW_TARGET"
                )

            # ----------------------------------------------
            # Base match breakdown
            #
            # This intentionally remains the base hybrid
            # evidence. JobResult.match_score carries the
            # personalized Career Twin score.
            # ----------------------------------------------

            match_breakdown = MatchBreakdown(
                overall_score=(
                    match.final_score
                ),

                role_fit=(
                    match.role_fit
                ),

                skill_fit=(
                    match.skill_fit
                ),

                experience_fit=(
                    match.experience_fit
                ),

                location_fit=(
                    match.location_fit
                ),

                salary_fit=(
                    match.salary_fit
                ),

                career_goal_fit=(
                    match.career_goal_fit
                ),

                semantic_score=(
                    match.semantic_score
                ),

                deterministic_score=(
                    match.deterministic_score
                ),
            )

            # ----------------------------------------------
            # Career Twin skill evidence
            # ----------------------------------------------

            twin_missing_skills = (
                career_twin_analysis.get(
                    "career_twin_missing_skills",
                    [],
                )
                if isinstance(
                    career_twin_analysis,
                    dict,
                )
                else []
            )

            twin_matched_skills = (
                career_twin_analysis.get(
                    "career_twin_matched_skills",
                    [],
                )
                if isinstance(
                    career_twin_analysis,
                    dict,
                )
                else []
            )

            combined_skill_gaps = sorted(
                set(
                    match.skill_gaps
                    + list(
                        twin_missing_skills
                        or []
                    )
                )
            )

            combined_matched_skills = sorted(
                set(
                    match.matched_skills
                    + list(
                        twin_matched_skills
                        or []
                    )
                )
            )

            # ----------------------------------------------
            # Job result
            # ----------------------------------------------

            results.append(
                JobResult(
                    source=job.source,

                    source_job_id=(
                        job.source_job_id
                    ),

                    sources=sources,

                    source_count=source_count,

                    source_records=(
                        source_records
                    ),

                    company=job.company,

                    title=job.title,

                    location=job.location,

                    remote=job.remote,

                    employment_type=(
                        job.employment_type
                    ),

                    # Personalized Career Twin score.
                    match_score=(
                        personalized_match[
                            "personalized_score"
                        ]
                    ),

                    decision=(
                        personalized_match[
                            "decision"
                        ]
                    ),

                    confidence=(
                        personalized_match[
                            "personalized_confidence"
                        ]
                    ),

                    strengths=(
                        personalized_match[
                            "strengths"
                        ]
                    ),

                    skill_gaps=(
                        combined_skill_gaps
                    ),

                    matched_skills=(
                        combined_matched_skills
                    ),

                    explanation=(
                        personalized_match[
                            "explanation"
                        ]
                    ),

                    match_breakdown=(
                        match_breakdown
                    ),

                    salary_min_lpa=(
                        salary_min
                    ),

                    salary_max_lpa=(
                        salary_max
                    ),

                    salary_disclosed=(
                        salary_disclosed
                    ),

                    salary_status=(
                        salary_status
                    ),

                    salary_confidence=(
                        salary_confidence
                    ),

                    salary_evidence=(
                        salary_evidence
                    ),

                    apply_url=(
                        job.apply_url
                    ),
                )
            )

        # --------------------------------------------------
        # 7. Final personalized ranking
        # --------------------------------------------------

        results.sort(
            key=lambda result: (
                result.match_score
                if result.match_score is not None
                else 0
            ),
            reverse=True,
        )

        # --------------------------------------------------
        # 8. Opportunity-pool requirement aggregation
        # --------------------------------------------------

        try:

            self.last_requirement_aggregation = (
                self.career_twin_job_intelligence
                .aggregate_requirements(
                    filtered_jobs
                )
            )

        except Exception as exc:

            self.last_requirement_aggregation = {
                "jobs_analyzed": 0,
                "error": (
                    f"{type(exc).__name__}: {exc}"
                ),
            }

            print(
                "[CareerSearchService] "
                "Requirement aggregation failed: "
                f"{exc}"
            )

        return results

    # ======================================================
    # CAREER TWIN SEARCH SUMMARY
    # ======================================================

    def get_career_twin_search_summary(
        self,
    ) -> Dict[str, Any]:
        """
        Backward-compatible summary for request-scoped
        Career Twin intelligence.
        """

        return {
            "opportunities_analyzed": len(
                self.last_career_twin_intelligence
            ),

            "career_twin_errors": len(
                self.career_twin_errors
            ),

            "career_twin_error_details": list(
                self.career_twin_errors
            ),

            "requirement_aggregation": dict(
                self.last_requirement_aggregation
            ),

            "market_intelligence": dict(
                self.last_market_intelligence
            ),

            "career_gap_intelligence": dict(
                self.last_career_gap_intelligence
            ),

            "career_timeline": dict(
                self.last_career_timeline
            ),

            "career_twin_sync": dict(
                self.last_career_twin_sync
            ),
        }

    # ======================================================
    # SALARY SUMMARY
    # ======================================================

    def build_salary_summary(
        self,
        results: List[JobResult],
        minimum_salary_lpa: Optional[float],
    ) -> SalarySummary:

        salary_verified = sum(
            1
            for result in results
            if (
                result.salary_status
                == "MEETS_TARGET"
                and result.salary_disclosed
            )
        )

        salary_undisclosed = sum(
            1
            for result in results
            if (
                result.salary_status
                == "UNDISCLOSED"
            )
        )

        return SalarySummary(
            minimum_salary_lpa=(
                minimum_salary_lpa
            ),

            opportunities_found=len(
                results
            ),

            salary_verified=(
                salary_verified
            ),

            salary_undisclosed=(
                salary_undisclosed
            ),
        )

    # ======================================================
    # SOURCE SUMMARY
    # ======================================================

    def build_source_summary(
        self,
        results: List[JobResult],
    ) -> SourceSummary:

        configured_sources = [
            str(
                source.name
            )
            for source
            in self.aggregator.sources
        ]

        contributing_sources = set()

        for result in results:

            contributing_sources.update(
                result.sources
                if result.sources
                else [result.source]
            )

        return SourceSummary(
            connected=len(
                configured_sources
            ),

            contributing=len(
                contributing_sources
            ),

            sources=(
                configured_sources
            ),
        )