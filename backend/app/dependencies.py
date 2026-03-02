from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import supabase_client
from app.services.billing.subscription import get_subscription_status

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    """
    Validates Supabase JWT and returns the authenticated user object.

    Raises 401 if the token is missing, expired, or invalid.
    Use as a dependency on any protected endpoint.
    """
    token = credentials.credentials
    try:
        user_response = supabase_client.auth.get_user(token)
        if user_response.user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
        return user_response.user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


async def get_authed_supabase(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    """
    Returns a callable that scopes Supabase PostgREST queries to the user's JWT.

    Uses supabase_client.postgrest.auth(token) per-query rather than set_auth()
    on the singleton — safer in async contexts where multiple requests share
    the same client instance (avoids JWT context bleed between concurrent requests).

    Usage in endpoint:
        db = Depends(get_authed_supabase)
        result = db("select", "avatars").execute()

    Or more directly via the returned helper that sets auth per-operation.
    """
    token = credentials.credentials

    class AuthedClient:
        """Thin wrapper that applies the user JWT to each PostgREST operation."""

        def from_(self, table: str):
            return supabase_client.postgrest.auth(token).from_(table)

        def table(self, table: str):
            return supabase_client.postgrest.auth(token).from_(table)

    return AuthedClient()


async def require_active_subscription(user=Depends(get_current_user)):
    """
    FastAPI dependency — raises 402 Payment Required if user has no active subscription.
    Used on POST /chat (web_chat router) and any other gated endpoints.
    Bypassed when STRIPE_SECRET_KEY is not configured (local dev without Stripe).
    """
    from app.config import settings
    if not settings.stripe_secret_key:
        return user  # Stripe not configured — allow chat in dev
    status_val = get_subscription_status(str(user.id))
    if status_val != "active":
        raise HTTPException(
            status_code=402,
            detail="Subscription required. Visit /subscribe to activate.",
        )
    return user
