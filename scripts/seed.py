"""Seed database with demo users, profiles, and memories."""

import asyncio
import logging

from sqlalchemy import select

from app.agents.memory_agent import MemoryAgent
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.security import get_password_hash
from app.database.session import get_session_factory
from app.memory.chroma_store import get_chroma_store
from app.models.profile import UserProfile
from app.models.user import User
from app.repositories.memory_repository import MemoryRepository
from app.repositories.profile_repository import ProfileRepository

logger = logging.getLogger(__name__)


async def seed() -> None:
    setup_logging()
    settings = get_settings()
    factory = get_session_factory()
    async with factory() as db:
        admin_result = await db.execute(
            select(User).where(User.email == settings.admin_email)
        )
        if not admin_result.scalar_one_or_none():
            admin = User(
                name="Admin User",
                email=settings.admin_email,
                password_hash=get_password_hash(settings.admin_password),
                is_admin=True,
            )
            db.add(admin)
            logger.info("Created admin user %s", settings.admin_email)

        demo_result = await db.execute(
            select(User).where(User.email == "demo@medisync.ai")
        )
        demo_user = demo_result.scalar_one_or_none()
        if not demo_user:
            demo_user = User(
                name="Demo Student",
                email="demo@medisync.ai",
                password_hash=get_password_hash("demo12345"),
            )
            db.add(demo_user)
            await db.flush()

            profile = UserProfile(
                user_id=demo_user.id,
                age_range="18-24",
                occupation="University Student",
                gender="prefer_not_to_say",
                stress_level="high",
                sleep_pattern="5-6 hours weekdays",
                hydration_level="low",
                activity_level="moderate",
                dietary_preferences="vegetarian, quick meals",
                health_goals="improve sleep, reduce stress, stay hydrated",
                communication_style="concise and actionable",
            )
            db.add(profile)
            await db.flush()

            memory_agent = MemoryAgent(
                db,
                get_chroma_store(),
                MemoryRepository(db),
                ProfileRepository(db),
            )
            memories = [
                ("behaviour", "Studies late until 2am before exams"),
                ("health", "Reports frequent headaches and afternoon fatigue"),
                ("behaviour", "Skips breakfast on busy mornings"),
                ("communication", "Prefers bullet-point health tips"),
                ("health", "Goal: sleep 7-8 hours consistently"),
            ]
            for category, content in memories:
                await memory_agent.create_memory(demo_user.id, category, content)

            logger.info("Created demo user with profile and memories")

        await db.commit()
        print("Seed data applied successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
