"""Application configuration with demo-mode security guard."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings. Demo mode is local-only and refused in production."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # --- Core ---
    app_env: str = "dev"  # dev | prod | demo
    database_url: str = "sqlite+aiosqlite:///./signal_observatory.db"
    db_path: str = "./signal_observatory.db"

    # --- Demo auth (local-only, never production) ---
    demo_auth_secret: str = "dev-only-secret-change-me"

    # --- Keycloak OIDC (production; planned milestone) ---
    keycloak_server_url: str = ""
    keycloak_realm: str = ""
    keycloak_client_id: str = ""
    keycloak_client_secret: str = ""
    keycloak_redirect_uri: str = "http://localhost:3000/auth/callback"

    # --- LLM (optional, advisory; planned milestone) ---
    llm_api_key: str = ""
    llm_provider: str = "openai-compatible"
    llm_model: str = ""
    llm_base_url: str = ""
    llm_timeout_seconds: int = 15

    # --- Relevance engine ---
    relevance_half_life_days: float = 7.0


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings. Refuse demo mode in production."""
    s = Settings()
    if s.app_env == "prod" and not s.keycloak_server_url:
        # Production requires Keycloak OIDC; demo auth is a local-only feature.
        raise RuntimeError(
            "Production mode (app_env=prod) requires keycloak_server_url. "
            "Local demo mode is available with app_env=dev or app_env=demo."
        )
    if s.app_env == "demo" and os.getenv("HOSTNAME", ""):
        raise RuntimeError(
            "Demo mode is local-only and refuses to start in containerized/production contexts."
        )
    return s