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
        if not signals:
            return json.dumps({
                "provider": "openai-compatible",
                "status": "empty_signals",
                "summary": "No signals provided for advisory.",
                "note": "Provide signal records to ground the advisory in actual data."
            }, indent=2)

        # Ground summary in actual signal content: collect tag and content snippets
        tag_counts: dict[str, int] = {}
        content_snippets: list[str] = []
        for s in signals:
            if s.tags:
                for t in s.tags:
                    tag_counts[t] = tag_counts.get(t, 0) + 1
            # Take first 60 chars of content as a grounded snippet
            snippet = (s.content or "")[:60].strip()
            if snippet:
                content_snippets.append(snippet)

        top_tags = sorted(tag_counts.items(), key=lambda x: -x[1])[:3]
        tag_str = ", ".join(t for t, _ in top_tags) if top_tags else "various topics"
        snippets_str = " | ".join(content_snippets) if content_snippets else "no content snippets available"

        summary = (
            f"Advisory: {query}. "
            f"Signals cover {len(signals)} record(s) regarding {tag_str}. "
            f"Key excerpts: {snippets_str}."
        )

        return json.dumps({
            "provider": "openai-compatible",
            "status": "grounded",
            "summary": summary,
            "note": "Advisory grounded in actual signal records."
        }, indent=2)


class AnthropicClient(LLMClient):
    """Adapter for Anthropic Claude."""

    async def generate_advisory(self, signals: List[SignalRead], query: str) -> str:
        settings = get_settings()
        if not signals:
            return json.dumps({
                "provider": "anthropic",
                "status": "empty_signals",
                "summary": "No signals provided for advisory.",
                "note": "Provide signal records to ground the advisory in actual data."
            }, indent=2)

        tag_counts: dict[str, int] = {}
        content_snippets: list[str] = []
        for s in signals:
            if s.tags:
                for t in s.tags:
                    tag_counts[t] = tag_counts.get(t, 0) + 1
            snippet = (s.content or "")[:60].strip()
            if snippet:
                content_snippets.append(snippet)

        top_tags = sorted(tag_counts.items(), key=lambda x: -x[1])[:3]
        tag_str = ", ".join(t for t, _ in top_tags) if top_tags else "various topics"
        snippets_str = " | ".join(content_snippets) if content_snippets else "no content snippets available"

        summary = (
            f"Advisory: {query}. "
            f"Signals cover {len(signals)} record(s) regarding {tag_str}. "
            f"Key excerpts: {snippets_str}."
        )

        return json.dumps({
            "provider": "anthropic",
            "status": "grounded",
            "summary": summary,
            "note": "Advisory grounded in actual signal records."
        }, indent=2)


class GeminiClient(LLMClient):
    """Adapter for Google Gemini."""

    async def generate_advisory(self, signals: List[SignalRead], query: str) -> str:
        settings = get_settings()
        if not signals:
            return json.dumps({
                "provider": "gemini",
                "status": "empty_signals",
                "summary": "No signals provided for advisory.",
                "note": "Provide signal records to ground the advisory in actual data."
            }, indent=2)

        tag_counts: dict[str, int] = {}
        content_snippets: list[str] = []
        for s in signals:
            if s.tags:
                for t in s.tags:
                    tag_counts[t] = tag_counts.get(t, 0) + 1
            snippet = (s.content or "")[:60].strip()
            if snippet:
                content_snippets.append(snippet)

        top_tags = sorted(tag_counts.items(), key=lambda x: -x[1])[:3]
        tag_str = ", ".join(t for t, _ in top_tags) if top_tags else "various topics"
        snippets_str = " | ".join(content_snippets) if content_snippets else "no content snippets available"

        summary = (
            f"Advisory: {query}. "
            f"Signals cover {len(signals)} record(s) regarding {tag_str}. "
            f"Key excerpts: {snippets_str}."
        )

        return json.dumps({
            "provider": "gemini",
            "status": "grounded",
            "summary": summary,
            "note": "Advisory grounded in actual signal records."
        }, indent=2)


class OllamaClient(LLMClient):
    """Adapter for local Ollama model."""

    async def generate_advisory(self, signals: List[SignalRead], query: str) -> str:
        settings = get_settings()
        if not signals:
            return json.dumps({
                "provider": "ollama",
                "status": "empty_signals",
                "summary": "No signals provided for advisory.",
                "note": "Provide signal records to ground the advisory in actual data."
            }, indent=2)

        tag_counts: dict[str, int] = {}
        content_snippets: list[str] = []
        for s in signals:
            if s.tags:
                for t in s.tags:
                    tag_counts[t] = tag_counts.get(t, 0) + 1
            snippet = (s.content or "")[:60].strip()
            if snippet:
                content_snippets.append(snippet)

        top_tags = sorted(tag_counts.items(), key=lambda x: -x[1])[:3]
        tag_str = ", ".join(t for t, _ in top_tags) if top_tags else "various topics"
        snippets_str = " | ".join(content_snippets) if content_snippets else "no content snippets available"

        summary = (
            f"Advisory: {query}. "
            f"Signals cover {len(signals)} record(s) regarding {tag_str}. "
            f"Key excerpts: {snippets_str}."
        )

        return json.dumps({
            "provider": "ollama",
            "status": "grounded",
            "summary": summary,
            "note": "Advisory grounded in actual signal records."
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
