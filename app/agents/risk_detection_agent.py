"""Risk detection agent — facade over RiskDetectionEngine."""

from app.agents.base_agent import AgentResult, BaseAgent
from app.risk_detection.engine import RiskDetectionEngine
from app.schemas.risk_detection import RiskDetectionRequest, RiskDetectionResponse


class RiskDetectionAgent(BaseAgent):
    def __init__(self, engine: RiskDetectionEngine) -> None:
        self._engine = engine
        self.db = engine._db
        self.llm = engine._llm
        self.memory_agent = None
        self.reasoning = engine._reasoning

    async def run(
        self,
        user_id: int,
        request: RiskDetectionRequest,
    ) -> AgentResult[RiskDetectionResponse]:
        return await self._engine.detect(user_id, request)
