import time
import uuid

from app.models import Job, JobStatus
from app.queue import RETRY_QUEUE_KEY, dequeue_job, redis_client, schedule_retry
from app.worker import MAX_RETRIES, process_job


def make_job(db_session, command: str, timeout_seconds: int = 30) -> Job:
    job = Job(command=command, status=JobStatus.PENDING.value, timeout_seconds=timeout_seconds)
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


def test_process_job_schedules_retry_on_failure(db_session, clean_queue):
    job = make_job(db_session, "exit 1")

    process_job(str(job.id), db_session)

    db_session.refresh(job)
    assert job.status == JobStatus.PENDING.value
    assert job.attempts == 1
    assert redis_client.zscore(RETRY_QUEUE_KEY, str(job.id)) is not None


def test_process_job_exhausts_retries(db_session, clean_queue):
    job = make_job(db_session, "exit 1")

    for _ in range(MAX_RETRIES):
        process_job(str(job.id), db_session)
        db_session.refresh(job)

    assert job.status == JobStatus.FAILED.value
    assert job.attempts == MAX_RETRIES
    assert redis_client.zscore(RETRY_QUEUE_KEY, str(job.id)) is None


def test_process_job_timeout(db_session, clean_queue):
    job = make_job(db_session, "sleep 5", timeout_seconds=1)

    started = time.monotonic()
    process_job(str(job.id), db_session)
    elapsed = time.monotonic() - started

    assert elapsed < 3  # should time out around 1s, not run the full 5s
    db_session.refresh(job)
    assert job.status == JobStatus.PENDING.value  # first failure, retry scheduled
    assert job.attempts == 1


def test_promote_ready_retries_only_promotes_past_due(clean_queue):
    past_id = uuid.uuid4()
    future_id = uuid.uuid4()
    schedule_retry(past_id, time.time() - 1)
    schedule_retry(future_id, time.time() + 1000)

    from app.queue import promote_ready_retries
    promoted = promote_ready_retries()

    assert promoted == 1
    assert dequeue_job(timeout=1) == str(past_id)
    assert redis_client.zscore(RETRY_QUEUE_KEY, str(future_id)) is not None