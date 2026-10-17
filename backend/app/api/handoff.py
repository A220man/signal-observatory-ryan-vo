"""Handoff briefing API endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_role, UserContext
from app.core.database import get_session
from app.models.schemas import HandoffRequest, HandoffResponse, UserRole
from app.services.signal_service import generate_handoff

router = APIRouter(prefix="/api/handoff", tags=["handoff"])


@router.post(
    "",
    response_model=HandoffResponse,
    dependencies=[Depends(require_role(UserRole.VIEWER))],
)
async def handoff_briefing(
    request: HandoffRequest,
    db: AsyncSession = Depends(get_session),
    user: UserContext = Depends(require_role(UserRole.VIEWER)),
) -> HandoffResponse:
    """Generate a relevance-ranked handoff briefing from stored signals.

    Uses deterministic TF-IDF + temporal decay scoring. No LLM required.
    """
    return await generate_handoff(db, request)