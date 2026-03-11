import os
import pytest


@pytest.fixture
def unsubscribed_jwt() -> str:
    """
    JWT for a production Supabase user with no active subscription row.
    Set SMOKE_UNSUBSCRIBED_JWT env var before running smoke tests.
    Obtain by: login to production app as a user with no subscription, copy JWT from
    browser DevTools -> Application -> Local Storage -> sb-*-auth-token -> access_token.
    """
    token = os.environ.get("SMOKE_UNSUBSCRIBED_JWT")
    if not token:
        pytest.skip("SMOKE_UNSUBSCRIBED_JWT env var not set — skipping production smoke test")
    return token


@pytest.fixture
def regular_user_jwt() -> str:
    """
    JWT for any production Supabase user without admin role.
    Set SMOKE_REGULAR_USER_JWT env var before running smoke tests.
    """
    token = os.environ.get("SMOKE_REGULAR_USER_JWT")
    if not token:
        pytest.skip("SMOKE_REGULAR_USER_JWT env var not set — skipping admin smoke test")
    return token


@pytest.fixture
def admin_jwt() -> str:
    """
    JWT for the production Supabase user with app_metadata.role == "super-admin".
    Set SMOKE_ADMIN_JWT env var before running admin smoke tests.
    Obtain by: login to production app as the operator (admin) account, copy JWT from
    browser DevTools -> Application -> Local Storage -> sb-*-auth-token -> access_token.
    """
    token = os.environ.get("SMOKE_ADMIN_JWT")
    if not token:
        pytest.skip("SMOKE_ADMIN_JWT env var not set — skipping admin metrics smoke test")
    return token
