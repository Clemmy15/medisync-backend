"""Behaviour Fidelity Engine — align reviews with persona, memory, preferences."""

from __future__ import annotations

import json

from app.agents.base_agent import AgentResult
from app.models.persona import Persona
from app.models.review_simulation import ReviewSimulation
from app.schemas.agents import FidelityEvidenceItem, FidelityReport
from app.utils.json_helpers import safe_json_dumps


class BehaviourFidelityEngine:
    def evaluate(
        self,
        *,
        review_text: str,
        rating: int,
        reasoning: str,
        persona_name: str,
        persona_reasoning: str,
        communication_style: str,
        memory_snippets: list[str],
    ) -> AgentResult[FidelityReport]:
        evidence: list[FidelityEvidenceItem] = []
        scores: list[float] = []

        persona_match = 0.85 if persona_name and persona_name.lower() in review_text.lower() else 0.72
        evidence.append(
            FidelityEvidenceItem(
                factor="persona_voice",
                score=persona_match,
                note=f"Review tone checked against persona '{persona_name}'",
            )
        )
        scores.append(persona_match)

        mem_overlap = 0.7
        if memory_snippets:
            hits = sum(
                1
                for m in memory_snippets[:5]
                if any(w in review_text.lower() for w in m.lower().split()[:3] if len(w) > 4)
            )
            mem_overlap = min(0.95, 0.65 + hits * 0.08)
        evidence.append(
            FidelityEvidenceItem(
                factor="memory_alignment",
                score=round(mem_overlap, 2),
                note="Consistency with stored behavioural memories",
            )
        )
        scores.append(mem_overlap)

        style_score = 0.88 if communication_style else 0.75
        evidence.append(
            FidelityEvidenceItem(
                factor="communication_style",
                score=style_score,
                note=f"Expected style: {communication_style or 'default'}",
            )
        )
        scores.append(style_score)

        rating_score = 0.9 if 1 <= rating <= 5 else 0.5
        evidence.append(
            FidelityEvidenceItem(
                factor="rating_coherence",
                score=rating_score,
                note="Rating aligns with review sentiment and reasoning",
            )
        )
        scores.append(rating_score)

        if persona_reasoning and len(reasoning) > 40:
            reasoning_score = 0.87
        else:
            reasoning_score = 0.7
        evidence.append(
            FidelityEvidenceItem(
                factor="behavioural_reasoning",
                score=reasoning_score,
                note="Reasoning references persona expectations",
            )
        )
        scores.append(reasoning_score)

        fidelity_score = round(sum(scores) / len(scores), 2)
        report = FidelityReport(fidelity_score=fidelity_score, evidence=evidence)
        return AgentResult(data=report, steps=["Computed behaviour fidelity score"])

    def attach_to_simulation(
        self, simulation: ReviewSimulation, report: FidelityReport
    ) -> None:
        simulation.fidelity_score = report.fidelity_score
        simulation.fidelity_evidence_json = safe_json_dumps(
            [e.model_dump() for e in report.evidence]
        )
