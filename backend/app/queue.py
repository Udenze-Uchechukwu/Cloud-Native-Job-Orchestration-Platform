import time
import uuid

import redis

from app.database import settings

# Two Redis structures: JOB_QUEUE_KEY is the "ready to run" list the worker
# blocks on; RETRY_QUEUE_KEY is a sorted set of jobs waiting out a backoff
# delay, scored by the Unix timestamp they become ready at. The scheduler
# moves entries from the retry set into the main queue once their time comes.
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
    """Park a job in the retry set until `ready_at` (a time.time() timestamp)."""
    redis_client.zadd(RETRY_QUEUE_KEY, {str(job_id): ready_at})


def clear_retry(job_id: uuid.UUID) -> None:
    """Remove a job from the retry set — called when it's done retrying for good."""
    redis_client.zrem(RETRY_QUEUE_KEY, str(job_id))


def promote_ready_retries() -> list[str]:
    """Move every job whose backoff has elapsed from the retry set to the main
    queue. Returns the ids promoted. Called by the scheduler on a timer."""
    now = time.time()
    ready_ids = redis_client.zrangebyscore(RETRY_QUEUE_KEY, min=0, max=now)
    for job_id in ready_ids:
        redis_client.zrem(RETRY_QUEUE_KEY, job_id)
        redis_client.lpush(JOB_QUEUE_KEY, job_id)
    return ready_ids
