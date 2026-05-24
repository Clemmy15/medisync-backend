from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.context_import import ContextImport


class ContextImportRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, record: ContextImport) -> ContextImport:
        self._db.add(record)
        await self._db.flush()
        return record

    async def list_by_user(self, user_id: int, limit: int = 50) -> list[ContextImport]:
        result = await self._db.execute(
            select(ContextImport)
            .where(ContextImport.user_id == user_id)
            .order_by(ContextImport.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
