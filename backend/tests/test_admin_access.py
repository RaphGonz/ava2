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
    """User with app_metadata = {"role": "super_admin"} should be returned without raising."""
    user = MagicMock()
    user.app_metadata = {"role": "super_admin"}
    result = await require_admin(user=user)
    assert result == user


@pytest.mark.asyncio
async def test_require_admin_blocks_non_admin():
    """User with app_metadata = {} (no role) should receive 403."""
    user = MagicMock()
    user.app_metadata = {}
    with pytest.raises(HTTPException) as exc_info:
        await require_admin(user=user)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_admin_blocks_wrong_role():
    """User with app_metadata = {"role": "user"} should receive 403."""
    user = MagicMock()
    user.app_metadata = {"role": "user"}
    with pytest.raises(HTTPException) as exc_info:
        await require_admin(user=user)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_admin_blocks_null_metadata():
    """User with app_metadata = None should receive 403."""
    user = MagicMock()
    user.app_metadata = None
    with pytest.raises(HTTPException) as exc_info:
        await require_admin(user=user)
    assert exc_info.value.status_code == 403
