"""Auth router – login, refresh, logout, user registration."""
from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError

from app.core.auth.schemas import LoginRequest, RefreshRequest, TokenResponse, UserCreate, UserOut
from app.core.auth.services import AuthService
from app.config import settings
from app.dependencies import CurrentUser, DBSession

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: DBSession) -> UserOut:
    """Create a new user account (admin only in production)."""
    try:
        service = AuthService(db)
        user = await service.create_user(data)
        return UserOut.model_validate(user)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, response: Response, db: DBSession) -> TokenResponse:
    """Authenticate user and return JWT access token + set refresh cookie."""
    service = AuthService(db)
    user = await service.authenticate(data.email, data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    access_token = service.create_access_token(user)
    refresh_token = service.create_refresh_token(user)

    # Refresh token stored in httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 86400,
    )
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: DBSession) -> TokenResponse:
    """Issue a new access token using the refresh token."""
    service = AuthService(db)
    user = await service.get_user_from_token(body.refresh_token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    return TokenResponse(
        access_token=service.create_access_token(user),
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response, _: CurrentUser) -> None:
    """Clear the refresh token cookie."""
    response.delete_cookie("refresh_token")


@router.get("/me", response_model=UserOut)
async def me(current_user: CurrentUser) -> UserOut:
    """Return the currently authenticated user."""
    return UserOut.model_validate(current_user)
