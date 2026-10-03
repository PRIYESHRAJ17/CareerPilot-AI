from __future__ import annotations

from typing import Any, Dict, List


class CareerTwinOrchestration:
    """
    Final orchestration bridge for Supervisor, Recommendation and
    Validation agents.
    """

    # ============================================================
    # SUPERVISOR
    # ============================================================

    @staticmethod
    def supervisor_guard(
        state: Dict[str, Any],
    ) -> Dict[str, Any]:

        updated = dict(state)

        twin = (
            updated.get(
                "career_twin"
            )
            or {}
        )

        market = (
            updated.get(
                "market_intelligence"
            )
            or {}
        )

        gaps = (
            updated.get(
                "career_gap_intelligence"
            )
            or {}
        )

        decision = dict(
            updated.get(
                "supervisor_decision"
            )
            or {}
        )

        decision[
            "career_twin_aware"
        ] = bool(twin)

        decision[
            "market_intelligence_available"
        ] = bool(market)

        decision[
            "career_gap_intelligence_available"
        ] = bool(gaps)

        decision[
            "career_twin_context"
        ] = {
            "candidate_id": (
                twin.get(
                    "candidate_id"
                )
                if isinstance(
                    twin,
                    dict,
                )
                else None
            ),
            "version": (
                twin.get(
                    "version"
                )
                if isinstance(
                    twin,
                    dict,
                )
                else None
            ),
            "jobs_analyzed": (
                market.get(
                    "jobs_analyzed",
                    0,
                )
                if isinstance(
                    market,
                    dict,
                )
                else 0
            ),
            "priority_gaps": (
                gaps.get(
                    "current_gaps",
                    [],
                )
                if isinstance(
                    gaps,
                    dict,
                )
                else []
            ),
        }

        updated[
            "supervisor_decision"
        ] = decision

        trace = list(
            updated.get(
                "agent_trace",
                [],
            )
            or []
        )

        trace.append(
            {
                "agent": "supervisor",
                "action": (
                    "career_twin_context_check"
                ),
                "status": "completed",
                "career_twin_aware": bool(
                    twin
                ),
                "market_intelligence_available": bool(
                    market
                ),
            }
        )

        updated[
            "agent_trace"
        ] = trace

        return updated

    # ============================================================
    # RECOMMENDATIONS
    # ============================================================

    @staticmethod
    def augment_recommendations(
        state: Dict[str, Any],
    ) -> Dict[str, Any]:

        updated = dict(state)

        recommendations = list(
            updated.get(
                "recommendations",
                [],
            )
            or []
        )

        market = (
            updated.get(
                "market_intelligence"
            )
            or {}
        )

        gaps = (
            updated.get(
                "career_gap_intelligence"
            )
            or {}
        )

        twin = (
            updated.get(
                "career_twin"
            )
            or {}
        )

        priority_gaps = list(
            gaps.get(
                "current_gaps",
                [],
            )
            or []
        )

        market_gaps = list(
            market.get(
                "market_skill_gaps",
                [],
            )
            or []
        )

        existing_titles = {
            str(
                item.get(
                    "title",
                    "",
                )
            ).casefold()
            for item in recommendations
            if isinstance(
                item,
                dict,
            )
        }

        next_priority = (
            len(recommendations)
            + 1
        )

        for gap in market_gaps[:3]:

            if not isinstance(
                gap,
                dict,
            ):
                continue

            skill = str(
                gap.get(
                    "skill",
                    "",
                )
                or ""
            ).strip()

            if not skill:
                continue

            title = (
                f"Develop market skill: "
                f"{skill}"
            )

            if (
                title.casefold()
                in existing_titles
            ):
                continue

            recommendation = {
                "type": (
                    "career_twin_market_gap"
                ),
                "priority": next_priority,
                "title": title,
                "action": (
                    f"Build verifiable practical "
                    f"evidence in {skill} because "
                    "it recurs in the live target "
                    "opportunity market."
                ),
                "reason": (
                    f"{gap.get('market_frequency', 0)} "
                    "observed opportunities mention "
                    f"{skill}, including "
                    f"{gap.get('required_frequency', 0)} "
                    "required mentions."
                ),
                "evidence_source": (
                    "career_twin_market_intelligence"
                ),
                "evidence": [
                    {
                        "type": (
                            "live_opportunity_market"
                        ),
                        "jobs_analyzed": (
                            market.get(
                                "jobs_analyzed",
                                0,
                            )
                        ),
                        "skill": skill,
                        "market_frequency": (
                            gap.get(
                                "market_frequency",
                                0,
                            )
                        ),
                    },
                    {
                        "type": "career_twin",
                        "candidate_id": (
                            twin.get(
                                "candidate_id"
                            )
                            if isinstance(
                                twin,
                                dict,
                            )
                            else None
                        ),
                    },
                ],
            }

            recommendations.append(
                recommendation
            )

            next_priority += 1

        updated[
            "recommendations"
        ] = recommendations

        if recommendations:
            first = recommendations[0]

            updated[
                "next_action"
            ] = {
                "action": first.get(
                    "action",
                    "",
                ),
                "reason": first.get(
                    "reason",
                    "",
                ),
                "priority": first.get(
                    "priority",
                    1,
                ),
                "type": first.get(
                    "type",
                    "career",
                ),
            }

        trace = list(
            updated.get(
                "agent_trace",
                [],
            )
            or []
        )

        trace.append(
            {
                "agent": "recommendation",
                "action": (
                    "career_twin_market_augmentation"
                ),
                "status": "completed",
                "added_recommendations": max(
                    0,
                    len(
                        recommendations
                    )
                    - next_priority
                    + 1,
                ),
                "career_twin_aware": bool(
                    twin
                ),
            }
        )

        updated[
            "agent_trace"
        ] = trace

        return updated

    # ============================================================
    # VALIDATION
    # ============================================================

    @staticmethod
    def validate(
        state: Dict[str, Any],
    ) -> Dict[str, Any]:

        updated = dict(state)

        twin = (
            updated.get(
                "career_twin"
            )
            or {}
        )

        market = (
            updated.get(
                "market_intelligence"
            )
            or {}
        )

        gaps = (
            updated.get(
                "career_gap_intelligence"
            )
            or {}
        )

        recommendations = list(
            updated.get(
                "recommendations",
                [],
            )
            or []
        )

        issues: List[str] = []
        warnings: List[str] = []

        if not twin:
            warnings.append(
                "Career Twin context was not available."
            )

        candidate_profile = (
            updated.get(
                "candidate_profile"
            )
            or {}
        )

        candidate_id = str(
            candidate_profile.get(
                "candidate_id",
                "",
            )
            or ""
        )

        twin_id = ""

        if isinstance(
            twin,
            dict,
        ):
            twin_id = str(
                twin.get(
                    "candidate_id",
                    "",
                )
                or ""
            )

        if (
            candidate_id
            and twin_id
            and candidate_id != twin_id
        ):
            issues.append(
                "Career Twin candidate_id does not "
                "match candidate_profile candidate_id."
            )

        if market:

            jobs_analyzed = int(
                market.get(
                    "jobs_analyzed",
                    0,
                )
                or 0
            )

            if jobs_analyzed <= 0:
                warnings.append(
                    "Market intelligence exists but "
                    "contains no analyzed opportunities."
                )

        for index, recommendation in enumerate(
            recommendations
        ):

            if not isinstance(
                recommendation,
                dict,
            ):
                continue

            source = str(
                recommendation.get(
                    "evidence_source",
                    "",
                )
                or ""
            )

            if (
                source
                == "career_twin_market_intelligence"
                and not recommendation.get(
                    "evidence"
                )
            ):
                issues.append(
                    f"Career Twin recommendation "
                    f"{index + 1} has no supporting evidence."
                )

        valid = not issues

        existing_validation = (
            updated.get(
                "final_validation"
            )
        )

        if isinstance(
            existing_validation,
            dict,
        ):
            existing_checks = list(
                existing_validation.get(
                    "checks",
                    [],
                )
                or []
            )

            existing_checks.append(
                {
                    "check": (
                        "career_twin_evidence"
                    ),
                    "status": (
                        "PASS"
                        if valid
                        else "FAIL"
                    ),
                    "result": {
                        "career_twin_present": bool(
                            twin
                        ),
                        "market_intelligence_present": bool(
                            market
                        ),
                        "career_gap_intelligence_present": bool(
                            gaps
                        ),
                        "issues": issues,
                        "warnings": warnings,
                    },
                }
            )

            failed_checks = [
                check
                for check in existing_checks
                if check.get(
                    "status"
                ) == "FAIL"
            ]

            existing_validation[
                "checks"
            ] = existing_checks

            existing_validation[
                "failed_checks"
            ] = len(
                failed_checks
            )

            existing_validation[
                "valid"
            ] = (
                existing_validation.get(
                    "valid",
                    True,
                )
                and valid
            )

            existing_validation[
                "status"
            ] = (
                "VALID"
                if existing_validation[
                    "valid"
                ]
                else "INVALID"
            )

            updated[
                "final_validation"
            ] = existing_validation

        else:
            updated[
                "final_validation"
            ] = {
                "valid": valid,
                "status": (
                    "VALID"
                    if valid
                    else "INVALID"
                ),
                "checks": [
                    {
                        "check": (
                            "career_twin_evidence"
                        ),
                        "status": (
                            "PASS"
                            if valid
                            else "FAIL"
                        ),
                        "result": {
                            "issues": issues,
                            "warnings": warnings,
                        },
                    }
                ],
                "failed_checks": (
                    0 if valid else 1
                ),
                "message": (
                    "Career Twin evidence "
                    "validation passed."
                    if valid
                    else (
                        "Career Twin evidence "
                        "validation failed."
                    )
                ),
            }

        return updated