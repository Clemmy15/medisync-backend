"""Seed database with demo users, profiles, and memories (Chroma optional)."""

import asyncio
import logging
from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.security import get_password_hash
from app.database.session import get_session_factory
from app.models.memory import Memory
from app.models.profile import UserProfile
from app.models.user import User

logger = logging.getLogger(__name__)


def _try_sync_chroma(memory: Memory) -> None:
    """Best-effort vector index; skipped when chromadb is not installed."""
    try:
        from app.memory.chroma_store import get_chroma_store

        store = get_chroma_store()
        memory.chroma_id = store.add_memory(
            memory.user_id,
            memory.id,
            memory.content,
            memory.category,
        )
    except ImportError:
        logger.warning(
            "chromadb not installed — memories saved to PostgreSQL only "
            "(semantic search disabled until chromadb is available)"
        )
    except Exception as exc:
        logger.warning("Chroma sync skipped: %s", exc)


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

            memories = [
                ("behaviour", "Studies late until 2am before exams"),
                ("health", "Reports frequent headaches and afternoon fatigue"),
                ("behaviour", "Skips breakfast on busy mornings"),
                ("communication", "Prefers bullet-point health tips"),
                ("health", "Goal: sleep 7-8 hours consistently"),
            ]
            for category, content in memories:
                memory = Memory(
                    user_id=demo_user.id,
                    category=category,
                    content=content,
                )
                db.add(memory)
                await db.flush()
                _try_sync_chroma(memory)

            logger.info("Created demo user with profile and memories")
        else:
            logger.info("Demo user already exists — skipped")

        await db.commit()
        print("Seed data applied successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
