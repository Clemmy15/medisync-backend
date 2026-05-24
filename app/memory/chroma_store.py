import logging
import uuid
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class ChromaMemoryStore:
    """Vector memory store backed by ChromaDB."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=settings.chroma_collection,
            metadata={"hnsw:space": "cosine"},
        )

    def add_memory(
        self,
        user_id: int,
        memory_id: int,
        content: str,
        category: str,
    ) -> str:
        chroma_id = f"user_{user_id}_mem_{memory_id}_{uuid.uuid4().hex[:8]}"
        self._collection.add(
            ids=[chroma_id],
            documents=[content],
            metadatas=[{
                "user_id": user_id,
                "memory_id": memory_id,
                "category": category,
            }],
        )
        logger.debug("Chroma indexed memory %s for user %s", chroma_id, user_id)
        return chroma_id

    def search_memories(
        self,
        user_id: int,
        query: str,
        n_results: int = 10,
    ) -> list[dict[str, Any]]:
        results = self._collection.query(
            query_texts=[query],
            n_results=n_results,
            where={"user_id": user_id},
        )
        items: list[dict[str, Any]] = []
        if results and results.get("documents"):
            for i, doc in enumerate(results["documents"][0]):
                items.append({
                    "content": doc,
                    "metadata": (
                        results["metadatas"][0][i] if results.get("metadatas") else {}
                    ),
                    "distance": (
                        results["distances"][0][i] if results.get("distances") else None
                    ),
                })
        return items

    def update_memory(
        self,
        chroma_id: str,
        user_id: int,
        memory_id: int,
        content: str,
        category: str,
    ) -> str:
        try:
            self._collection.update(
                ids=[chroma_id],
                documents=[content],
                metadatas=[{
                    "user_id": user_id,
                    "memory_id": memory_id,
                    "category": category,
                }],
            )
            logger.debug("Chroma updated memory %s", chroma_id)
            return chroma_id
        except Exception as exc:
            logger.warning("Chroma update failed for %s: %s", chroma_id, exc)
            return self.add_memory(user_id, memory_id, content, category)

    def delete_memory(self, chroma_id: str) -> None:
        try:
            self._collection.delete(ids=[chroma_id])
            logger.debug("Chroma deleted memory %s", chroma_id)
        except Exception as exc:
            logger.warning("Failed to delete Chroma memory %s: %s", chroma_id, exc)


_chroma_store: ChromaMemoryStore | None = None


def get_chroma_store() -> ChromaMemoryStore:
    global _chroma_store
    if _chroma_store is None:
        _chroma_store = ChromaMemoryStore()
    return _chroma_store
