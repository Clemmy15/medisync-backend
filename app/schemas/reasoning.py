from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class ReasoningSteps(BaseModel):
    """Nested reasoning trace (legacy shape; prefer top-level ``steps``)."""

    steps: list[str]


class AgentStepsMixin(BaseModel):
    """
    Transparent reasoning on every agent response.

    Clients should read top-level ``steps``; ``reasoning_trace`` mirrors the same data.
    """

    steps: list[str] = Field(
        default_factory=list,
        description="Ordered step-by-step transparent reasoning",
    )
    reasoning_trace: ReasoningSteps = Field(
        description="Same steps as reasoning_trace.steps (backward compatible)",
    )

    @model_validator(mode="before")
    @classmethod
    def sync_steps_and_trace(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        steps = data.get("steps")
        trace = data.get("reasoning_trace")
        if steps is not None and trace is None:
            data["reasoning_trace"] = {"steps": steps}
        elif trace is not None and steps is None:
            if isinstance(trace, ReasoningSteps):
                data["steps"] = trace.steps
            elif isinstance(trace, dict):
                data["steps"] = trace.get("steps", [])
        return data


class ReasoningTraceResponse(BaseModel):
    id: int
    trace_type: str
    reference_id: int | None
    steps: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ReasoningTraceListResponse(BaseModel):
    traces: list[ReasoningTraceResponse]
    total: int
