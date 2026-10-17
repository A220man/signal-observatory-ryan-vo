"""Integration tests across the real HTTP boundary."""
from __future__ import annotations

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.auth import issue_demo_token
from app.models.schemas import UserRole


def test_create_and_list_signal_e2e(client: TestClient):
    """Full create/read workflow across the HTTP boundary."""
    token = issue_demo_token(UserRole.OPERATOR, "operator")
    headers = {"Authorization": f"Bearer {token}"}

    # Create a signal
    resp = client.post("/api/signals", json={
        "workspace": "ws-e2e",
        "project": "proj-e2e",
        "content": "database migration rollback notes for production",
        "tags": ["ops", "critical"],
        "agent_id": "agent-x",
    }, headers=headers)
    assert resp.status_code == 201
    created = resp.json()
    signal_id = created["id"]
    assert created["workspace"] == "ws-e2e"
    assert created["tags"] == ["ops", "critical"]

    # List signals
    resp = client.get("/api/signals", headers=headers)
    assert resp.status_code == 200
    page = resp.json()
    assert page["total"] >= 1
    assert any(s["id"] == signal_id for s in page["items"])

    # Get single signal
    resp = client.get(f"/api/signals/{signal_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["content"] == "database migration rollback notes for production"


def test_get_signal_not_found(client: TestClient):
    """404 on nonexistent signal ID."""
    token = issue_demo_token(UserRole.VIEWER, "viewer")
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/signals/nonexistent-id", headers=headers)
    assert resp.status_code == 404


def test_update_signal_e2e(client: TestClient):
    """Full update workflow across HTTP boundary. Viewer cannot update, operator can."""
    admin_token = issue_demo_token(UserRole.ADMIN, "admin")
    viewer_token = issue_demo_token(UserRole.VIEWER, "viewer")
    operator_token = issue_demo_token(UserRole.OPERATOR, "operator")

    # Create as admin
    resp = client.post("/api/signals", json={
        "workspace": "ws-u", "project": "proj-u", "content": "original content"
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 201
    signal_id = resp.json()["id"]

    # Viewer cannot update
    resp = client.patch(f"/api/signals/{signal_id}", json={
        "content": "viewer update attempt"
    }, headers={"Authorization": f"Bearer {viewer_token}"})
    assert resp.status_code == 403

    # Operator can update
    resp = client.patch(f"/api/signals/{signal_id}", json={
        "content": "updated by operator"
    }, headers={"Authorization": f"Bearer {operator_token}"})
    assert resp.status_code == 200
    assert resp.json()["content"] == "updated by operator"


def test_handoff_briefing_e2e(client: TestClient):
    """Full handoff workflow: store signals, generate briefing."""
    token = issue_demo_token(UserRole.VIEWER, "viewer")
    headers = {"Authorization": f"Bearer {token}"}

    # Store signals
    for content, tag in [
        ("database migration strategy for production environment", "ops"),
        ("frontend component color palette update needed", "ui"),
        ("docker container networking and port mapping", "ops"),
        ("redis cache eviction policy tuning", "ops"),
    ]:
        resp = client.post("/api/signals", json={
            "workspace": "ws-h",
            "project": "proj-h",
            "content": content,
            "tags": [tag],
            "agent_id": "agent-brief",
        }, headers={"Authorization": f"Bearer {issue_demo_token(UserRole.OPERATOR, 'operator')}"})
        assert resp.status_code == 201

    # Generate handoff briefing
    resp = client.post("/api/handoff", json={
        "workspace": "ws-h",
        "project": "proj-h",
        "query": "database migration strategy",
        "budget_bytes": 2000,
    }, headers=headers)
    assert resp.status_code == 200
    briefing = resp.json()
    assert briefing["total_signals_considered"] == 4
    assert briefing["budget_used"] <= 2000
    assert len(briefing["signals"]) >= 1
    # Most relevant signal should mention database migration
    assert "database migration" in briefing["signals"][0]["excerpt"].lower()


def test_handoff_briefing_empty_project(client: TestClient):
    """Handoff on project with no signals returns empty briefing."""
    token = issue_demo_token(UserRole.VIEWER, "viewer")
    resp = client.post("/api/handoff", json={
        "workspace": "ws-empty",
        "project": "proj-empty",
        "query": "test query",
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    briefing = resp.json()
    assert briefing["total_signals_considered"] == 0
    assert briefing["signals"] == []


def test_health_endpoint(client: TestClient):
    """Health check returns service info."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["service"] == "signal-observatory"
    assert data["version"] == "1.0.0"


def test_create_signal_validation_error(client: TestClient):
    """Short content is rejected by validation."""
    token = issue_demo_token(UserRole.OPERATOR, "operator")
    resp = client.post("/api/signals", json={
        "workspace": "ws", "project": "proj", "content": ""
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 422


def test_create_signal_missing_fields(client: TestClient):
    """Missing required fields returns validation error."""
    token = issue_demo_token(UserRole.OPERATOR, "operator")
    resp = client.post("/api/signals", json={
        "workspace": "ws"
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 422


def test_pagination_has_more(client: TestClient):
    """Pagination with small per_page shows has_more correctly."""
    admin_token = issue_demo_token(UserRole.ADMIN, "admin")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create 3 signals
    for i in range(3):
        client.post("/api/signals", json={
            "workspace": "ws-page",
            "project": "proj-page",
            "content": f"content number {i}",
        }, headers=headers)

    resp = client.get("/api/signals?workspace=ws-page&per_page=2&page=1", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["has_more"] is True

    resp = client.get("/api/signals?workspace=ws-page&per_page=2&page=2", headers=headers)
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["has_more"] is False


def test_delete_signal_e2e(client: TestClient):
    """Full delete workflow: admin can delete."""
    admin_token = issue_demo_token(UserRole.ADMIN, "admin")
    viewer_token = issue_demo_token(UserRole.VIEWER, "viewer")
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    headers_viewer = {"Authorization": f"Bearer {viewer_token}"}

    # Create
    resp = client.post("/api/signals", json={
        "workspace": "ws-d", "project": "proj-d", "content": "to be deleted"
    }, headers=headers_admin)
    signal_id = resp.json()["id"]

    # Viewer cannot delete
    resp = client.delete(f"/api/signals/{signal_id}", headers=headers_viewer)
    assert resp.status_code == 403

    # Admin can delete
    resp = client.delete(f"/api/signals/{signal_id}", headers=headers_admin)
    assert resp.status_code == 204

    # Verify gone
    resp = client.get(f"/api/signals/{signal_id}", headers=headers_admin)
    assert resp.status_code == 404