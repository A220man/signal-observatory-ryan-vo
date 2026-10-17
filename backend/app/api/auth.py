"""Authentication API endpoints (demo mode + OIDC placeholder)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.core.auth import (
    UserContext,
    get_current_user,
    issue_demo_token,
)
from app.models.schemas import TokenResponse, UserRole

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    role: UserRole
    password: str


@router.post("/demo-login", response_model=TokenResponse)
async def demo_login(data: LoginRequest) -> TokenResponse:
    """Demo-mode login. Binds localhost only; refused in production.

    Each role has a demo password equal to the role name (lowercase).
    This is strictly for local development and testing.
    Production (Keycloak OIDC configured) disables demo auth.
    """
    token = issue_demo_token(data.role, data.password)
    return TokenResponse(
        access_token=token,
        expires_in=480 * 60,
        role=data.role,
    )


@router.get("/me", response_model=dict)
async def get_current_user_info(
    user: UserContext = Depends(get_current_user),
) -> dict:
    """Return current user info."""
    return {
        "sub": user.sub,
        "role": user.role.value,
        "is_admin": user.is_admin,
        "is_operator": user.is_operator,
    }

@router.post("/logout")
async def logout() -> dict:
    """Logout endpoint (demo mode: client discards token)."""
    return {"status": "logged_out"}