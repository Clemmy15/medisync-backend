"""Persona agent — facade over PersonaEngine for agent orchestration."""

from app.agents.base_agent import AgentResult, BaseAgent
from app.persona.engine import PersonaEngine
from app.schemas.persona import PersonaGenerateResponse


class PersonaAgent(BaseAgent):
    def __init__(self, engine: PersonaEngine) -> None:
        self._engine = engine
        self.db = engine._db
        self.llm = engine._llm
        self.memory_agent = None
        self.reasoning = engine._reasoning

    async def run(self, user_id: int) -> AgentResult[PersonaGenerateResponse]:
        return await self._engine.generate(user_id)
