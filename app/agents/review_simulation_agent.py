"""Review simulation agent — facade over ReviewSimulationEngine."""

from app.agents.base_agent import AgentResult, BaseAgent
from app.review_simulation.engine import ReviewSimulationEngine
from app.schemas.review_simulation import ReviewSimulationRequest, ReviewSimulationResponse


class ReviewSimulationAgent(BaseAgent):
    def __init__(self, engine: ReviewSimulationEngine) -> None:
        self._engine = engine
        self.db = engine._db
        self.llm = engine._llm
        self.memory_agent = None
        self.reasoning = engine._reasoning

    async def run(
        self,
        user_id: int,
        request: ReviewSimulationRequest,
    ) -> AgentResult[ReviewSimulationResponse]:
        return await self._engine.simulate(user_id, request)
