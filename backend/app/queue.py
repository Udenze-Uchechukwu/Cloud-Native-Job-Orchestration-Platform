import uuid

import redis

from app.database import settings

JOB_QUEUE_KEY = "jobs:queue"

redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True, socket_timeout=None)


def enqueue_job(job_id: uuid.UUID) -> None:
    redis_client.lpush(JOB_QUEUE_KEY, str(job_id))


def dequeue_job(timeout: int = 0) -> str | None:
    # timeout = 0 for indefinte wait, so brpop should never return None!
    result = redis_client.brpop(JOB_QUEUE_KEY, timeout=timeout)
    if result is None:
        return None
    _, job_id = result
    return job_id
