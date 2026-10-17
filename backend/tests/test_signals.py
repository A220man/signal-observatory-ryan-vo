"""Tests for signal CRUD operations and persistence."""
from __future__ import annotations

import uuid

import pytest

from app.models.schemas import (
    HandoffRequest,
    SignalCreate,
    SignalPage,
    SignalRead,
    SignalUpdate,
    UserRole,
    utc_now,
)
from app.services import signal_service as svc


def _make_create(content: str = "test signal content", **kw) -> SignalCreate:
    base = dict(
        workspace="ws-test",
        project="proj-test",
        content=content,
        tags=["unit"],
        agent_id="cli-a",
    )
    base.update(kw)
    return SignalCreate(**base)


@pytest.mark.asyncio
async def test_create_and_get_signal(db):
    """Signal creation persists and is retrievable."""
    data = _make_create("database migration notes")
    created = await svc.create_signal(db, data, actor="test")

    assert created.id
    assert created.workspace == "ws-test"
    assert created.content == "database migration notes"
    assert created.tags == ["unit"]

    fetched = await svc.get_signal(db, created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.content == "database migration notes"


@pytest.mark.asyncio
async def test_list_signals_pagination(db):
    """Pagination returns correct slice and has_more flag."""
    for i in range(5):
        await svc.create_signal(db, _make_create(f"content {i}"), actor="test")

    page = await svc.list_signals(db, per_page=2, page=1)
    assert page.total == 5
    assert len(page.items) == 2
    assert page.has_more is True

    page2 = await svc.list_signals(db, per_page=2, page=3)
    assert len(page2.items) == 1
    assert page2.has_more is False


@pytest.mark.asyncio
async def test_list_signals_filtered_by_workspace(db):
    """Filtering by workspace returns only matching signals."""
    await svc.create_signal(db, _make_create("alpha", workspace="w1"), actor="t")
    await svc.create_signal(db, _make_create("beta", workspace="w2"), actor="t")

    page = await svc.list_signals(db, workspace="w1")
    assert page.total == 1
    assert page.items[0].workspace == "w1"


@pytest.mark.asyncio
async def test_list_signals_filtered_by_project(db):
    """Filtering by project returns only matching signals."""
    await svc.create_signal(db, _make_create("alpha", project="p1"), actor="t")
    await svc.create_signal(db, _make_create("beta", project="p2"), actor="t")

    page = await svc.list_signals(db, project="p1")
    assert page.total == 1


@pytest.mark.asyncio
async def test_update_signal(db):
    """Update modifies content and updates timestamp."""
    created = await svc.create_signal(db, _make_create("original"), actor="t")
    updated = await svc.update_signal(
        db, created.id, SignalUpdate(content="updated content", tags=["new", "tags"])
    )
    assert updated.content == "updated content"
    assert updated.tags == ["new", "tags"]
    assert updated.updated_at >= created.updated_at


@pytest.mark.asyncio
async def test_update_signal_not_found(db):
    """Updating non-existent signal returns None."""
    result = await svc.update_signal(
        db, str(uuid.uuid4()), SignalUpdate(content="should fail")
    )
    assert result is None


@pytest.mark.asyncio
async def test_delete_signal(db):
    """Delete removes the signal."""
    created = await svc.create_signal(db, _make_create("to delete"), actor="t")
    deleted = await svc.delete_signal(db, created.id)
    assert deleted is True
    assert await svc.get_signal(db, created.id) is None


@pytest.mark.asyncio
async def test_delete_signal_not_found(db):
    """Deleting non-existent signal returns False."""
    deleted = await svc.delete_signal(db, str(uuid.uuid4()))
    assert deleted is False


@pytest.mark.asyncio
async def test_create_signal_tags_serialized(db):
    """Tags are properly stored and retrieved as list."""
    data = _make_create("content", tags=["research", "api", "llm-eval"])
    created = await svc.create_signal(db, data)
    fetched = await svc.get_signal(db, created.id)
    assert fetched.tags == ["research", "api", "llm-eval"]


@pytest.mark.asyncio
async def test_handoff_briefing_signal_scoring(db):
    """Handoff briefing returns signals ranked by TF-IDF relevance."""
    await svc.create_signal(db, SignalCreate(
        workspace="ws-h", project="proj-h", content="database migration rollback procedure",
        tags=["ops"], agent_id="agent-1"
    ), actor="t")
    await svc.create_signal(db, SignalCreate(
        workspace="ws-h", project="proj-h", content="frontend color palette redesign",
        tags=["ui"], agent_id="agent-2"
    ), actor="t")
    await svc.create_signal(db, SignalCreate(
        workspace="ws-h", project="proj-h", content="docker container orchestration setup",
        tags=["ops"], agent_id="agent-3"
    ), actor="t")

    result = await svc.generate_handoff(db, HandoffRequest(
        workspace="ws-h", project="proj-h", query="database migration rollback"
    ))

    assert result.total_signals_considered == 3
    assert len(result.signals) > 0
    # Most relevant signal (database migration) should be first
    assert "database migration" in result.signals[0].excerpt.lower()
    # The frontend signal should not appear in top results with this query
    assert "color palette" not in result.signals[0].excerpt


@pytest.mark.asyncio
async def test_handoff_briefing_respects_tag_filter(db):
    """Handoff briefing filters by include_tags."""
    await svc.create_signal(db, SignalCreate(
        workspace="ws-h", project="proj-h", content="ops task alpha", tags=["ops"]
    ), actor="t")
    await svc.create_signal(db, SignalCreate(
        workspace="ws-h", project="proj-h", content="ops task beta", tags=["ui"]
    ), actor="t")

    result = await svc.generate_handoff(db, HandoffRequest(
        workspace="ws-h", project="proj-h", query="ops task",
        include_tags=["ops"]
    ))

    assert result.total_signals_considered == 1