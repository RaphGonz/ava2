"""
Smoke tests: paywall contract (SC-5) and admin access control (ADMN-03).
These tests hit the PRODUCTION server at https://avasecret.org.
Prerequisites:
  - SMOKE_UNSUBSCRIBED_JWT: JWT from a prod user with no subscription row in DB
  - SMOKE_REGULAR_USER_JWT: JWT from a prod user without super-admin app_metadata
Run: cd backend && python -m pytest tests/test_smoke_paywall.py -x -v
"""
import pytest
import httpx

PROD_BASE = "https://avasecret.org"


@pytest.mark.asyncio
async def test_unauthed_chat_returns_401():
    """No credentials -> 401 (bearer scheme enforcement)."""
    async with httpx.AsyncClient(base_url=PROD_BASE, timeout=10.0) as client:
        r = await client.post("/chat", json={"text": "hello"})
    assert r.status_code == 401, f"Expected 401, got {r.status_code}: {r.text}"


@pytest.mark.asyncio
async def test_unsubscribed_chat_returns_402(unsubscribed_jwt: str):
    """
    Active Supabase user with no subscription row -> 402 Payment Required.
    Confirms STRIPE_SECRET_KEY is set on production (dev bypass not active).
    """
    async with httpx.AsyncClient(
        base_url=PROD_BASE,
        headers={"Authorization": f"Bearer {unsubscribed_jwt}"},
        timeout=10.0,
    ) as client:
        r = await client.post("/chat", json={"text": "hello"})
    assert r.status_code == 402, (
        f"Expected 402, got {r.status_code}: {r.text}\n"
        "If 200: STRIPE_SECRET_KEY may be missing from production .env — check immediately."
    )
    data = r.json()
    assert "Subscription required" in data.get("detail", ""), (
        f"Expected 'Subscription required' in detail, got: {data}"
    )


@pytest.mark.asyncio
async def test_non_admin_gets_403(regular_user_jwt: str):
    """
    Regular (non-admin) user hitting /admin/metrics -> 403 Forbidden.
    Confirms require_admin dependency is active in production.
    """
    async with httpx.AsyncClient(
        base_url=PROD_BASE,
        headers={"Authorization": f"Bearer {regular_user_jwt}"},
        timeout=10.0,
    ) as client:
        r = await client.get("/admin/metrics")
    assert r.status_code == 403, (
        f"Expected 403, got {r.status_code}: {r.text}\n"
        "If 200: admin route is unprotected in production — critical security issue."
    )
