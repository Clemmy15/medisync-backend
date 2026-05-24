from app.agents.base_agent import AgentResult, BaseAgent
from app.cold_start.engine import ColdStartEngine
from app.schemas.agents import ColdStartRequest, ColdStartResponse


class ColdStartAgent(BaseAgent):
    def __init__(self, engine: ColdStartEngine) -> None:
        self._engine = engine
        self.db = engine._db
        self.llm = engine._llm
        self.memory_agent = None
        self.reasoning = engine._reasoning

    async def run(
        self, user_id: int, request: ColdStartRequest | None = None
    ) -> AgentResult[ColdStartResponse]:
        return await self._engine.run(user_id, request)
