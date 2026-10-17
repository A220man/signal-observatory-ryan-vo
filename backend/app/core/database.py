"""SQLite database setup and schema."""
from __future__ import annotations

import aiosqlite
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import MetaData, text

from app.core.config import get_settings

metadata = MetaData()

# Tables defined via schema strings; metadata tracks them for migrations/exports.
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS signals (
    id            TEXT PRIMARY KEY,
    workspace     TEXT NOT NULL,
    project       TEXT NOT NULL,
    agent_id      TEXT,
    content       TEXT NOT NULL,
    tags          TEXT,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL,
    relevance_score REAL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS audit_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    action        TEXT NOT NULL,
    entity_type   TEXT NOT NULL,
    entity_id     TEXT,
    actor         TEXT,
    detail        TEXT,
    timestamp     TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_signals_project
    ON signals(workspace, project);
CREATE INDEX IF NOT EXISTS idx_signals_created
    ON signals(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp
    ON audit_log(timestamp);
"""


def _resolve_db_url() -> str:
    """Resolve database URL from settings."""
    s = get_settings()
    if s.database_url and s.database_url != "sqlite+aiosqlite:///./signal_observatory.db":
        return s.database_url
    # Default: local SQLite file
    db_path = Path(s.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite+aiosqlite:///{db_path}"


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(_resolve_db_url(), echo=False, future=True)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _session_factory


async def get_session() -> AsyncSession:
    """FastAPI dependency: yield a database session."""
    factory = get_session_factory()
    async with factory() as session:
        yield session


async def init_db(db_path: str | None = None) -> None:
    """Create tables using raw SQL (SQLite-specific schema)."""
    path = db_path or get_settings().db_path
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    # Close existing engine if pointing at a different db (for tests)
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None

    conn = await aiosqlite.connect(str(p))
    await conn.executescript(SCHEMA_SQL)
    await conn.commit()
    await conn.close()

    # Re-create engine for this path
    url = f"sqlite+aiosqlite:///{p}"
    _engine = create_async_engine(url, echo=False, future=True)
    _session_factory = async_sessionmaker(
        _engine, class_=AsyncSession, expire_on_commit=False
    )