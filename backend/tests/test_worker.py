import uuid

from app.models import Job, JobLog, JobStatus
from app.queue import dequeue_job, enqueue_job
from app.worker import process_job


def test_process_job_success(db_session):
    job = Job(command="echo hello", status=JobStatus.PENDING.value)
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    process_job(str(job.id), db_session)

    db_session.refresh(job)
    assert job.status == JobStatus.SUCCEEDED.value

    logs = db_session.query(JobLog).filter(JobLog.job_id == job.id).all()
    assert any("hello" in log.message for log in logs)


def test_process_job_failure(db_session):
    job = Job(command="exit 1", status=JobStatus.PENDING.value)
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    process_job(str(job.id), db_session)

    db_session.refresh(job)
    assert job.status == JobStatus.FAILED.value


def test_process_job_missing_job(db_session):
    missing_id = str(uuid.uuid4())
    process_job(missing_id, db_session)  # should not raise


def test_enqueue_dequeue_roundtrip(clean_queue):
    job_id = uuid.uuid4()
    enqueue_job(job_id)
    result = dequeue_job(timeout=1)
    assert result == str(job_id)


def test_create_job_enqueues(client, clean_queue):
    response = client.post("/jobs", json={"command": "echo hi"})
    job_id = response.json()["id"]

    queued_id = dequeue_job(timeout=1)
    assert queued_id == job_id