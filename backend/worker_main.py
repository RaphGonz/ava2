"""
BullMQ Worker entry point.

Run as a separate Docker service:
  CMD: python worker_main.py

This process ONLY runs the BullMQ Worker — it never imports or starts FastAPI.
Concurrency: 3 concurrent image generation jobs (Claude's discretion per CONTEXT.md).

Redis connection: parsed from REDIS_URL env var.
  Default: redis://redis:6379 (Docker Compose service name 'redis')
  Override with REDIS_URL env var for local or cloud Redis.

IMPORTANT (RESEARCH.md Pitfall 5): Use the same connection dict format on both
Queue (enqueue) and Worker (consume) to avoid job serialization mismatch.
"""
import asyncio
import logging
import os
from urllib.parse import urlparse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger("ava.worker")


async def main() -> None:
    # Deferred imports ensure env vars (loaded by app.config) are available
    from bullmq import Worker
    from app.services.jobs.processor import process_photo_job

    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    parsed = urlparse(redis_url)
    host = parsed.hostname or "redis"
    port = parsed.port or 6379

    logger.info(f"BullMQ worker starting — Redis {host}:{port} concurrency=3")

    worker = Worker(
        "photo_generation",
        process_photo_job,
        {
            "connection": {"host": host, "port": port},
            "concurrency": 3,
        },
    )

    logger.info("Worker ready — listening for photo_generation jobs...")
    # Block forever — process killed by Docker stop signal
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
