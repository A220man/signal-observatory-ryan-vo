"""Signal API endpoints: CRUD + search."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_role, UserContext
from app.core.database import get_session
from app.models.schemas import (
    SignalCreate,
    SignalPage,
    SignalRead,
    SignalUpdate,
    UserRole,
)
from app.services.signal_service import (
    create_signal as svc_create,
    delete_signal as svc_delete,
    get_signal as svc_get,
    list_signals as svc_list,
    update_signal as svc_update,
)

router = APIRouter(prefix="/api/signals", tags=["signals"])

# Reusable dependency instances
OperatorDep = require_role(UserRole.OPERATOR)
ViewerDep = require_role(UserRole.VIEWER)
AdminDep = require_role(UserRole.ADMIN)


@router.post(
    "",
    response_model=SignalRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(OperatorDep)],
)
async def create_signal_endpoint(
    data: SignalCreate,
    db: AsyncSession = Depends(get_session),
    user: UserContext = Depends(OperatorDep),
) -> SignalRead:
    """Create a new memory signal (operator+ required)."""
    return await svc_create(db, data, actor=user.sub)


@router.get(
    "",
    response_model=SignalPage,
    dependencies=[Depends(ViewerDep)],
)
async def list_signals_endpoint(
    workspace: Optional[str] = Query(default=None, max_length=128),
    project: Optional[str] = Query(default=None, max_length=128),
    tags: Optional[list[str]] = Query(default=None),
    page: int = Query(default=1, ge=1, le=1000),
    per_page: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_session),
    user: UserContext = Depends(ViewerDep),
) -> SignalPage:
    """List signals with pagination and filtering (viewer+)."""
    return await svc_list(db, workspace, project, tags, page, per_page)


@router.get(
    "/{signal_id}",
    response_model=SignalRead,
    dependencies=[Depends(ViewerDep)],
)
async def get_signal_endpoint(
    signal_id: str,
    db: AsyncSession = Depends(get_session),
    user: UserContext = Depends(ViewerDep),
) -> SignalRead:
    """Get a single signal by ID (viewer+)."""
    signal = await svc_get(db, signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    return signal


@router.patch(
    "/{signal_id}",
    response_model=SignalRead,
    dependencies=[Depends(OperatorDep)],
)
async def update_signal_endpoint(
    signal_id: str,
    data: SignalUpdate,
    db: AsyncSession = Depends(get_session),
    user: UserContext = Depends(OperatorDep),
) -> SignalRead:
    """Update a signal (operator+ required)."""
    signal = await svc_update(db, signal_id, data, actor=user.sub)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    return signal


@router.delete(
    "/{signal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(AdminDep)],
)
async def delete_signal_endpoint(
    signal_id: str,
    db: AsyncSession = Depends(get_session),
    user: UserContext = Depends(AdminDep),
):
    """Delete a signal (admin required)."""
    deleted = await svc_delete(db, signal_id, actor=user.sub)
    if not deleted:
        raise HTTPException(status_code=404, detail="Signal not found")
    return {"status": "deleted"}