from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.agents.memory_agent import MemoryAgent
from app.api.helpers import to_agent_result_schema
from app.core.deps import get_current_user, get_memory_agent
from app.core.exceptions import NotFoundError
from app.domain.enums import MemoryCategory
from app.models.user import User
from app.schemas.memory import (
    MemoryCreate,
    MemoryResponse,
    MemorySearchRequest,
    MemorySearchResult,
    MemorySummaryRequest,
    MemorySummaryResult,
    MemoryUpdate,
)

router = APIRouter()


@router.post(
    "",
    response_model=MemoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a behavioural memory",
    description=(
        "Stores a new memory in PostgreSQL and indexes it in ChromaDB for semantic search. "
        "Types: **health**, **behaviour**, **recommendation**, **communication**."
    ),
)
async def create_memory(
    data: MemoryCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    agent: Annotated[MemoryAgent, Depends(get_memory_agent)],
) -> MemoryResponse:
    memory = await agent.create_memory(
        current_user.id, data.category.value, data.content
    )
    return MemoryResponse.model_validate(memory)


@router.get(
    "",
    response_model=list[MemoryResponse],
    summary="Retrieve user memories",
    description="List memories with optional category filter and pagination.",
)
async def list_memories(
    current_user: Annotated[User, Depends(get_current_user)],
    agent: Annotated[MemoryAgent, Depends(get_memory_agent)],
    category: MemoryCategory | None = Query(
        default=None,
        description="Filter: health | behaviour | recommendation | communication",
    ),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[MemoryResponse]:
    memories = await agent.engine.list_memories(
        current_user.id,
        category=category,
        limit=limit,
        offset=offset,
    )
    return [MemoryResponse.model_validate(m) for m in memories]


@router.get(
    "/{memory_id}",
    response_model=MemoryResponse,
    summary="Retrieve a single memory by ID",
)
async def get_memory(
    memory_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    agent: Annotated[MemoryAgent, Depends(get_memory_agent)],
) -> MemoryResponse:
    memory = await agent.get_memory(current_user.id, memory_id)
    return MemoryResponse.model_validate(memory)


@router.put(
    "/{memory_id}",
    response_model=MemoryResponse,
    summary="Update a memory",
    description="Updates PostgreSQL record and re-syncs ChromaDB vector embedding.",
)
async def update_memory(
    memory_id: int,
    data: MemoryUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    agent: Annotated[MemoryAgent, Depends(get_memory_agent)],
) -> MemoryResponse:
    memory = await agent.update_memory(
        current_user.id,
        memory_id,
        content=data.content,
        category=data.category.value if data.category else None,
    )
    return MemoryResponse.model_validate(memory)


@router.post(
    "/search",
    response_model=MemorySearchResult,
    summary="Semantic memory search",
    description=(
        "Searches long-term memory using ChromaDB vector similarity with PostgreSQL "
        "enrichment. Supports natural language queries across all memory types."
    ),
)
async def search_memories(
    data: MemorySearchRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    agent: Annotated[MemoryAgent, Depends(get_memory_agent)],
) -> MemorySearchResult:
    result = await agent.search_memories(
        current_user.id,
        data.query,
        category=data.category,
        limit=data.limit,
    )
    return to_agent_result_schema(result, MemorySearchResult)


@router.post(
    "/summarize",
    response_model=MemorySummaryResult,
    summary="Summarize user memories",
    description=(
        "Generates an overall and per-category summary of stored memories "
        "for agent context and user dashboards."
    ),
)
async def summarize_memories(
    data: MemorySummaryRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    agent: Annotated[MemoryAgent, Depends(get_memory_agent)],
) -> MemorySummaryResult:
    result = await agent.summarize_memories(
        current_user.id,
        category=data.category,
        max_memories=data.max_memories,
    )
    return to_agent_result_schema(result, MemorySummaryResult)


@router.delete(
    "/{memory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a memory",
    description="Removes memory from PostgreSQL and ChromaDB vector store.",
)
async def delete_memory(
    memory_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    agent: Annotated[MemoryAgent, Depends(get_memory_agent)],
) -> None:
    deleted = await agent.delete_memory(current_user.id, memory_id)
    if not deleted:
        raise NotFoundError("Memory not found", details={"memory_id": memory_id})
