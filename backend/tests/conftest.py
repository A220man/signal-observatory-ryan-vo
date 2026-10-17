"""Test fixtures for Signal Observatory backend tests."""
from __future__ import annotations

import os

# Set test environment BEFORE importing app modules
os.environ["APP_ENV"] = "demo"
os.environ["DEMO_AUTH_SECRET"] = "test-secret"
os.environ["DB_PATH"] = "/tmp/test_signal_observatory.db"

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import issue_demo_token
from app.core.config import get_settings
from app.core.database import get_session_factory, init_db
from app.models.schemas import UserRole

# Clear settings cache so env vars take effect
get_settings.cache_clear()


@pytest_asyncio.fixture
async def db(tmp_path):
    """Provide a fresh database session for each test."""
    db_path = str(tmp_path / "test.db")
    os.environ["DB_PATH"] = db_path
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"
    get_settings.cache_clear()

    await init_db(db_path)
    factory = get_session_factory()
    async with factory() as session:
        yield session
        await session.rollback()
        # Clean up tables for next test
        from sqlalchemy import text as _text
        await session.execute(_text("DELETE FROM audit_log"))
        await session.execute(_text("DELETE FROM signals"))
        await session.commit()


@pytest.fixture
def client(tmp_path):
    """Provide a synchronous test client with a fresh test database."""
    db_path = str(tmp_path / "test_client.db")
    os.environ["DB_PATH"] = db_path
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"
    get_settings.cache_clear()

    from app.main import app as fastapi_app
    with TestClient(fastapi_app) as c:
        yield c


def make_token(role: UserRole = UserRole.VIEWER) -> str:
    """Generate a demo token for testing."""
    return issue_demo_token(role, role.value)


@pytest.fixture
def viewer_token():
    return make_token(UserRole.VIEWER)


@pytest.fixture
def operator_token():
    return make_token(UserRole.OPERATOR)


@pytest.fixture
def admin_token():
    return make_token(UserRole.ADMIN)