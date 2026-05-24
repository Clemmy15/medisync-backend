from pydantic import BaseModel

from app.agents.base_agent import AgentResult
from app.schemas.reasoning import ReasoningSteps


def to_agent_result_schema(
    result: AgentResult[BaseModel],
    result_schema: type[BaseModel],
) -> BaseModel:
    """Merge agent payload with top-level ``steps`` and ``reasoning_trace``."""
    steps = result.steps
    return result_schema(
        **result.data.model_dump(),
        steps=steps,
        reasoning_trace=ReasoningSteps(steps=steps),
    )
