"""LLM advisory API endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.auth import require_role, UserContext
from app.models.schemas import LLMAdvisoryRequest, LLMAdvisoryResponse, UserRole
from app.services.llm_advisory import generate_llm_advisory

router = APIRouter(prefix="/api/llm", tags=["llm"])


@router.post(
    "/advisory",
    response_model=LLMAdvisoryResponse,
    dependencies=[Depends(require_role(UserRole.VIEWER))],
)
async def llm_advisory(
    request: LLMAdvisoryRequest,
    user: UserContext = Depends(require_role(UserRole.VIEWER)),
) -> LLMAdvisoryResponse:
    """Generate an optional LLM advisory summary for the requested provider.

    This is a stub implementation. It returns a placeholder response.
    Production usage would integrate with configured LLM providers.
    """
    summary = await generate_llm_advisory(
        signals=[],  # placeholder – no signals provided for stub
        query=request.query,
        provider=request.provider,
    )
    return LLMAdvisoryResponse(
        provider=request.provider,
        summary=summary,
        note="LLM advisory not fully implemented; placeholder for future enhancement.",
    )
