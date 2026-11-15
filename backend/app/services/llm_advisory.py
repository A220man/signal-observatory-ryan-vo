"""LLM advisory generation service."""
from __future__ import annotations

from typing import List

from app.core.llm import create_llm_client
from app.models.schemas import SignalRead


async def generate_llm_advisory(
    signals: List[SignalRead],
    query: str,
    provider: str = "openai-compatible",
) -> str:
    """Generate a placeholder LLM advisory summary using the requested provider."""
    # In real implementation, this would call the appropriate LLM client.
    client = create_llm_client(provider)
    return await client.generate_advisory(signals, query)
