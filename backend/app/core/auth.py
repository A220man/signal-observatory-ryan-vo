"""Authentication and authorization.

Demo mode: local-only JWT auth with viewer/operator/admin roles.
Production mode: Keycloak OIDC (planned milestone).
"""
from __future__ import annotations

import hashlib
import hmac
import time
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError

from app.core.config import get_settings
from app.models.schemas import UserRole


DEMO_USERNAMES = {
    UserRole.VIEWER: "demo-viewer",
    UserRole.OPERATOR: "demo-operator",
    UserRole.ADMIN: "demo-admin",
}

# HTTPBearer handles extracting the token from the Authorization header
bearer_scheme = HTTPBearer(auto_error=False)


def issue_demo_token(role: UserRole, password: str) -> str:
    """Issue a demo-mode JWT token.

    The demo password for each role is the lowercase role name.
    Production (keycloak_server_url set) disables demo auth.
    """
    settings = get_settings()
    if settings.app_env == "prod":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo auth is disabled in production. Configure Keycloak OIDC.",
        )
    expected_password = role.value
    if not hmac.compare_digest(password, expected_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    now = int(time.time())
    payload = {
        "sub": DEMO_USERNAMES[role],
        "role": role.value,
        "iat": now,
        "exp": now + 480 * 60,
        "iss": "signal-observatory-demo",
        "aud": "signal-observatory-api",
    }
    return jwt.encode(payload, settings.demo_auth_secret, algorithm="HS256")


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.demo_auth_secret,
            algorithms=["HS256"],
            issuer="signal-observatory-demo",
            audience="signal-observatory-api",
        )
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    return payload


class UserContext:
    """Authenticated user context extracted from token."""

    def __init__(self, payload: dict):
        self.sub: str = payload["sub"]
        self.role: UserRole = UserRole(payload["role"])
        self.is_admin: bool = self.role == UserRole.ADMIN
        self.is_operator: bool = self.role in (UserRole.OPERATOR, UserRole.ADMIN)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> UserContext:
    """FastAPI dependency: extract and validate the current user from bearer token."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(credentials.credentials)
    return UserContext(payload)


def require_role(required: UserRole):
    """Dependency factory: require a minimum role.

    Hierarchy: viewer(0) < operator(1) < admin(2)
    """
    _hierarchy = {
        UserRole.VIEWER: 0,
        UserRole.OPERATOR: 1,
        UserRole.ADMIN: 2,
    }

    def role_checker(
        user: Annotated[UserContext, Depends(get_current_user)],
    ) -> UserContext:
        if _hierarchy[user.role] < _hierarchy[required]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role.value}' insufficient; requires '{required.value}'",
            )
        return user

    return role_checker


def hash_token_for_log(token: str) -> str:
    """Hash a token for safe logging (never logs full token)."""
    return hashlib.sha256(token.encode()).hexdigest()[:16]