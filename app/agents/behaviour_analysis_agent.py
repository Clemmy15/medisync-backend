from app.agents.base_agent import AgentResult, BaseAgent
from app.agents.memory_agent import MemoryAgent
from app.schemas.analysis import BehaviourAnalysisResponse
from app.services.llm_service import LLMService
from app.services.reasoning_service import ReasoningService
from app.utils.prompts import BEHAVIOUR_ANALYSIS_SYSTEM
from sqlalchemy.ext.asyncio import AsyncSession


class BehaviourAnalysisAgent(BaseAgent):
    def __init__(
        self,
        db: AsyncSession,
        llm: LLMService,
        memory_agent: MemoryAgent,
        reasoning: ReasoningService,
    ) -> None:
        super().__init__(db, llm, memory_agent, reasoning)

    async def run(self, user_id: int) -> AgentResult[BehaviourAnalysisResponse]:
        steps = [
            "Retrieved user profile",
            "Retrieved behavioural memory",
            "Analyzed behavioural patterns",
        ]
        context = await self.load_user_context(user_id)

        result = await self.llm.complete_json(
            BEHAVIOUR_ANALYSIS_SYSTEM,
            f"Analyze behaviour for user:\n{context}",
        )
        steps.append("Generated trend analysis and insights")

        response = BehaviourAnalysisResponse(
            trend_analysis=str(result.get("trend_analysis", "")),
            behavioural_insights=list(result.get("behavioural_insights", [])),
            confidence_scores={
                str(k): float(v)
                for k, v in result.get("confidence_scores", {}).items()
            },
        )

        await self.reasoning.save_trace(
            self.db, user_id, "behaviour_analysis", steps
        )
        return AgentResult(data=response, steps=steps)
