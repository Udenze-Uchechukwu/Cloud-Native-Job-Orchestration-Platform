import subprocess
import sys
import uuid
import os
import signal
import time

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Job, JobLog, JobStatus
from app.queue import clear_retry, dequeue_job, schedule_retry

MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 2


def run_command(command: str, timeout_seconds: int) -> tuple[int, str, str]:
    proc = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout_seconds)
        return proc.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        stdout, stderr = proc.communicate()
        return -1, stdout, stderr or f"job timed out after {timeout_seconds}s"


def process_job(job_id: str, db: Session) -> None:
    job = db.get(Job, uuid.UUID(job_id))
    if job is None:
        print(f"job {job_id} not found, skipping", file=sys.stderr)
        return

    job.status = JobStatus.RUNNING.value
    db.commit()

    try:
        returncode, stdout, stderr = run_command(job.command, job.timeout_seconds)
    except Exception as exc:
        returncode, stdout, stderr = -1, "", f"worker error: {exc}"

    if stdout:
        db.add(JobLog(job_id=job.id, message=stdout))
    if stderr:
        db.add(JobLog(job_id=job.id, message=stderr))

    job.attempts += 1

    if returncode == 0:
        job.status = JobStatus.SUCCEEDED.value
        db.commit()
        return

    if job.attempts < MAX_RETRIES:
        job.status = JobStatus.PENDING.value
        db.commit()
        backoff = BASE_BACKOFF_SECONDS * (2 ** (job.attempts - 1))
        schedule_retry(job.id, time.time() + backoff)
    else:
        clear_retry(job.id)
        job.status = JobStatus.FAILED.value
        db.commit()


def main() -> None:
    print("worker started, waiting for jobs...")
    while True:
        job_id = dequeue_job()
        if job_id is None:
            continue
        db = SessionLocal()
        try:
            process_job(job_id, db)
        finally:
            db.close()


if __name__ == "__main__":
    main()
