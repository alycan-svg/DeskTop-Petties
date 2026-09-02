"""Tests that app resources do not depend on the terminal directory."""

from app.paths import ENV_FILE, INDEX_FILE, PROJECT_ROOT, STATIC_DIR


def test_application_paths_are_absolute_and_exist() -> None:
    assert PROJECT_ROOT.is_absolute()
    assert STATIC_DIR.is_dir()
    assert INDEX_FILE.is_file()
    assert ENV_FILE == PROJECT_ROOT / ".env"
