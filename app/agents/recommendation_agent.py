"""Recommendation agent — facade over RecommendationEngine."""

from app.agents.base_agent import AgentResult, BaseAgent
from app.domain.enums import RecommendationCategory
from app.recommendations.engine import RecommendationEngine
from app.schemas.recommendation import RecommendationResponse


class RecommendationAgent(BaseAgent):
    def __init__(self, engine: RecommendationEngine) -> None:
        self._engine = engine
        self.db = engine._db
        self.llm = engine._llm
        self.memory_agent = None
        self.reasoning = engine._reasoning

    async def run(
        self,
        user_id: int,
        category: RecommendationCategory | None = None,
    ) -> AgentResult[RecommendationResponse]:
        return await self._engine.generate(user_id, category)
