"""
Smoke test: /admin/metrics returns 200 with real (non-empty) metric data (ADMN-01).
Hits the PRODUCTION server at https://avasecret.org.
Prerequisites:
  - SMOKE_ADMIN_JWT: JWT from the production operator account with app_metadata.role == "super-admin"
    Obtain: log in as operator, copy access_token from DevTools -> Application ->
    Local Storage -> sb-*-auth-token -> access_token
Run: cd backend && SMOKE_ADMIN_JWT="<jwt>" python -m pytest tests/test_smoke_admin.py -x -v
"""
import pytest
import httpx

PROD_BASE = "https://avasecret.org"

EXPECTED_METRIC_KEYS = [
    "active_users_7d",
    "messages_sent",
    "photos_generated",
    "active_subscriptions",
    "new_signups",
]


@pytest.mark.asyncio
async def test_admin_metrics_returns_data(admin_jwt: str):
    """
    Admin JWT -> GET /admin/metrics returns 200 with all 5 metric keys present
    and at least one metric has a value > 0 (confirming real data, not zeros).
    """
    async with httpx.AsyncClient(
        base_url=PROD_BASE,
        headers={"Authorization": f"Bearer {admin_jwt}"},
        timeout=10.0,
    ) as client:
        r = await client.get("/admin/metrics")

    assert r.status_code == 200, (
        f"Expected 200, got {r.status_code}: {r.text}\n"
        "If 403: verify operator account has app_metadata.role == 'super-admin' (with hyphen) in Supabase Dashboard."
    )

    data = r.json()
    missing_keys = [k for k in EXPECTED_METRIC_KEYS if k not in data]
    assert not missing_keys, (
        f"Response missing expected metric keys: {missing_keys}\n"
        f"Got: {list(data.keys())}"
    )

    non_zero = [k for k in EXPECTED_METRIC_KEYS if data.get(k, 0) > 0]
    assert non_zero, (
        f"All 5 metrics are zero — production may have no data yet, or metrics query is broken.\n"
        f"Values: { {k: data.get(k) for k in EXPECTED_METRIC_KEYS} }"
    )
