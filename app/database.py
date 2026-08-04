"""Database client helpers.

Step 1 keeps this module intentionally small. Supabase integration is added in
Step 3 after the cloud schema is created.
"""

from app.config import get_settings


def is_database_configured() -> bool:
    """Return whether Supabase connection settings are present."""
    settings = get_settings()
    return bool(settings.supabase_url and settings.supabase_service_role_key)
