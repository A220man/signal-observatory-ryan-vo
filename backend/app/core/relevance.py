"""Deterministic TF-IDF + temporal decay relevance engine for agent memory signals.

This engine scores stored signals against a query (session context) using
TF-IDF term weighting and applies recency-based temporal decay. It is
fully offline and produces deterministic results.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.models.schemas import SignalRead

# Word tokenizer: lowercase, alphanumeric sequences.
_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric tokens.

    Deterministic: same input always yields same tokens.
    """
    if not text:
        return []
    return _TOKEN_RE.findall(text.lower())


def compute_idf(vocab: set[str], document_tokens: list[list[str]]) -> dict[str, float]:
    """Compute inverse document frequency (smoothed).

    idf[t] = ln((N + 1) / (df[t] + 1)) + 1

    This avoids zero-idf for unseen terms and is bounded.
    """
    N = len(document_tokens)
    if N == 0:
        return {}
    df: dict[str, int] = field(default_factory=dict)  # placeholder, replaced below
    df = {}
    for tokens in document_tokens:
        seen = set(tokens)
        for t in seen:
            df[t] = df.get(t, 0) + 1
    idf: dict[str, float] = {}
    for t in vocab:
        idf[t] = math.log((N + 1) / (df.get(t, 0) + 1)) + 1.0
    return idf


def compute_tf(tokens: list[str]) -> dict[str, float]:
    """Compute term frequency (count-based)."""
    counts: dict[str, int] = {}
    for t in tokens:
        counts[t] = counts.get(t, 0) + 1
    total = len(tokens)
    if total == 0:
        return {}
    return {t: c / total for t, c in counts.items()}


def temporal_decay(age_days: float, half_life_days: float) -> float:
    """Exponential temporal decay.

    score *= 2^(-age_days / half_life_days)

    A signal exactly half_life_days old retains 50% of its relevance.
    """
    if age_days <= 0:
        return 1.0
    if half_life_days <= 0:
        return 1.0
    return math.pow(0.5, age_days / half_life_days)


@dataclass
class ScoredSignal:
    """A signal with its computed relevance score."""

    signal: SignalRead
    raw_tfidf: float
    decay_factor: float
    final_score: float
    matched_terms: list[str] = field(default_factory=list)
    excerpt: str | None = None


@dataclass
class RelevanceEngine:
    """Deterministic TF-IDF + temporal decay relevance engine."""

    half_life_days: float = 7.0

    def score_signals(
        self,
        query: str,
        signals: list[SignalRead],
        now: datetime | None = None,
        half_life_days: float | None = None,
    ) -> list[ScoredSignal]:
        """Score a list of signals against a query.

        Returns signals sorted by final_score descending. Ties break by
        recency (newer first) for deterministic ordering.
        """
        hl = half_life_days if half_life_days is not None else self.half_life_days
        current = now or datetime.now(timezone.utc)

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        # Build corpus for IDF
        signal_tokens = [tokenize(s.content) for s in signals]
        vocab: set[str] = set()
        for tokens in signal_tokens:
            vocab.update(tokens)
        for t in query_tokens:
            vocab.add(t)

        idf = compute_idf(vocab, signal_tokens)

        scored: list[ScoredSignal] = []
        for signal, tokens in zip(signals, signal_tokens):
            tf = compute_tf(tokens)
            tfidf = {t: tf.get(t, 0.0) * idf.get(t, 0.0) for t in query_tokens}
            raw = sum(tfidf.values())
            matched = [t for t in query_tokens if tf.get(t, 0.0) > 0]

            age_days = (current - signal.created_at).total_seconds() / 86400.0
            decay = temporal_decay(age_days, hl)

            final = raw * decay if raw > 0 else 0.0

            scored.append(
                ScoredSignal(
                    signal=signal,
                    raw_tfidf=raw,
                    decay_factor=decay,
                    final_score=final,
                    matched_terms=matched,
                )
            )

        # Sort by final_score desc, then by created_at desc for determinism
        scored.sort(key=lambda s: (-s.final_score, -s.signal.created_at.timestamp()))
        return scored

    def build_briefing(
        self,
        query: str,
        signals: list[SignalRead],
        budget_bytes: int,
        max_signals: int,
        now: datetime | None = None,
        half_life_days: float | None = None,
        include_tags: list[str] | None = None,
    ) -> tuple[list[ScoredSignal], int]:
        """Build a bounded briefing from scored signals.

        Returns (selected_signals, total_bytes_used). Stops when budget or
        max_signals is reached.
        """
        # Filter by tags if specified
        if include_tags:
            tag_set = set(t.lower() for t in include_tags)
            signals = [
                s for s in signals
                if tag_set.intersection(set(t.lower() for t in s.tags))
            ]

        scored = self.score_signals(query, signals, now=now, half_life_days=half_life_days)

        selected: list[ScoredSignal] = []
        used = 0
        for s in scored[:max_signals]:
            # Skip signals with zero relevance — no query term overlap
            if s.final_score <= 0.0:
                continue
            remaining = budget_bytes - used
            excerpt = self._make_excerpt(s.signal.content, remaining)
            if not excerpt:
                break
            s.excerpt = excerpt
            selected.append(s)
            used += len(excerpt.encode("utf-8"))
            if used >= budget_bytes:
                break

        return selected, used

    @staticmethod
    def _make_excerpt(content: str, remaining_budget: int) -> str | None:
        """Extract an excerpt of content within the remaining budget."""
        if remaining_budget <= 0:
            return None
        encoded = content.encode("utf-8")
        if len(encoded) <= remaining_budget:
            return content
        # Truncate within budget, breaking at a word boundary if possible
        truncated = encoded[:remaining_budget].decode("utf-8", errors="ignore")
        # Try to break at last whitespace
        last_space = max(truncated.rfind(" "), truncated.rfind("\n"))
        if last_space > 0:
            truncated = truncated[:last_space]
        return truncated if truncated.strip() else None