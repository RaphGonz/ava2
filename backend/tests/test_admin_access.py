"""
Tests for require_admin FastAPI dependency.

Tests run without a live DB or Supabase connection — all user objects are mocked.
Run from the backend/ directory: python -m pytest tests/test_admin_access.py -x -q
"""
import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException

from app.routers.admin import require_admin


@pytest.mark.asyncio
async def test_require_admin_allows_admin_true():
    """User with user_metadata = {"is_admin": True} should be returned without raising."""
    user = MagicMock()
    user.user_metadata = {"is_admin": True}
    result = await require_admin(user=user)
    assert result == user


@pytest.mark.asyncio
async def test_require_admin_blocks_non_admin():
    """User with empty user_metadata (no is_admin key) should receive 403."""
    user = MagicMock()
    user.user_metadata = {}
    with pytest.raises(HTTPException) as exc_info:
        await require_admin(user=user)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_admin_blocks_admin_false():
    """User with user_metadata = {"is_admin": False} should receive 403."""
    user = MagicMock()
    user.user_metadata = {"is_admin": False}
    with pytest.raises(HTTPException) as exc_info:
        await require_admin(user=user)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_admin_handles_null_metadata():
    """User with user_metadata = None should receive 403 (None handled via `or {}`)."""
    user = MagicMock()
    user.user_metadata = None
    with pytest.raises(HTTPException) as exc_info:
        await require_admin(user=user)
    assert exc_info.value.status_code == 403
