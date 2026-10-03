from __future__ import annotations

from typing import Any, Dict, List

from backend.tools.knowledge_tools import career_knowledge_tool


class RecommendationAgent:
    """
    Specialist agent responsible for synthesizing personalized
    career recommendations from existing shared-state evidence.

    This agent intentionally does not duplicate candidate, resume,
    job, or strategy intelligence engines.

    It consumes existing shared-state outputs and converts them
    into prioritized, actionable next steps.
    """

    name = "recommendation"

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(state, dict):
            raise TypeError(
                "RecommendationAgent state must be a dictionary."
            )

        updated_state = dict(state)

        knowledge_result = career_knowledge_tool.invoke({
            "query": state.get("user_goal", ""),
            "top_k": 5,
        })
        updated_state["career_knowledge_evidence"] = (
            knowledge_result.get("evidence", [])
        )
        knowledge_trace = list(updated_state.get("tool_trace", []) or [])
        knowledge_trace.append({
            "tool": "search_career_knowledge",
            "agent": self.name,
            "status": "completed",
            "result_count": knowledge_result.get("count", 0),
        })
        updated_state["tool_trace"] = knowledge_trace

        candidate_intelligence = (
            state.get("candidate_intelligence") or {}
        )
        career_strategy = (
            state.get("career_strategy") or {}
        )
        strategy_summary = (
            state.get("strategy_summary") or {}
        )
        skill_gaps = state.get("skill_gaps") or {}
        resume_intelligence = (
            state.get("resume_intelligence") or {}
        )
        ats_analysis = state.get("ats_analysis") or {}
        job_fit_analysis = (
            state.get("job_fit_analysis") or {}
        )
        rewrite_analysis = (
            state.get("rewrite_analysis") or {}
        )

        job_results = state.get(
            "job_search_results",
            state.get("job_results", {}),
        ) or {}

        recommendations = self._build_recommendations(
            candidate_intelligence=candidate_intelligence,
            career_strategy=career_strategy,
            strategy_summary=strategy_summary,
            skill_gaps=skill_gaps,
            resume_intelligence=resume_intelligence,
            ats_analysis=ats_analysis,
            job_fit_analysis=job_fit_analysis,
            rewrite_analysis=rewrite_analysis,
            job_results=job_results,
        )

        next_action = self._build_next_action(
            recommendations
        )

        recommendation_summary = self._build_summary(
            recommendations
        )

        recommendation_result = {
            "recommendations": recommendations,
            "next_action": next_action,
            "recommendation_summary": recommendation_summary,
        }

        updated_state["recommendations"] = recommendations
        updated_state["next_action"] = next_action
        updated_state["recommendation_summary"] = (
            recommendation_summary
        )
        updated_state["recommendation_result"] = (
            recommendation_result
        )

        return self._record_execution(
            state=updated_state,
            decision="recommendations_complete",
        )

    # ============================================================
    # RECOMMENDATION GENERATION
    # ============================================================

    def _build_recommendations(
        self,
        candidate_intelligence: Dict[str, Any],
        career_strategy: Dict[str, Any],
        strategy_summary: Dict[str, Any],
        skill_gaps: Dict[str, Any],
        resume_intelligence: Dict[str, Any],
        ats_analysis: Dict[str, Any],
        job_fit_analysis: Dict[str, Any],
        rewrite_analysis: Dict[str, Any],
        job_results: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        recommendations: List[Dict[str, Any]] = []
        priority = 1

        # --------------------------------------------------------
        # 1. Required skill gaps
        # --------------------------------------------------------

        required_gaps = self._as_list(
            skill_gaps.get("required", [])
        )

        preferred_gaps = self._as_list(
            skill_gaps.get("preferred", [])
        )

        for skill in required_gaps[:3]:
            skill_name = str(skill)

            recommendations.append(
                {
                    "type": "skill_gap",
                    "priority": priority,
                    "title": (
                        f"Close required skill gap: {skill_name}"
                    ),
                    "action": (
                        f"Build practical evidence for {skill_name} "
                        "through a project, coursework, or targeted "
                        "preparation before relying on this role as "
                        "a strong match."
                    ),
                    "reason": (
                        "The job requirements identify this as a "
                        "required skill that is not currently "
                        "represented in the candidate skill profile."
                    ),
                    "evidence_source": "job_requirements",
                }
            )

            priority += 1

        # --------------------------------------------------------
        # 2. Preferred skill gaps
        # --------------------------------------------------------

        for skill in preferred_gaps[:2]:
            skill_name = str(skill)

            recommendations.append(
                {
                    "type": "preferred_skill",
                    "priority": priority,
                    "title": (
                        f"Strengthen preferred skill: {skill_name}"
                    ),
                    "action": (
                        f"Consider developing or demonstrating "
                        f"{skill_name} to improve competitiveness "
                        "for target opportunities."
                    ),
                    "reason": (
                        "This skill is preferred by the target "
                        "opportunity but is not currently "
                        "represented in the candidate profile."
                    ),
                    "evidence_source": "job_requirements",
                }
            )

            priority += 1

        # --------------------------------------------------------
        # 3. Resume improvement
        # --------------------------------------------------------

        rewrite_suggestions = self._extract_list(
            rewrite_analysis,
            "suggestions",
        )

        if rewrite_suggestions:
            recommendations.append(
                {
                    "type": "resume",
                    "priority": priority,
                    "title": "Improve resume evidence",
                    "action": (
                        "Apply the highest-confidence evidence-supported "
                        "resume rewrites before using the resume for "
                        "targeted applications."
                    ),
                    "reason": (
                        f"{len(rewrite_suggestions)} rewrite "
                        "opportunities were identified by the "
                        "deterministic resume rewrite engine."
                    ),
                    "evidence_source": "rewrite_analysis",
                }
            )

            priority += 1

        # --------------------------------------------------------
        # 4. ATS improvement
        # --------------------------------------------------------

        ats_score = self._extract_score(
            ats_analysis,
            (
                "score",
                "ats_score",
                "overall_score",
                "overall_ats_score",
            ),
        )

        if ats_score is not None and ats_score < 80:
            recommendations.append(
                {
                    "type": "resume_alignment",
                    "priority": priority,
                    "title": "Improve ATS alignment",
                    "action": (
                        "Strengthen keyword and requirement alignment "
                        "using only skills and evidence already "
                        "supported by the resume."
                    ),
                    "reason": (
                        f"The current ATS-related score is {ats_score}, "
                        "indicating room for stronger target-role "
                        "alignment."
                    ),
                    "evidence_source": "ats_analysis",
                }
            )

            priority += 1

        # --------------------------------------------------------
        # 5. Job fit
        # --------------------------------------------------------

        fit_score = self._extract_score(
            job_fit_analysis,
            (
                "overall_score",
                "fit_score",
                "match_score",
                "score",
            ),
        )

        if fit_score is not None and fit_score < 70:
            recommendations.append(
                {
                    "type": "job_fit",
                    "priority": priority,
                    "title": "Address job-fit gaps",
                    "action": (
                        "Review the strongest missing requirements "
                        "before prioritizing this opportunity."
                    ),
                    "reason": (
                        f"The available job-fit analysis indicates "
                        f"a score of {fit_score}."
                    ),
                    "evidence_source": "job_fit_analysis",
                }
            )

            priority += 1

        # --------------------------------------------------------
        # 6. Career strategy actions
        # --------------------------------------------------------

        strategy_actions = self._as_list(
            career_strategy.get(
                "recommended_actions",
                [],
            )
        )

        for action in strategy_actions[:2]:
            action_text = str(action)

            recommendations.append(
                {
                    "type": "career_strategy",
                    "priority": priority,
                    "title": self._strategy_title(
                        action_text
                    ),
                    "action": action_text,
                    "reason": (
                        "This action comes from the existing "
                        "deterministic career strategy generated "
                        "from candidate intelligence."
                    ),
                    "evidence_source": "career_strategy",
                }
            )

            priority += 1

        # --------------------------------------------------------
        # 7. Targeted opportunities
        # --------------------------------------------------------

        job_count = self._extract_job_count(
            job_results
        )

        if job_count > 0:
            recommendations.append(
                {
                    "type": "opportunity",
                    "priority": priority,
                    "title": "Prioritize targeted applications",
                    "action": (
                        "Review the ranked job opportunities and "
                        "prioritize the strongest matches rather "
                        "than applying indiscriminately."
                    ),
                    "reason": (
                        f"{job_count} job opportunity result(s) "
                        "are available in shared workflow state."
                    ),
                    "evidence_source": "job_search_results",
                }
            )

            priority += 1

        # --------------------------------------------------------
        # 8. Candidate readiness
        # --------------------------------------------------------

        readiness = str(
            candidate_intelligence.get(
                "readiness_level",
                "",
            )
            or ""
        )

        if readiness in {
            "EARLY_STAGE",
            "DEVELOPING",
        }:
            recommendations.append(
                {
                    "type": "readiness",
                    "priority": priority,
                    "title": "Build role readiness",
                    "action": (
                        "Prioritize practical evidence and high-impact "
                        "skill development before targeting highly "
                        "competitive roles."
                    ),
                    "reason": (
                        f"Candidate readiness is currently {readiness}."
                    ),
                    "evidence_source": (
                        "candidate_intelligence"
                    ),
                }
            )

            priority += 1

        # --------------------------------------------------------
        # 9. Fallback
        # --------------------------------------------------------

        if not recommendations:
            primary_role = str(
                career_strategy.get(
                    "primary_role",
                    "target roles",
                )
                or "target roles"
            )

            recommendations.append(
                {
                    "type": "next_step",
                    "priority": 1,
                    "title": "Continue targeted preparation",
                    "action": (
                        f"Continue strengthening the candidate "
                        f"profile for {primary_role} using "
                        "evidence-backed projects, skills, and "
                        "targeted applications."
                    ),
                    "reason": (
                        "No higher-priority gap was identified "
                        "from the currently available shared state."
                    ),
                    "evidence_source": "shared_state",
                }
            )

        return recommendations

    # ============================================================
    # DISTINCT STRATEGY TITLES
    # ============================================================

    @staticmethod
    def _strategy_title(action: str) -> str:
        text = action.strip()
        lowered = text.casefold()

        if "target" in lowered and (
            "opportunit" in lowered
            or "role" in lowered
            or "application" in lowered
        ):
            return "Target aligned opportunities"

        if "strengthen" in lowered and (
            "api" in lowered
            or "backend" in lowered
            or "database" in lowered
            or "deployment" in lowered
        ):
            return "Strengthen production backend skills"

        if "build" in lowered and (
            "project" in lowered
            or "ai" in lowered
        ):
            return "Build stronger AI project evidence"

        if "system design" in lowered:
            return "Practice backend system design"

        if "skill gap" in lowered or "gap" in lowered:
            return "Review and close key skill gaps"

        if "resume" in lowered:
            return "Strengthen resume positioning"

        if "continuously evaluate" in lowered:
            return "Review role-specific skill gaps"

        if "practice" in lowered:
            return "Practice role-relevant fundamentals"

        if "document" in lowered:
            return "Document measurable project impact"

        return "Advance your career strategy"

    # ============================================================
    # NEXT ACTION
    # ============================================================

    @staticmethod
    def _build_next_action(
        recommendations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not recommendations:
            return {
                "action": "No immediate action identified.",
                "reason": (
                    "The workflow did not produce a recommendation."
                ),
                "priority": None,
            }

        first = recommendations[0]

        return {
            "action": first.get("action", ""),
            "reason": first.get("reason", ""),
            "priority": first.get("priority", 1),
            "type": first.get("type", "next_step"),
        }

    # ============================================================
    # SUMMARY
    # ============================================================

    @staticmethod
    def _build_summary(
        recommendations: List[Dict[str, Any]],
    ) -> str:
        if not recommendations:
            return (
                "No actionable recommendations were generated."
            )

        first = recommendations[0]

        return (
            f"{len(recommendations)} personalized career "
            f"recommendation(s) generated. The highest-priority "
            f"next step is: "
            f"{first.get('title', 'next action')}."
        )

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def _as_list(value: Any) -> List[Any]:
        if value is None:
            return []

        if isinstance(value, list):
            return value

        if isinstance(value, tuple):
            return list(value)

        return [value]

    @staticmethod
    def _extract_list(
        payload: Any,
        key: str,
    ) -> List[Any]:
        if not isinstance(payload, dict):
            return []

        return RecommendationAgent._as_list(
            payload.get(key)
        )

    @staticmethod
    def _extract_score(
        payload: Any,
        keys: tuple[str, ...],
    ) -> float | None:
        if not isinstance(payload, dict):
            return None

        for key in keys:
            value = payload.get(key)

            if isinstance(value, (int, float)):
                return float(value)

        return None

    @staticmethod
    def _extract_job_count(
        payload: Any,
    ) -> int:
        if not isinstance(payload, dict):
            return 0

        for key in (
            "count",
            "jobs_found",
            "total",
        ):
            value = payload.get(key)

            if isinstance(value, int):
                return value

        results = payload.get("results")

        if isinstance(results, list):
            return len(results)

        return 0

    # ============================================================
    # TRACE
    # ============================================================

    def _record_execution(
        self,
        state: Dict[str, Any],
        decision: str,
    ) -> Dict[str, Any]:
        updated_state = dict(state)

        updated_state["current_agent"] = self.name

        updated_state["last_decision"] = {
            "agent": self.name,
            "decision": decision,
            "reasoning": (
                "Recommendation Agent synthesized existing "
                "candidate, resume, job, and strategy evidence "
                "into prioritized next actions."
            ),
            "next_step": "validation",
        }

        agents_used = list(
            updated_state.get("agents_used", []) or []
        )

        if self.name not in agents_used:
            agents_used.append(self.name)

        updated_state["agents_used"] = agents_used

        agent_trace = list(
            updated_state.get("agent_trace", []) or []
        )

        agent_trace.append(
            {
                "agent": self.name,
                "action": "synthesize_recommendations",
                "status": "completed",
                "reasoning": (
                    "Synthesized existing shared-state evidence "
                    "without re-running upstream intelligence."
                ),
            }
        )

        updated_state["agent_trace"] = agent_trace

        return updated_state

    # ============================================================
    # UNIFORM EXECUTION ALIAS
    # ============================================================

    def execute(
        self,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        return self.run(state)


# ============================================================
# MODULE-LEVEL INSTANCE
# ============================================================

recommendation_agent = RecommendationAgent()


def run_recommendation_agent(
    state: Dict[str, Any],
) -> Dict[str, Any]:
    return recommendation_agent.run(state)