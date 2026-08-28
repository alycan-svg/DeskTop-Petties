"""Absolute filesystem paths used by the application."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = PROJECT_ROOT / "app" / "static"
INDEX_FILE = STATIC_DIR / "index.html"
ENV_FILE = PROJECT_ROOT / ".env"
