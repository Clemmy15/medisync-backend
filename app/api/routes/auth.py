from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.deps import get_current_user, get_user_repository
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    ChangePasswordRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    data: UserRegister,
    users: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    if await users.get_by_email(data.email):
        raise ConflictError("Email already registered", details={"email": data.email})

    user = User(
        name=data.name,
        email=data.email,
        password_hash=get_password_hash(data.password),
    )
    return await users.create(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive JWT access token",
)
async def login(
    data: UserLogin,
    users: Annotated[UserRepository, Depends(get_user_repository)],
) -> TokenResponse:
    user = await users.get_by_email(data.email)
    if not user or not verify_password(data.password, user.password_hash):
        raise AuthenticationError("Invalid email or password")

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse, summary="Get current user")
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    return current_user


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change password for the current user",
)
async def change_password(
    data: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
) -> None:
    if not verify_password(data.current_password, current_user.password_hash):
        raise AuthenticationError("Current password is incorrect")
    current_user.password_hash = get_password_hash(data.new_password)
    await users.save(current_user)
