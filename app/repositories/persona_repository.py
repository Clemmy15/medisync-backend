from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.persona import Persona


class PersonaRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, persona: Persona) -> Persona:
        self._db.add(persona)
        await self._db.flush()
        return persona

    async def get_latest(self, user_id: int) -> Persona | None:
        result = await self._db.execute(
            select(Persona)
            .where(Persona.user_id == user_id)
            .order_by(Persona.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: int, limit: int = 20) -> list[Persona]:
        result = await self._db.execute(
            select(Persona)
            .where(Persona.user_id == user_id)
            .order_by(Persona.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
