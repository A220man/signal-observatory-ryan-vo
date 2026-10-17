"""Tests for the deterministic TF-IDF + temporal decay relevance engine."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.core.relevance import (
    RelevanceEngine,
    ScoredSignal,
    compute_idf,
    compute_tf,
    temporal_decay,
    tokenize,
)
from app.models.schemas import SignalRead


def _make_signal(
    id: str = "sig-1",
    content: str = "default content",
    tags: list[str] | None = None,
    created_at: datetime | None = None,
    workspace: str = "ws",
    project: str = "proj",
) -> SignalRead:
    return SignalRead(
        id=id,
        workspace=workspace,
        project=project,
        agent_id="agent-1",
        content=content,
        tags=tags or [],
        created_at=created_at or datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        relevance_score=0.0,
    )


# --- Tokenizer ---

def test_tokenize_strips_punctuation_and_lowercases():
    tokens = tokenize("Hello, World! API-Key")
    assert tokens == ["hello", "world", "api", "key"]


def test_tokenize_empty_string():
    assert tokenize("") == []
    assert tokenize("   ") == []


def test_tokenize_removes_numbers_mixed():
    tokens = tokenize("feature-v2.0 released")
    assert tokens == ["feature", "v2", "0", "released"]


# --- TF computation ---

def test_compute_tf_normalizes_by_total():
    tf = compute_tf(["alpha", "beta", "alpha"])
    assert tf["alpha"] == 2 / 3
    assert tf["beta"] == 1 / 3


def test_compute_tf_empty():
    assert compute_tf([]) == {}


# --- IDF computation ---

def test_compute_idf_rare_term_higher():
    doc1 = ["common", "rare"]
    doc2 = ["common", "common"]
    vocab = {"common", "rare"}
    idf = compute_idf(vocab, [doc1, doc2])
    assert idf["rare"] > idf["common"]


def test_compute_idf_empty_corpus():
    assert compute_idf(set(), []) == {}


# --- Temporal decay ---

def test_temporal_decay_at_zero_age():
    assert temporal_decay(0, 7.0) == 1.0


def test_temporal_decay_halves_at_one_half_life():
    assert temporal_decay(7.0, 7.0) == pytest.approx(0.5)


def test_temporal_decay_doubles_at_two_half_lives():
    assert temporal_decay(14.0, 7.0) == pytest.approx(0.25)


def test_temporal_decay_negative_age_clamped_to_one():
    assert temporal_decay(-5.0, 7.0) == 1.0


# --- Engine scoring ---

def test_score_signals_ranks_by_relevance():
    """Signal with matching query terms ranks higher."""
    sig_a = _make_signal("a", "database migration performance tuning")
    sig_b = _make_signal("b", "frontend UI color scheme buttons")
    sig_c = _make_signal("c", "database connection pool settings")

    engine = RelevanceEngine(half_life_days=7.0)
    scored = engine.score_signals("database migration", [sig_a, sig_b, sig_c])

    assert scored[0].signal.id == "a"  # both terms match
    assert scored[1].signal.id == "c"  # "database" matches
    assert scored[2].signal.id == "b"  # no match, score 0


def test_score_signals_zero_match_returns_score_zero():
    sig = _make_signal("a", "completely unrelated content here")
    engine = RelevanceEngine()
    scored = engine.score_signals("kubernetes docker", [sig])
    assert scored[0].final_score == 0.0


def test_score_signals_applies_temporal_decay():
    """Older signal with same content gets lower score."""
    old = _make_signal("old", "database migration tuning",
                       created_at=datetime.now(timezone.utc) - timedelta(days=30))
    new = _make_signal("new", "database migration tuning",
                       created_at=datetime.now(timezone.utc))

    engine = RelevanceEngine(half_life_days=7.0)
    scored = engine.score_signals("database migration", [old, new])
    # Newer should rank higher even with same content
    assert scored[0].signal.id == "new"
    assert scored[0].final_score > scored[1].final_score


def test_build_briefing_respects_budget():
    """Briefing total excerpt bytes must not exceed budget."""
    # Use repeated tokens so query "xxx" matches
    content = " ".join(["xxx"] * 1000)  # ~4000 bytes, exceeds budget of 100
    sig = _make_signal("a", content)
    engine = RelevanceEngine()
    selected, used = engine.build_briefing(
        query="xxx",
        signals=[sig],
        budget_bytes=100,
        max_signals=5,
    )
    assert used <= 100
    assert len(selected) >= 1
    assert len(selected[0].excerpt.encode("utf-8")) <= 100


def test_build_briefing_respects_max_signals():
    signals = [_make_signal(f"s{i}", f"content topic-{i}") for i in range(5)]
    engine = RelevanceEngine()
    selected, _ = engine.build_briefing(
        query="topic",
        signals=signals,
        budget_bytes=50_000,
        max_signals=3,
    )
    assert len(selected) <= 3


def test_build_briefing_filters_by_tags():
    sig_a = _make_signal("a", "important task", tags=["urgent"])
    sig_b = _make_signal("b", "routine task", tags=["normal"])
    engine = RelevanceEngine()
    selected, _ = engine.build_briefing(
        query="task",
        signals=[sig_a, sig_b],
        budget_bytes=50_000,
        max_signals=5,
        include_tags=["urgent"],
    )
    assert len(selected) == 1
    assert selected[0].signal.id == "a"


def test_score_signals_deterministic_ordering():
    """Same inputs produce same ordering across calls."""
    sigs = [
        _make_signal(f"s{i}", f"alpha beta gamma delta {i}") for i in range(10)
    ]
    now = datetime.now(timezone.utc)
    engine = RelevanceEngine()
    r1 = engine.score_signals("alpha gamma", sigs, now=now)
    r2 = engine.score_signals("alpha gamma", sigs, now=now)
    assert [s.signal.id for s in r1] == [s.signal.id for s in r2]