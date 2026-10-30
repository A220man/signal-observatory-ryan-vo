# Changelog

## 1.2.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.1.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.0.0 — 2026-10-17

### Added
- Signal storage: create, read, update, delete memory signals with workspace/project/tags metadata, UTC timestamps, and audit log.
- Signal listing with pagination (page/per_page), workspace/project/tag filtering.
- Handoff briefing endpoint: deterministic TF-IDF + temporal decay relevance scoring engine that ranks stored signals by relevance to a session context query, with budget-bounded excerpt truncation.
- Demo-mode JWT authentication with viewer/operator/admin role hierarchy; unauthenticated rejection and role-based access control on all endpoints.
- Frontend React + TypeScript + Vite dashboard: signal creation, listing, search, **signal detail view with inline editing**, and handoff briefing with loading/error/empty states.
- Docker support: backend and frontend Dockerfiles with nonroot users, healthchecks, and .dockerignore files.
- Docker Compose with Keycloak for production OIDC (demo mode available for local development).
- CI workflow: backend pytest, frontend build/test, Docker image builds.
- README with install/run/test steps, architecture diagram, API reference, auth documentation, and AI/ML evaluation section.
- AI/ML evaluation: deterministic relevance scoring with reproducible test corpus.

## 1.0.1 — 2026-10-23

### Added
- Signal detail view (`/signals/:id`) with full signal content display, metadata (workspace, project, agent, timestamps, relevance score, tags), and inline editing for operators/admins.
- Dashboard links signal content to detail view for navigation.
- Backend update/delete endpoints now fully exercised through frontend UI.