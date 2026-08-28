"""Supabase client creation and database-specific errors."""

from functools import lru_cache
from typing import Any

from app.config import get_settings


class DatabaseConfigurationError(RuntimeError):
    """Raised when the server has no usable Supabase credentials."""


def is_database_configured() -> bool:
    """Return whether Supabase connection settings are present."""
    settings = get_settings()
    return bool(settings.supabase_url and settings.supabase_service_role_key)


@lru_cache
def get_supabase_client() -> Any:
    """Create and cache the server-side Supabase client.

    The service-role key belongs only on this backend. It must never be sent to
    the browser or bundled with the future PyQt6 desktop client.
    """
    settings = get_settings()
    if not is_database_configured():
        raise DatabaseConfigurationError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured."
        )

    # Import lazily so health checks and the explicit 503 configuration response
    # remain available before optional cloud dependencies are installed.
    from supabase import create_client

    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
    )
