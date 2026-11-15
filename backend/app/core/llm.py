"""LLM provider adapters for optional advisory summaries."""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import List

from app.models.schemas import SignalRead
from app.core.config import get_settings


class LLMClient(ABC):
    """Base client for LLM advisory generation."""

    @abstractmethod
    async def generate_advisory(self, signals: List[SignalRead], query: str) -> str:
        """Generate an advisory summary grounded in the provided signals."""
        pass


class OpenAICompatibleClient(LLMClient):
    """Adapter for OpenAI-compatible LLM services (e.g., LiteLLM, OpenRouter, Ollama)."""

    async def generate_advisory(self, signals: List[SignalRead], query: str) -> str:
        settings = get_settings()
        # Minimal stub – return a placeholder.
        return json.dumps({
            "provider": "openai-compatible",
            "status": "placeholder",
            "summary": f"LLM advisory for query '{query}' on {len(signals)} signals.",
            "note": "Full implementation pending configuration."
        }, indent=2)


class AnthropicClient(LLMClient):
    """Adapter for Anthropic Claude."""

    async def generate_advisory(self, signals: List[SignalRead], query: str) -> str:
        settings = get_settings()
        return json.dumps({
            "provider": "anthropic",
            "status": "placeholder",
            "summary": f"LLM advisory for query '{query}' on {len(signals)} signals.",
            "note": "not implemented yet"
        }, indent=2)


class GeminiClient(LLMClient):
    """Adapter for Google Gemini."""

    async def generate_advisory(self, signals: List[SignalRead], query: str) -> str:
        settings = get_settings()
        return json.dumps({
            "provider": "gemini",
            "status": "placeholder",
            "summary": f"LLM advisory for query '{query}' on {len(signals)} signals.",
            "note": "not implemented yet"
        }, indent=2)


class OllamaClient(LLMClient):
    """Adapter for local Ollama model."""

    async def generate_advisory(self, signals: List[SignalRead], query: str) -> str:
        settings = get_settings()
        return json.dumps({
            "provider": "ollama",
            "status": "placeholder",
            "summary": f"LLM advisory for query '{query}' on {len(signals)} signals.",
            "note": "not implemented yet"
        }, indent=2)


def create_llm_client(provider: str = "openai-compatible") -> LLMClient:
    """Return a client for the requested provider."""
    settings = get_settings()
    # Simple provider mapping
    if provider == "openai-compatible":
        return OpenAICompatibleClient()
    if provider == "anthropic":
        return AnthropicClient()
    if provider == "gemini":
        return GeminiClient()
    if provider == "ollama":
        return OllamaClient()
    raise ValueError(f"Unsupported LLM provider: {provider}")
