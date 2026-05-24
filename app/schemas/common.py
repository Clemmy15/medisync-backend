from typing import TypeVar

from pydantic import BaseModel

from app.schemas.reasoning import AgentStepsMixin, ReasoningSteps

T = TypeVar("T", bound=BaseModel)


class AgentResultResponse(AgentStepsMixin):
    """Wraps any agent payload with transparent reasoning steps."""


def merge_with_reasoning_trace(
    payload: BaseModel, steps: list[str]
) -> dict[str, object]:
    return {
        **payload.model_dump(),
        "steps": steps,
        "reasoning_trace": ReasoningSteps(steps=steps).model_dump(),
    }
