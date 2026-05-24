"""Memory agent — facade over BehaviouralMemoryEngine for agent orchestration."""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base_agent import AgentResult
from app.domain.enums import MemoryCategory
from app.memory.behavioural_engine import BehaviouralMemoryEngine
from app.memory.chroma_store import ChromaMemoryStore
from app.models.memory import Memory
from app.repositories.memory_repository import MemoryRepository
from app.repositories.profile_repository import ProfileRepository
from app.schemas.memory import MemorySearchResponse, MemorySummaryResponse
from app.services.reasoning_service import ReasoningService

logger = logging.getLogger(__name__)


class MemoryAgent:
    """Manages dual-store memory: PostgreSQL + ChromaDB embeddings."""

    def __init__(
        self,
        db: AsyncSession,
        chroma_store: ChromaMemoryStore,
        memory_repo: MemoryRepository,
        profile_repo: ProfileRepository,
        reasoning: ReasoningService | None = None,
    ) -> None:
        self._db = db
        self._reasoning = reasoning or ReasoningService()
        self._engine = BehaviouralMemoryEngine(
            db, chroma_store, memory_repo, profile_repo
        )

    @property
    def engine(self) -> BehaviouralMemoryEngine:
        return self._engine

    async def create_memory(
        self, user_id: int, category: str, content: str
    ) -> Memory:
        cat = MemoryCategory(category)
        return await self._engine.create(user_id, cat, content)

    async def update_memory(
        self,
        user_id: int,
        memory_id: int,
        *,
        content: str | None = None,
        category: str | None = None,
    ) -> Memory:
        cat = MemoryCategory(category) if category else None
        return await self._engine.update(
            user_id, memory_id, content=content, category=cat
        )

    async def delete_memory(self, user_id: int, memory_id: int) -> bool:
        return await self._engine.delete(user_id, memory_id)

    async def get_memory(self, user_id: int, memory_id: int) -> Memory:
        return await self._engine.get(user_id, memory_id)

    async def list_memories(
        self,
        user_id: int,
        category: MemoryCategory | None = None,
    ) -> list[Memory]:
        return await self._engine.list_memories(user_id, category=category)

    async def search_memories(
        self,
        user_id: int,
        query: str,
        *,
        category: MemoryCategory | None = None,
        limit: int = 10,
    ) -> AgentResult[MemorySearchResponse]:
        steps = [
            "Retrieved user profile",
            "Retrieved behavioural memory index",
            "Executed semantic vector search",
            "Ranked results by relevance",
        ]
        response = await self._engine.semantic_search(
            user_id, query, category=category, limit=limit
        )
        await self._reasoning.save_trace(
            self._db, user_id, "memory_search", steps
        )
        return AgentResult(data=response, steps=steps)

    async def summarize_memories(
        self,
        user_id: int,
        *,
        category: MemoryCategory | None = None,
        max_memories: int = 50,
    ) -> AgentResult[MemorySummaryResponse]:
        steps = [
            "Retrieved user profile",
            "Retrieved behavioural memory",
            "Grouped memories by category",
        ]
        response = await self._engine.summarize(
            user_id, category=category, max_memories=max_memories
        )
        steps.append("Generated memory summary response")
        await self._reasoning.save_trace(
            self._db, user_id, "memory_summarize", steps
        )
        return AgentResult(data=response, steps=steps)

    async def get_context_for_agents(self, user_id: int) -> str:
        return await self._engine.get_context_for_agents(user_id)

    async def run(
        self, user_id: int, query: str | None = None
    ) -> dict[str, Any]:
        if query:
            result = await self.search_memories(user_id, query)
            return {
                "memories": [h.model_dump() for h in result.data.results],
                "semantic_matches": result.data.results,
                "steps": result.steps,
            }
        memories = await self.list_memories(user_id)
        return {
            "memories": [
                {"id": m.id, "category": m.category, "content": m.content}
                for m in memories
            ]
        }
