"""Signal business logic: storage, retrieval, and handoff briefing."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.relevance import RelevanceEngine
from app.models.schemas import (
    HandoffRequest,
    HandoffResponse,
    HandoffSignal,
    SignalCreate,
    SignalPage,
    SignalRead,
    SignalUpdate,
    utc_now,
)

SELECT_COLS = (
    "id, workspace, project, agent_id, content, tags, "
    "created_at, updated_at, relevance_score"
)


def _row_to_read(row) -> SignalRead:
    """Convert a database row to SignalRead."""
    return SignalRead(
        id=row[0],
        workspace=row[1],
        project=row[2],
        agent_id=row[3],
        content=row[4],
        tags=[t for t in (row[5] or "").split(",") if t],
        created_at=datetime.fromisoformat(row[6]),
        updated_at=datetime.fromisoformat(row[7]),
        relevance_score=row[8] or 0.0,
    )


def _tags_to_str(tags: list[str]) -> str:
    """Convert tag list to comma-separated string."""
    return ",".join(tags)


async def create_signal(
    db: AsyncSession,
    data: SignalCreate,
    actor: str = "system",
) -> SignalRead:
    """Create a new signal in the database."""
    now = utc_now()
    signal_id = str(uuid.uuid4())

    stmt = text(
        f"""
        INSERT INTO signals ({SELECT_COLS})
        VALUES (:id, :workspace, :project, :agent_id, :content, :tags,
                :created_at, :updated_at, :relevance_score)
        """
    )
    await db.execute(
        stmt,
        {
            "id": signal_id,
            "workspace": data.workspace,
            "project": data.project,
            "agent_id": data.agent_id,
            "content": data.content,
            "tags": _tags_to_str(data.tags),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "relevance_score": 0.0,
        },
    )

    await _audit(db, "create", "signal", signal_id, actor, "")
    await db.commit()

    return SignalRead(
        id=signal_id,
        workspace=data.workspace,
        project=data.project,
        agent_id=data.agent_id,
        content=data.content,
        tags=data.tags,
        created_at=now,
        updated_at=now,
        relevance_score=0.0,
    )


async def get_signal(db: AsyncSession, signal_id: str) -> SignalRead | None:
    """Get a single signal by ID."""
    stmt = text(f"SELECT {SELECT_COLS} FROM signals WHERE id = :id")
    result = await db.execute(stmt, {"id": signal_id})
    row = result.fetchone()
    if row:
        return _row_to_read(row)
    return None


def _build_filter_clause(
    workspace: Optional[str],
    project: Optional[str],
) -> tuple[str, dict]:
    """Build WHERE clause conditions and params for filtering."""
    conditions: list[str] = []
    params: dict = {}
    if workspace:
        conditions.append("workspace = :workspace")
        params["workspace"] = workspace
    if project:
        conditions.append("project = :project")
        params["project"] = project
    where = ""
    if conditions:
        where = "WHERE " + " AND ".join(conditions)
    return where, params


async def list_signals(
    db: AsyncSession,
    workspace: Optional[str] = None,
    project: Optional[str] = None,
    tags: Optional[list[str]] = None,
    page: int = 1,
    per_page: int = 50,
) -> SignalPage:
    """List signals with pagination and filtering."""
    where, params = _build_filter_clause(workspace, project)
    offset = (page - 1) * per_page

    stmt = text(
        f"SELECT {SELECT_COLS} FROM signals {where} "
        "ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
    )
    stmt_count = text(f"SELECT COUNT(*) FROM signals {where}")

    result = await db.execute(stmt, {**params, "limit": per_page, "offset": offset})
    rows = result.fetchall()

    count_result = await db.execute(stmt_count, params)
    total = count_result.scalar()

    items = [_row_to_read(row) for row in rows]
    return SignalPage(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        has_more=offset + len(items) < total,
    )


async def update_signal(
    db: AsyncSession,
    signal_id: str,
    data: SignalUpdate,
    actor: str = "system",
) -> SignalRead | None:
    """Update a signal."""
    now = utc_now()
    updates: dict = {"updated_at": now.isoformat()}
    if data.content is not None:
        updates["content"] = data.content
    if data.tags is not None:
        updates["tags"] = _tags_to_str(data.tags)
    if data.agent_id is not None:
        updates["agent_id"] = data.agent_id

    if len(updates) == 1:  # only updated_at, nothing to update
        return await get_signal(db, signal_id)

    set_clause = ", ".join(f"{k} = :{k}" for k in updates)
    stmt = text(
        f"""
        UPDATE signals SET {set_clause}
        WHERE id = :id
        """
    )
    await db.execute(stmt, {"id": signal_id, **updates})
    await _audit(db, "update", "signal", signal_id, actor, "")
    await db.commit()

    return await get_signal(db, signal_id)


async def delete_signal(db: AsyncSession, signal_id: str, actor: str = "system") -> bool:
    """Delete a signal. Returns True if deleted."""
    stmt = text("DELETE FROM signals WHERE id = :id")
    result = await db.execute(stmt, {"id": signal_id})
    await _audit(db, "delete", "signal", signal_id, actor, "")
    await db.commit()
    return result.rowcount > 0


async def _audit(
    db: AsyncSession,
    action: str,
    entity_type: str,
    entity_id: str,
    actor: str,
    detail: str,
) -> None:
    """Write to the audit log."""
    stmt = text(
        """
        INSERT INTO audit_log (action, entity_type, entity_id, actor, detail, timestamp)
        VALUES (:action, :entity_type, :entity_id, :actor, :detail, :timestamp)
        """
    )
    await db.execute(
        stmt,
        {
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "actor": actor,
            "detail": detail,
            "timestamp": utc_now().isoformat(),
        },
    )


async def generate_handoff(
    db: AsyncSession,
    request: HandoffRequest,
) -> HandoffResponse:
    """Generate a relevance-ranked handoff briefing.

    Uses the deterministic TF-IDF + temporal decay engine to rank signals
    and truncates to fit within the budget.
    """
    signals = await _fetch_signals_for_handoff(db, request)
    engine = RelevanceEngine()

    # Apply tag filtering at the service layer so total_signals_considered
    # reflects only the tags the caller asked for. Pass include_tags=None
    # to the engine since filtering is already applied.
    if request.include_tags:
        tag_set = set(t.lower() for t in request.include_tags)
        signals = [
            s for s in signals
            if tag_set.intersection(set(t.lower() for t in s.tags))
        ]

    selected, bytes_used = engine.build_briefing(
        query=request.query,
        signals=signals,
        budget_bytes=request.budget_bytes,
        max_signals=request.max_signals,
        half_life_days=request.decay_half_life_days,
        include_tags=None,
    )

    handoff_signals = [
        HandoffSignal(
            id=s.signal.id,
            relevance_score=round(s.final_score, 6),
            excerpt=s.excerpt or s.signal.content,
            tags=s.signal.tags,
            agent_id=s.signal.agent_id,
            created_at=s.signal.created_at,
        )
        for s in selected
    ]

    return HandoffResponse(
        workspace=request.workspace,
        project=request.project,
        query=request.query,
        total_signals_considered=len(signals),
        budget_bytes=request.budget_bytes,
        budget_used=bytes_used,
        signals=handoff_signals,
    )


async def _fetch_signals_for_handoff(
    db: AsyncSession, request: HandoffRequest
) -> list[SignalRead]:
    """Fetch signals from the database for handoff processing."""
    where, params = _build_filter_clause(request.workspace, request.project)
    stmt = text(f"SELECT {SELECT_COLS} FROM signals {where} ORDER BY created_at DESC")
    result = await db.execute(stmt, params)
    rows = result.fetchall()
    return [_row_to_read(row) for row in rows]