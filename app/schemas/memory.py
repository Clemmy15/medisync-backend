from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import MemoryCategory
from app.schemas.reasoning import AgentStepsMixin


class MemoryCreate(BaseModel):
    category: MemoryCategory = Field(
        description="health | behaviour | recommendation | communication"
    )
    content: str = Field(..., min_length=1, max_length=10000)


class MemoryUpdate(BaseModel):
    content: str | None = Field(default=None, min_length=1, max_length=10000)
    category: MemoryCategory | None = None


class MemoryResponse(BaseModel):
    id: int
    user_id: int
    category: str
    content: str
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class MemorySearchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=2,
        max_length=500,
        description="Natural language query for semantic search",
        examples=["sleep problems and stress"],
    )
    category: MemoryCategory | None = Field(
        default=None,
        description="Optional filter by memory type",
    )
    limit: int = Field(default=10, ge=1, le=50)


class MemorySearchHit(BaseModel):
    memory_id: int | None = None
    category: str
    content: str
    relevance_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Semantic similarity score (higher is more relevant)",
    )


class MemorySearchResponse(BaseModel):
    query: str
    results: list[MemorySearchHit]
    total: int


class MemorySearchResult(MemorySearchResponse, AgentStepsMixin):
    pass


class MemorySummaryRequest(BaseModel):
    category: MemoryCategory | None = Field(
        default=None,
        description="Summarize only one memory type, or all if omitted",
    )
    max_memories: int = Field(default=50, ge=1, le=200)


class MemoryCategorySummary(BaseModel):
    category: str
    label: str
    count: int
    summary: str


class MemorySummaryResponse(BaseModel):
    overall_summary: str
    total_memories: int
    by_category: list[MemoryCategorySummary]


class MemorySummaryResult(MemorySummaryResponse, AgentStepsMixin):
    pass
