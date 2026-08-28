"""Lightweight password checks for the shared world prototype."""

from fastapi import HTTPException, status

from app.config import get_settings


def verify_access_password(password: str) -> None:
    """Raise an HTTP error when the shared access password is invalid."""
    expected_password = get_settings().access_password
    if password != expected_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access password.",
        )
