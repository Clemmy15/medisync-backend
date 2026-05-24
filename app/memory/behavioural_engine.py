"""Behavioural Memory Engine — dual-store long-term memory (PostgreSQL + ChromaDB)."""

import logging
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.domain.enums import MemoryCategory
from app.memory.categories import MEMORY_TYPE_LABELS, get_memory_label
from app.memory.chroma_store import ChromaMemoryStore
from app.models.memory import Memory
from app.models.profile import UserProfile
from app.repositories.memory_repository import MemoryRepository
from app.repositories.profile_repository import ProfileRepository
from app.schemas.memory import (
    MemoryCategorySummary,
    MemorySearchHit,
    MemorySearchResponse,
    MemorySummaryResponse,
)
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

MEMORY_SUMMARY_SYSTEM = """You are MedisyncAI Memory Summarization Agent.
Summarize the user's behavioural memories concisely for healthcare personalization.
Return JSON: overall_summary (string, 2-4 sentences), category_summaries (object mapping
category key to one-sentence summary).
"""


class BehaviouralMemoryEngine:
    """
    Long-term behavioural memory with PostgreSQL persistence and ChromaDB semantic retrieval.

  Memory types:
    - health: Health Memory
    - behaviour: Behaviour Memory
    - recommendation: Recommendation Memory
    - communication: Communication Memory
    """

    def __init__(
        self,
        db: AsyncSession,
        chroma_store: ChromaMemoryStore,
        memory_repo: MemoryRepository,
        profile_repo: ProfileRepository,
        llm: LLMService | None = None,
    ) -> None:
        self._db = db
        self._chroma = chroma_store
        self._memory_repo = memory_repo
        self._profile_repo = profile_repo
        self._llm = llm or LLMService()

    async def create(
        self,
        user_id: int,
        category: MemoryCategory,
        content: str,
    ) -> Memory:
        memory = Memory(
            user_id=user_id,
            category=category.value,
            content=content.strip(),
        )
        await self._memory_repo.create(memory)

        chroma_id = self._chroma.add_memory(
            user_id=user_id,
            memory_id=memory.id,
            content=memory.content,
            category=memory.category,
        )
        memory.chroma_id = chroma_id
        memory.updated_at = memory.updated_at or datetime.now(timezone.utc)
        await self._memory_repo.save(memory)
        await self._db.refresh(memory)
        logger.info(
            "Created %s id=%s user_id=%s",
            get_memory_label(category),
            memory.id,
            user_id,
        )
        return memory

    async def get(self, user_id: int, memory_id: int) -> Memory:
        memory = await self._memory_repo.get_by_id(memory_id, user_id)
        if not memory:
            raise NotFoundError(
                "Memory not found",
                details={"memory_id": memory_id},
            )
        return memory

    async def list_memories(
        self,
        user_id: int,
        *,
        category: MemoryCategory | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Memory]:
        return await self._memory_repo.list_by_user(
            user_id,
            category=category,
            limit=limit,
            offset=offset,
        )

    async def update(
        self,
        user_id: int,
        memory_id: int,
        *,
        content: str | None = None,
        category: MemoryCategory | None = None,
    ) -> Memory:
        memory = await self.get(user_id, memory_id)

        if content is not None:
            memory.content = content.strip()
        if category is not None:
            memory.category = category.value
        memory.updated_at = datetime.now(timezone.utc)

        if memory.chroma_id:
            memory.chroma_id = self._chroma.update_memory(
                chroma_id=memory.chroma_id,
                user_id=user_id,
                memory_id=memory.id,
                content=memory.content,
                category=memory.category,
            )
        else:
            memory.chroma_id = self._chroma.add_memory(
                user_id=user_id,
                memory_id=memory.id,
                content=memory.content,
                category=memory.category,
            )

        await self._memory_repo.save(memory)
        await self._db.refresh(memory)
        logger.info("Updated memory id=%s user_id=%s", memory_id, user_id)
        return memory

    async def delete(self, user_id: int, memory_id: int) -> bool:
        memory = await self._memory_repo.get_by_id(memory_id, user_id)
        if not memory:
            return False
        if memory.chroma_id:
            self._chroma.delete_memory(memory.chroma_id)
        await self._memory_repo.delete(memory)
        logger.info("Deleted memory id=%s user_id=%s", memory_id, user_id)
        return True

    async def semantic_search(
        self,
        user_id: int,
        query: str,
        *,
        category: MemoryCategory | None = None,
        limit: int = 10,
    ) -> MemorySearchResponse:
        """ChromaDB vector search with optional category filter and PG enrichment."""
        raw_hits = self._chroma.search_memories(user_id, query, n_results=limit * 2)

        results: list[MemorySearchHit] = []
        seen_ids: set[int] = set()

        for hit in raw_hits:
            metadata = hit.get("metadata") or {}
            hit_category = str(metadata.get("category", "unknown"))
            if category is not None and hit_category != category.value:
                continue

            memory_id = metadata.get("memory_id")
            if isinstance(memory_id, float):
                memory_id = int(memory_id)

            distance = hit.get("distance")
            relevance = self._distance_to_relevance(distance)

            content = str(hit.get("content", ""))
            if memory_id and memory_id not in seen_ids:
                pg_memory = await self._memory_repo.get_by_id(int(memory_id), user_id)
                if pg_memory:
                    content = pg_memory.content
                    hit_category = pg_memory.category
                    seen_ids.add(int(memory_id))

            results.append(
                MemorySearchHit(
                    memory_id=int(memory_id) if memory_id else None,
                    category=hit_category,
                    content=content,
                    relevance_score=relevance,
                )
            )
            if len(results) >= limit:
                break

        # Fallback: keyword scan in PostgreSQL if vector store returns few results
        if len(results) < limit:
            pg_matches = await self._keyword_fallback(
                user_id, query, category, limit - len(results), seen_ids
            )
            results.extend(pg_matches)

        return MemorySearchResponse(
            query=query,
            results=results,
            total=len(results),
        )

    async def summarize(
        self,
        user_id: int,
        *,
        category: MemoryCategory | None = None,
        max_memories: int = 50,
    ) -> MemorySummaryResponse:
        memories = await self._memory_repo.list_by_user(
            user_id, category=category, limit=max_memories
        )
        if not memories:
            return MemorySummaryResponse(
                overall_summary="No memories stored yet.",
                total_memories=0,
                by_category=[],
            )

        grouped: dict[str, list[Memory]] = defaultdict(list)
        for memory in memories:
            grouped[memory.category].append(memory)

        by_category: list[MemoryCategorySummary] = []
        for cat_key, items in grouped.items():
            try:
                cat_enum = MemoryCategory(cat_key)
                label = get_memory_label(cat_enum)
            except ValueError:
                label = cat_key
            by_category.append(
                MemoryCategorySummary(
                    category=cat_key,
                    label=label,
                    count=len(items),
                    summary=self._heuristic_category_summary(items),
                )
            )

        overall = await self._generate_overall_summary(user_id, memories, grouped)
        return MemorySummaryResponse(
            overall_summary=overall,
            total_memories=len(memories),
            by_category=sorted(by_category, key=lambda c: c.category),
        )

    async def get_context_for_agents(self, user_id: int) -> str:
        """Build text context from profile + recent memories for downstream agents."""
        memories = await self._memory_repo.list_by_user(user_id, limit=20)
        profile = await self._profile_repo.get_by_user_id(user_id)
        return self._format_context(profile, memories)

    async def _keyword_fallback(
        self,
        user_id: int,
        query: str,
        category: MemoryCategory | None,
        limit: int,
        exclude_ids: set[int],
    ) -> list[MemorySearchHit]:
        tokens = [t.lower() for t in query.split() if len(t) > 2]
        if not tokens:
            return []

        all_memories = await self._memory_repo.list_by_user(
            user_id, category=category, limit=200
        )
        hits: list[MemorySearchHit] = []
        for memory in all_memories:
            if memory.id in exclude_ids:
                continue
            text = memory.content.lower()
            matches = sum(1 for t in tokens if t in text)
            if matches > 0:
                hits.append(
                    MemorySearchHit(
                        memory_id=memory.id,
                        category=memory.category,
                        content=memory.content,
                        relevance_score=round(min(0.85, 0.4 + matches * 0.15), 3),
                    )
                )
        hits.sort(key=lambda h: h.relevance_score, reverse=True)
        return hits[:limit]

    async def _generate_overall_summary(
        self,
        user_id: int,
        memories: list[Memory],
        grouped: dict[str, list[Memory]],
    ) -> str:
        lines = [
            f"[{cat}] " + "; ".join(m.content for m in items[:8])
            for cat, items in grouped.items()
        ]
        user_prompt = f"Summarize memories for user {user_id}:\n" + "\n".join(lines)

        try:
            result = await self._llm.complete_json(MEMORY_SUMMARY_SYSTEM, user_prompt)
            if summary := result.get("overall_summary"):
                return str(summary)
        except Exception as exc:
            logger.warning("LLM summarization fallback: %s", exc)

        parts = [
            f"{get_memory_label(MemoryCategory(k))}: {len(v)} entries"
            for k, v in grouped.items()
            if k in {c.value for c in MemoryCategory}
        ]
        return (
            f"User has {len(memories)} stored memories across "
            f"{len(grouped)} categories ({', '.join(parts)})."
        )

    @staticmethod
    def _heuristic_category_summary(memories: list[Memory]) -> str:
        samples = [m.content for m in memories[:3]]
        preview = "; ".join(samples)
        if len(memories) > 3:
            preview += f"; and {len(memories) - 3} more"
        return preview

    @staticmethod
    def _distance_to_relevance(distance: float | None) -> float:
        if distance is None:
            return 0.5
        # Cosine distance: 0 = identical, 2 = opposite
        return round(max(0.0, min(1.0, 1.0 - (float(distance) / 2.0))), 3)

    @staticmethod
    def _format_context(
        profile: UserProfile | None, memories: list[Memory]
    ) -> str:
        parts: list[str] = []
        if profile:
            parts.append(
                f"Profile: age={profile.age_range}, stress={profile.stress_level}, "
                f"sleep={profile.sleep_pattern}, goals={profile.health_goals}"
            )
        for memory in memories:
            label = get_memory_label(memory.category)
            parts.append(f"[{label}] {memory.content}")
        return "\n".join(parts) if parts else "No profile or memory data available."
