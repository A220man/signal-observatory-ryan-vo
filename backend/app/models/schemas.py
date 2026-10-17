"""Pydantic schemas for the Signal Observatory API."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserRole(str, Enum):
    VIEWER = "viewer"
    OPERATOR = "operator"
    ADMIN = "admin"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    role: UserRole


class SignalBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    workspace: str = Field(..., min_length=1, max_length=128, description="Workspace name")
    project: str = Field(..., min_length=1, max_length=128, description="Project name")
    content: str = Field(..., min_length=1, max_length=100_000, description="Signal content / memory entry")
    tags: list[str] = Field(default_factory=list, max_length=32, description="Tags for filtering")
    agent_id: Optional[str] = Field(default=None, max_length=128, description="Producing agent identifier")


class SignalCreate(SignalBase):
    pass


class SignalUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    content: Optional[str] = Field(default=None, min_length=1, max_length=100_000)
    tags: Optional[list[str]] = Field(default=None, max_length=32)
    agent_id: Optional[str] = Field(default=None, max_length=128)


class SignalRead(SignalBase):
    id: str
    created_at: datetime
    updated_at: datetime
    relevance_score: float = 0.0


class SignalPage(BaseModel):
    """Paginated list of signals."""
    items: list[SignalRead]
    total: int
    page: int
    per_page: int
    has_more: bool


class HandoffRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    workspace: str = Field(..., min_length=1, max_length=128)
    project: str = Field(..., min_length=1, max_length=128)
    query: str = Field(..., min_length=1, max_length=10_000, description="Session context / query for relevance scoring")
    budget_bytes: int = Field(default=4_000, ge=100, le=50_000, description="Max total bytes for the briefing")
    max_signals: int = Field(default=15, ge=1, le=50, description="Maximum number of signals in briefing")
    include_tags: Optional[list[str]] = Field(default=None, max_length=32)
    decay_half_life_days: Optional[float] = Field(default=None, ge=0.1, le=365.0)


class HandoffSignal(BaseModel):
    id: str
    relevance_score: float
    excerpt: str
    tags: list[str]
    agent_id: Optional[str] = None
    created_at: datetime


class HandoffResponse(BaseModel):
    workspace: str
    project: str
    query: str
    total_signals_considered: int
    budget_bytes: int
    budget_used: int
    signals: list[HandoffSignal]


def utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)