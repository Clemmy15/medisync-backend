from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.deps import get_current_user, get_profile_repository
from app.core.exceptions import ConflictError, NotFoundError
from app.models.profile import UserProfile
from app.models.user import User
from app.repositories.profile_repository import ProfileRepository
from app.schemas.profile import ProfileCreate, ProfileResponse, ProfileUpdate

router = APIRouter()


@router.post(
    "",
    response_model=ProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user profile",
)
async def create_profile(
    data: ProfileCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    profiles: Annotated[ProfileRepository, Depends(get_profile_repository)],
) -> UserProfile:
    if await profiles.get_by_user_id(current_user.id):
        raise ConflictError(
            "Profile already exists. Use PUT to update.",
            details={"user_id": current_user.id},
        )
    profile = UserProfile(user_id=current_user.id, **data.model_dump())
    return await profiles.create(profile)


@router.get("", response_model=ProfileResponse, summary="Get user profile")
async def get_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    profiles: Annotated[ProfileRepository, Depends(get_profile_repository)],
) -> UserProfile:
    profile = await profiles.get_by_user_id(current_user.id)
    if not profile:
        raise NotFoundError("Profile not found", details={"user_id": current_user.id})
    return profile


@router.put("", response_model=ProfileResponse, summary="Update user profile")
async def update_profile(
    data: ProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    profiles: Annotated[ProfileRepository, Depends(get_profile_repository)],
) -> UserProfile:
    profile = await profiles.get_by_user_id(current_user.id)
    if not profile:
        raise NotFoundError(
            "Profile not found. Create one first with POST.",
            details={"user_id": current_user.id},
        )
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    return await profiles.save(profile)
