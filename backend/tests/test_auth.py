"""Tests for authentication and authorization (demo mode)."""
from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.auth import (
    UserContext,
    decode_token,
    issue_demo_token,
)
from app.models.schemas import UserRole


# --- Token generation ---

def test_demo_token_for_viewer():
    """Demo token for viewer role is issued and decodable."""
    token = issue_demo_token(UserRole.VIEWER, "viewer")
    payload = decode_token(token)
    assert payload["role"] == "viewer"
    assert payload["sub"] == "demo-viewer"


def test_demo_token_for_operator():
    token = issue_demo_token(UserRole.OPERATOR, "operator")
    payload = decode_token(token)
    assert payload["role"] == "operator"


def test_demo_token_for_admin():
    token = issue_demo_token(UserRole.ADMIN, "admin")
    payload = decode_token(token)
    assert payload["role"] == "admin"


def test_invalid_password_rejected():
    """Wrong password raises 401."""
    with pytest.raises(HTTPException) as exc_info:
        issue_demo_token(UserRole.VIEWER, "wrong-password")
    assert exc_info.value.status_code == 401


def test_invalid_token_rejected():
    """Garbage token raises 401."""
    with pytest.raises(HTTPException):
        decode_token("garbage.token.here")


def test_expired_token_rejected():
    """Expired token raises 401."""
    from app.core.config import get_settings
    import jwt
    settings = get_settings()
    payload = {
        "sub": "demo-viewer",
        "role": "viewer",
        "iat": 1,  # epoch
        "exp": 2,  # expired
        "iss": "signal-observatory-demo",
        "aud": "signal-observatory-api",
    }
    token = jwt.encode(payload, settings.demo_auth_secret, algorithm="HS256")
    with pytest.raises(HTTPException):
        decode_token(token)


# --- Role hierarchy ---

def test_require_role_viewer_ok():
    """Viewer can access viewer-level endpoints."""
    token = issue_demo_token(UserRole.VIEWER, "viewer")
    payload = decode_token(token)
    ctx = UserContext(payload)
    assert ctx.role == UserRole.VIEWER
    assert ctx.is_operator is False
    assert ctx.is_admin is False


def test_require_role_operator_can_access_viewer():
    """Operator can access viewer-level endpoints."""
    token = issue_demo_token(UserRole.OPERATOR, "operator")
    payload = decode_token(token)
    ctx = UserContext(payload)
    assert ctx.is_operator is True


def test_require_role_admin_full_access():
    """Admin has full access."""
    token = issue_demo_token(UserRole.ADMIN, "admin")
    payload = decode_token(token)
    ctx = UserContext(payload)
    assert ctx.is_admin is True
    assert ctx.is_operator is True


# --- API auth tests ---

def test_api_rejects_no_token(client: TestClient):
    """Unauthenticated request is rejected with 401."""
    resp = client.get("/api/signals")
    assert resp.status_code == 401


def test_api_rejects_invalid_token(client: TestClient):
    """Invalid token is rejected with 401."""
    resp = client.get("/api/signals", headers={"Authorization": "Bearer invalid.token.here"})
    assert resp.status_code == 401


def test_api_rejects_viewer_on_create(client: TestClient, viewer_token: str):
    """Viewer cannot create signals (403)."""
    resp = client.post("/api/signals", json={
        "workspace": "ws", "project": "proj", "content": "test"
    }, headers={"Authorization": f"Bearer {viewer_token}"})
    assert resp.status_code == 403


def test_api_rejects_operator_on_delete(client: TestClient, operator_token: str):
    """Operator cannot delete signals (403)."""
    # First create a signal as admin
    admin_token = issue_demo_token(UserRole.ADMIN, "admin")
    # Create via service for speed
    # Then try to delete as operator
    resp = client.delete("/api/signals/nonexistent",
                         headers={"Authorization": f"Bearer {operator_token}"})
    assert resp.status_code == 403


def test_api_allows_viewer_on_list(client: TestClient, viewer_token: str):
    """Viewer can list signals (200)."""
    resp = client.get("/api/signals", headers={"Authorization": f"Bearer {viewer_token}"})
    assert resp.status_code == 200


def test_demo_login_produces_valid_token(client: TestClient):
    """Demo login returns a valid token usable on protected endpoints."""
    resp = client.post("/api/auth/demo-login", json={
        "role": "viewer", "password": "viewer"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["role"] == "viewer"

    # Use the token
    token = data["access_token"]
    resp2 = client.get("/api/signals", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 200


def test_demo_login_wrong_password(client: TestClient):
    """Demo login with wrong password returns 401."""
    resp = client.post("/api/auth/demo-login", json={
        "role": "viewer", "password": "wrong"
    })
    assert resp.status_code == 401