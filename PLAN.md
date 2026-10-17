# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

signal-store-and-handoff

## Roadmap

### signal-store-and-handoff — Signal store with relevance-ranked handoff briefing

Status: done

Acceptance:
- POST /api/signals stores a signal with content, tags, workspace, project, and UTC timestamp
- GET /api/signals lists signals with pagination and project filtering
- GET /api/signals/{id} retrieves a single signal
- POST /api/handoff computes a relevance-ranked briefing from stored signals using TF-IDF + temporal decay
- Handoff briefing respects a byte budget and returns ranked, truncated signal excerpts
- All data endpoints reject unauthenticated requests and enforce role-based access
- Frontend dashboard creates signals and generates handoff briefings with loading/error/empty states
- Backend has 12+ meaningful pytest tests covering domain logic, persistence, auth, and API workflows
- Frontend has 3+ vitest tests covering user-visible behavior

Implementation: `backend/app/main.py`, `backend/app/core/config.py`, `backend/app/core/database.py`, `backend/app/core/auth.py`, `backend/app/core/relevance.py`, `backend/app/models/schemas.py`, `backend/app/services/signal_service.py`, `backend/app/api/signals.py`, `backend/app/api/handoff.py`, `backend/app/api/auth.py`, `frontend/src/App.tsx`, `frontend/src/api/client.ts`, `frontend/src/components/AuthProvider.tsx`, `frontend/src/components/Dashboard.tsx`, `frontend/src/components/SignalForm.tsx`, `frontend/src/components/HandoffBriefing.tsx`, `frontend/src/components/HeaderNav.tsx`, `frontend/src/components/LoginPage.tsx`, `frontend/src/types/index.ts`

Tests: `backend/tests/test_relevance.py`, `backend/tests/test_signals.py`, `backend/tests/test_auth.py`, `backend/tests/test_api.py`, `frontend/src/App.test.tsx`

### llm-advisory-summaries — Optional LLM advisory summaries (opt-in)

Status: planned

Acceptance:
- LLM provider adapters for OpenAI-compatible, Anthropic, Gemini, Ollama
- Summaries are labeled advisory and grounded in actual signal records
- Provider errors never fabricate successful responses

### full-keycloak-oidc — Production Keycloak OIDC with SAML brokering

Status: planned

Acceptance:
- OIDC authorization-code login with state, nonce, PKCE, and library-validated tokens
- Keycloak realm import with SAML identity provider brokering
- Production mode refuses demo auth

### signal-import-export — Bulk import and export of signals

Status: planned

Acceptance:
- Import signals from JSON with validation
- Export filtered signal sets as JSON

