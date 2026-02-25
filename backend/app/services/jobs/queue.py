"""
BullMQ photo generation queue (enqueue side only — no Worker import here).

Only the FastAPI web process uses this module to add jobs.
The worker process (worker_main.py) uses BullMQ Worker directly.

Anti-pattern avoided: importing BullMQ Worker in the web process (RESEARCH.md anti-patterns).
"""
import logging
from urllib.parse import urlparse
from bullmq import Queue
from app.config import settings

logger = logging.getLogger(__name__)

_photo_queue: Queue | None = None


def get_photo_queue() -> Queue:
    """Return module-level Queue singleton. Lazy init on first call."""
    global _photo_queue
    if _photo_queue is None:
        host = "redis"
        port = 6379
        if settings.redis_url:
            try:
                parsed = urlparse(settings.redis_url)
                host = parsed.hostname or host
                port = parsed.port or port
            except Exception:
                pass
        _photo_queue = Queue(
            "photo_generation",
            {"connection": {"host": host, "port": port}},
        )
    return _photo_queue


async def enqueue_photo_job(
    user_id: str,
    scene_description: str,
    avatar: dict,
    channel: str,
) -> None:
    """
    Enqueue a photo generation job to BullMQ.

    Args:
        user_id: Authenticated user's UUID.
        scene_description: Scene/pose description from LLM send_photo tool call.
        avatar: Full avatar dict (must include gender, nationality, physical_description).
        channel: "web" or "whatsapp" (for delivery routing in processor).
    """
    queue = get_photo_queue()
    await queue.add(
        "generate_photo",
        {
            "user_id": user_id,
            "scene_description": scene_description,
            "avatar": avatar,
            "channel": channel,
        },
        {
            "attempts": 3,
            "backoff": {"type": "exponential", "delay": 2000},  # 2s, 4s, 8s retries
            "removeOnComplete": 100,
            "removeOnFail": 200,
        },
    )
    logger.info(f"Photo job enqueued for user {user_id}, channel={channel}")
