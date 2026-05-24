from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm_service import LLMService
from app.services.reasoning_service import ReasoningService

if TYPE_CHECKING:
    from app.agents.memory_agent import MemoryAgent

T = TypeVar("T", bound=BaseModel)


@dataclass(frozen=True)
class AgentResult(Generic[T]):
    """Typed container for agent output and reasoning steps."""

    data: T
    steps: list[str]


class BaseAgent(ABC):
    def __init__(
        self,
        db: AsyncSession,
        llm: LLMService,
        memory_agent: MemoryAgent | None = None,  # noqa: F821
        reasoning: ReasoningService | None = None,
    ) -> None:
        self.db = db
        self.llm = llm
        self.memory_agent = memory_agent
        self.reasoning = reasoning or ReasoningService()

    async def load_user_context(self, user_id: int) -> str:
        if not self.memory_agent:
            raise RuntimeError("MemoryAgent is required for context loading")
        return await self.memory_agent.get_context_for_agents(user_id)

    @abstractmethod
    async def run(self, *args: object, **kwargs: object) -> AgentResult[BaseModel]:
        pass
