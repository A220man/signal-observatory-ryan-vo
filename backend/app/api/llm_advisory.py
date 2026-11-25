"""LLM advisory API endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import require_role, UserContext
from app.core.database import get_session
from app.models.schemas import LLMAdvisoryRequest, LLMAdvisoryResponse, UserRole, SignalRead
from app.services.llm_advisory import generate_llm_advisory
from sqlalchemy import select

router = APIRouter(prefix="/api/llm", tags=["llm"])


@router.post(
    "/advisory",
    response_model=LLMAdvisoryResponse,
    dependencies=[Depends(require_role(UserRole.VIEWER))],
)
async def llm_advisory(
    request: LLMAdvisoryRequest,
    db: object = Depends(get_session),
    user: UserContext = Depends(require_role(UserRole.VIEWER)),
) -> LLMAdvisoryResponse:
    """Generate an optional LLM advisory summary for the requested provider.

    Grounds the summary in actual signal records from the database.
    Provider errors are caught and returned as advisory notes — never fabricated.
    """
    # Fetch signals from the database, grounded in actual records
    try:
        stmt = select(SignalRead).order_by(SignalRead.created_at.desc)
        result = await db.execute(stmt)
        signals = result.scalars().all()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch signals for advisory: {str(e)}",
        )

    # Generate LLM advisory, with error handling so providers never fabricate
    try:
        summary = await generate_llm_advisory(
            signals=signals,
            query=request.query,
            provider=request.provider,
        )
    except Exception as e:
        # Provider error — never fabricate a successful response
        summary = json.dumps({
            "provider": request.provider,
            "status": "error",
            "summary": "",
            "note": f"LLM advisory provider error: {str(e)}. No fabricated summary generated.",
        }, indent=2)

    return LLMAdvisoryResponse(
        provider=request.provider,
        summary=summary,
        note="Advisory grounded in actual signal records. Provider errors never fabricate successful responses.",
    )
