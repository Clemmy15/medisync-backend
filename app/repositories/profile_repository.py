from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import UserProfile


class ProfileRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_user_id(self, user_id: int) -> UserProfile | None:
        result = await self._db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, profile: UserProfile) -> UserProfile:
        self._db.add(profile)
        await self._db.flush()
        return profile

    async def save(self, profile: UserProfile) -> UserProfile:
        await self._db.flush()
        return profile
