from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import MemoryCategory
from app.models.memory import Memory


class MemoryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, memory_id: int, user_id: int) -> Memory | None:
        result = await self._db.execute(
            select(Memory).where(Memory.id == memory_id, Memory.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: int,
        *,
        category: MemoryCategory | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Memory]:
        query = (
            select(Memory)
            .where(Memory.user_id == user_id)
            .order_by(Memory.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if category is not None:
            query = query.where(Memory.category == category.value)
        result = await self._db.execute(query)
        return list(result.scalars().all())

    async def count_by_user(
        self,
        user_id: int,
        category: MemoryCategory | None = None,
    ) -> int:
        from sqlalchemy import func

        query = select(func.count()).select_from(Memory).where(Memory.user_id == user_id)
        if category is not None:
            query = query.where(Memory.category == category.value)
        result = await self._db.scalar(query)
        return result or 0

    async def list_all(self, limit: int = 100) -> list[Memory]:
        result = await self._db.execute(
            select(Memory).order_by(Memory.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, memory: Memory) -> Memory:
        self._db.add(memory)
        await self._db.flush()
        return memory

    async def save(self, memory: Memory) -> Memory:
        await self._db.flush()
        return memory

    async def delete(self, memory: Memory) -> None:
        await self._db.delete(memory)
