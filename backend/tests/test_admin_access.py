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
async def test_require_admin_allows_super_admin():
    """User with is_super_admin=True should be returned without raising."""
    user = MagicMock()
    user.is_super_admin = True
    result = await require_admin(user=user)
    assert result == user


@pytest.mark.asyncio
async def test_require_admin_blocks_non_admin():
    """User with is_super_admin=False should receive 403."""
    user = MagicMock()
    user.is_super_admin = False
    with pytest.raises(HTTPException) as exc_info:
        await require_admin(user=user)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_admin_blocks_missing_flag():
    """User with no is_super_admin attribute should receive 403 (defaults to False)."""
    user = MagicMock(spec=[])  # spec=[] means no attributes — getattr returns default
    with pytest.raises(HTTPException) as exc_info:
        await require_admin(user=user)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_admin_blocks_none_flag():
    """User with is_super_admin=None should receive 403."""
    user = MagicMock()
    user.is_super_admin = None
    with pytest.raises(HTTPException) as exc_info:
        await require_admin(user=user)
    assert exc_info.value.status_code == 403
