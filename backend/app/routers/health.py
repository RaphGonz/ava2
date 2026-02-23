from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Health check endpoint — returns ok if the server is running."""
    return {"status": "ok"}
