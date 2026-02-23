from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import supabase_client

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
