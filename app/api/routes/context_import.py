from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.helpers import to_agent_result_schema
from app.context_import.service import ContextImportService
from app.core.deps import get_context_import_service, get_current_user
from app.domain.enums import AIPlatform
from app.models.user import User
from app.schemas.context_import import (
    ContextAnalyzeRequest,
    ContextAnalyzeResult,
    ContextImportHistoryItem,
    ContextSaveRequest,
    ContextSaveResult,
    ImportPromptResponse,
    PlatformPromptsResponse,
)

router = APIRouter()


@router.get(
    "/prompts",
    response_model=PlatformPromptsResponse,
    summary="Get import prompts for ChatGPT, Gemini, and Claude",
    description=(
        "Returns platform-specific copy-paste prompts for exporting health context "
        "from external AI assistants into MedisyncAI."
    ),
)
async def get_all_import_prompts(
    service: Annotated[ContextImportService, Depends(get_context_import_service)],
) -> PlatformPromptsResponse:
    return service.get_all_prompts()


@router.get(
    "/prompt/{platform}",
    response_model=ImportPromptResponse,
    summary="Get import prompt for a specific AI platform",
)
async def get_platform_import_prompt(
    platform: AIPlatform,
    service: Annotated[ContextImportService, Depends(get_context_import_service)],
) -> ImportPromptResponse:
    return service.get_platform_prompt(platform)


@router.get(
    "/prompt",
    response_model=ImportPromptResponse,
    summary="Get import prompt (optional platform query param)",
    deprecated=False,
)
async def get_import_prompt(
    service: Annotated[ContextImportService, Depends(get_context_import_service)],
    platform: AIPlatform = Query(
        default=AIPlatform.CHATGPT,
        description="Target AI platform: chatgpt, gemini, or claude",
    ),
) -> ImportPromptResponse:
    return service.get_platform_prompt(platform)


@router.post(
    "/analyze",
    response_model=ContextAnalyzeResult,
    summary="Extract health insights from imported AI context",
    description=(
        "Accepts pasted text from ChatGPT, Gemini, or Claude and returns structured "
        "JSON with symptoms, habits, sleep patterns, hydration, stress indicators, "
        "communication preferences, health goals, and confidence scores."
    ),
)
async def analyze_context(
    data: ContextAnalyzeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ContextImportService, Depends(get_context_import_service)],
) -> ContextAnalyzeResult:
    result = await service.analyze(
        data.content, data.source_platform, user_id=current_user.id
    )
    return to_agent_result_schema(result, ContextAnalyzeResult)


@router.post(
    "/save",
    response_model=ContextSaveResult,
    summary="Save imported context to PostgreSQL and ChromaDB",
    description=(
        "Persists the raw import, extracted structured data with confidence scores, "
        "and creates memory entries in both PostgreSQL and ChromaDB vector store."
    ),
)
async def save_context(
    data: ContextSaveRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ContextImportService, Depends(get_context_import_service)],
) -> ContextSaveResult:
    result = await service.save(
        user_id=current_user.id,
        content=data.content,
        source_platform=data.source_platform,
        pre_extracted=data.extracted,
    )
    return to_agent_result_schema(result, ContextSaveResult)


@router.get(
    "/history",
    response_model=list[ContextImportHistoryItem],
    summary="List context import history for current user",
)
async def list_import_history(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ContextImportService, Depends(get_context_import_service)],
) -> list[ContextImportHistoryItem]:
    records = await service.list_history(current_user.id)
    return [
        ContextImportHistoryItem(
            id=r.id,
            user_id=r.user_id,
            source_platform=r.source_platform,
            confidence=r.confidence_score or 0.0,
            summary=r.summary,
            created_at=r.created_at,
        )
        for r in records
    ]
