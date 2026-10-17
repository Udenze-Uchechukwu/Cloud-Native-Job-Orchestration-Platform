import time
import uuid

import redis

from app.database import settings

JOB_QUEUE_KEY = "jobs:queue"
RETRY_QUEUE_KEY = "jobs:retry"

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


def schedule_retry(job_id: uuid.UUID, ready_at: float) -> None:
    redis_client.zadd(RETRY_QUEUE_KEY, {str(job_id): ready_at})


def promote_ready_retries() -> int:
    now = time.time()
    ready_ids = redis_client.zrangebyscore(RETRY_QUEUE_KEY, min=0, max=now)
    for job_id in ready_ids:
        redis_client.zrem(RETRY_QUEUE_KEY, job_id)
        redis_client.lpush(JOB_QUEUE_KEY, job_id)
    return len(ready_ids)