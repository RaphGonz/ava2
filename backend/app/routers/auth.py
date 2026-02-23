from fastapi import APIRouter, HTTPException
from app.database import supabase_client
from app.models.auth import SignupRequest, SigninRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse)
async def signup(body: SignupRequest):
    """
    Create a new user account with email and password.

    IMPORTANT: Requires email confirmation disabled in Supabase Dashboard.
    Authentication > Providers > Email > uncheck 'Confirm email'.
    Otherwise session will be None and no token can be returned.
    """
    try:
        response = supabase_client.auth.sign_up({
            "email": body.email,
            "password": body.password,
        })
        if response.user is None:
            raise HTTPException(status_code=400, detail="Signup failed")
        if response.session is None:
            raise HTTPException(
                status_code=400,
                detail="Email confirmation required — disable it in Supabase Dashboard "
                       "(Authentication > Providers > Email > uncheck 'Confirm email')",
            )
        return TokenResponse(
            access_token=response.session.access_token,
            user_id=str(response.user.id),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/signin", response_model=TokenResponse)
async def signin(body: SigninRequest):
    """Sign in with email and password. Returns JWT access token."""
    try:
        response = supabase_client.auth.sign_in_with_password({
            "email": body.email,
            "password": body.password,
        })
        return TokenResponse(
            access_token=response.session.access_token,
            user_id=str(response.user.id),
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")
