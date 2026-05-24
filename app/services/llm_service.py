import json
import logging
import re
from typing import Any

from app.core.config import get_settings
from app.core.exceptions import LLMServiceError

logger = logging.getLogger(__name__)


class LLMService:
    """Unified LLM interface supporting OpenAI, Gemini, and mock mode."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        provider = self.settings.llm_provider
        try:
            if provider == "openai":
                return await self._openai_complete(system_prompt, user_prompt)
            if provider == "gemini":
                return await self._gemini_complete(system_prompt, user_prompt)
            return self._mock_complete(system_prompt, user_prompt)
        except LLMServiceError:
            raise
        except Exception as exc:
            logger.exception("LLM provider %s failed", provider)
            raise LLMServiceError(
                f"LLM provider '{provider}' failed",
                details={"error": str(exc)},
            ) from exc

    async def complete_json(
        self, system_prompt: str, user_prompt: str
    ) -> dict[str, Any]:
        raw = await self.complete(system_prompt, user_prompt)
        parsed = self._parse_json(raw)
        if "raw" in parsed and len(parsed) == 1:
            logger.warning("LLM returned non-JSON response; using fallback parsing")
        return parsed

    async def _openai_complete(self, system_prompt: str, user_prompt: str) -> str:
        if not self.settings.openai_api_key:
            raise LLMServiceError("OPENAI_API_KEY is not configured")
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        response = await client.chat.completions.create(
            model=self.settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content or ""

    async def _gemini_complete(self, system_prompt: str, user_prompt: str) -> str:
        if not self.settings.gemini_api_key:
            raise LLMServiceError("GEMINI_API_KEY is not configured")
        import google.generativeai as genai

        genai.configure(api_key=self.settings.gemini_api_key)
        model = genai.GenerativeModel(
            self.settings.gemini_model,
            system_instruction=system_prompt,
        )
        response = await model.generate_content_async(user_prompt)
        return response.text or ""

    def _mock_complete(self, system_prompt: str, user_prompt: str) -> str:
        lowered = system_prompt.lower()
        if "extract" in lowered or "extraction" in lowered:
            return json.dumps({
                "symptoms": ["occasional headaches", "fatigue"],
                "habits": ["irregular sleep", "moderate exercise"],
                "sleep_patterns": ["5-6 hours on weekdays", "weekend catch-up"],
                "hydration_behaviour": ["2-3 glasses water daily"],
                "stress_indicators": ["work deadlines", "evening anxiety"],
                "communication_preferences": ["concise summaries", "actionable tips"],
                "health_goals": ["improve sleep", "reduce stress"],
                "summary": "User shows signs of sleep deprivation and work-related stress.",
                "confidence": 0.92,
                "field_confidence": {
                    "symptoms": 0.88,
                    "habits": 0.85,
                    "sleep_patterns": 0.91,
                    "hydration_behaviour": 0.78,
                    "stress_indicators": 0.87,
                    "communication_preferences": 0.72,
                    "health_goals": 0.9,
                },
            })
        if "review simulation" in lowered:
            return json.dumps({
                "rating": 4,
                "review": (
                    "This sleep tracking app helped me notice my late-night screen habits. "
                    "Easy to use, though reminders could be gentler."
                ),
                "reasoning": (
                    "Persona values practical tools; moderate enthusiasm reflects "
                    "realistic expectations."
                ),
            })
        if "cold start" in lowered:
            return json.dumps({
                "persona": "Budget-Conscious Nigerian Student",
                "recommendations": [
                    {
                        "category": "health_apps",
                        "recommendation": "Use a free sleep tracker app with gentle reminders.",
                        "confidence": 0.86,
                    },
                    {
                        "category": "food_nutrition",
                        "recommendation": "Affordable hydration plan with local foods and water intake goals.",
                        "confidence": 0.82,
                    },
                    {
                        "category": "educational_content",
                        "recommendation": "Read short sleep hygiene articles in plain English.",
                        "confidence": 0.8,
                    },
                    {
                        "category": "exercise_plans",
                        "recommendation": "15-minute campus walks after lectures.",
                        "confidence": 0.78,
                    },
                ],
                "reasoning": (
                    "New user profile shows student occupation and sleep goals with limited "
                    "history; affordable cross-domain starter recommendations are appropriate."
                ),
            })
        if "cross-domain" in lowered or "ranked_recommendations" in lowered:
            return json.dumps({
                "ranked_recommendations": [
                    {
                        "category": "health_apps",
                        "recommendation": "Sleep tracking app with wind-down reminders",
                        "reasoning": "Directly addresses poor sleep",
                        "confidence": 0.92,
                    },
                    {
                        "category": "food_nutrition",
                        "recommendation": "Daily hydration plan with 2L water target",
                        "reasoning": "Hydration supports sleep quality",
                        "confidence": 0.85,
                    },
                    {
                        "category": "educational_content",
                        "recommendation": "Short article on sleep hygiene for students",
                        "reasoning": "Low-cost education",
                        "confidence": 0.83,
                    },
                    {
                        "category": "exercise_plans",
                        "recommendation": "Evening light stretching routine (10 min)",
                        "reasoning": "Supports relaxation before bed",
                        "confidence": 0.8,
                    },
                    {
                        "category": "productivity_habits",
                        "recommendation": "Fixed study cutoff time by 10 PM",
                        "reasoning": "Reduces late-night fatigue",
                        "confidence": 0.78,
                    },
                ],
            })
        if "nigerian context" in lowered:
            return json.dumps({
                "affordability_tier": "student_budget",
                "affordability_notes": (
                    "Prioritize free apps, campus-friendly habits, and low-cost nutrition."
                ),
                "lifestyle_patterns": (
                    "Irregular power, shared accommodation, exam seasons, and mobile-first access."
                ),
                "communication_style": (
                    "Warm, respectful, concise English with practical Nigerian examples."
                ),
                "contextual_reasoning": (
                    "Recommendations and reviews should mention affordability and realistic "
                    "student schedules in Nigeria."
                ),
            })
        if "recommendation" in lowered and "review" not in lowered:
            return json.dumps({
                "category": "sleep_improvement",
                "recommendation": (
                    "Establish a consistent sleep schedule of 7-8 hours and use a "
                    "sleep tracking app with a 10-minute screen-free wind-down routine."
                ),
                "reasoning": (
                    "Your profile shows 5-6h sleep as a student, persona indicates "
                    "Sleep-Deprived Student, and memories reference late-night study. "
                    "Sleep improvement is the highest-impact intervention."
                ),
                "confidence": 0.88,
            })
        if "persona engine" in lowered:
            return json.dumps({
                "persona_name": "Sleep-Deprived Student",
                "reasoning": (
                    "Profile indicates university student occupation with 5-6h sleep, "
                    "memories show late-night study habits, and imported context "
                    "references fatigue and exam stress."
                ),
                "confidence_score": 0.87,
            })
        if "risk detection" in lowered:
            return json.dumps({
                "risk_level": "moderate",
                "reasoning": (
                    "Dangerous symptom patterns: recurring headaches with fatigue but no "
                    "acute red flags. Behavioural deterioration: declining sleep quality "
                    "noted in memory. Recurring health concerns: stress and hydration "
                    "issues appear across multiple entries."
                ),
                "recommended_action": (
                    "Schedule a primary care visit within 2 weeks; track symptoms daily "
                    "and seek urgent care if symptoms worsen suddenly."
                ),
            })
        if "behaviour analysis" in lowered:
            return json.dumps({
                "trend_analysis": (
                    "Declining sleep quality over past weeks with increasing stress markers."
                ),
                "behavioural_insights": [
                    "Irregular bedtime on weekdays",
                    "Low hydration correlates with fatigue reports",
                    "Stress spikes before deadlines",
                ],
                "confidence_scores": {
                    "sleep_pattern": 0.88,
                    "hydration": 0.75,
                    "stress": 0.91,
                },
            })
        if "summarization" in lowered or "memory summar" in lowered:
            return json.dumps({
                "overall_summary": (
                    "User shows patterns of sleep deprivation, work-related stress, "
                    "and a preference for concise health guidance."
                ),
                "category_summaries": {
                    "health": "Headaches and fatigue linked to short sleep.",
                    "behaviour": "Irregular study schedule affecting rest.",
                },
            })
        return json.dumps({
            "message": "Mock LLM response",
            "input_preview": user_prompt[:100],
        })

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        text = text.strip()
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError as exc:
                logger.warning("Failed to parse LLM JSON: %s", exc)
        return {"raw": text}
