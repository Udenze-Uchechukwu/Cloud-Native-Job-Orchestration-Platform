import sys
import subprocess
import uuid

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Job, JobLog, JobStatus
from app.queue import dequeue_job


def process_job(job_id: str, db: Session) -> None:
    job = db.get(Job, uuid.UUID(job_id))
    if job is None:
        print(f"job {job_id} not found, skipping", file=sys.stderr)
        return

    job.status = JobStatus.RUNNING.value
    db.commit()

    try:
        result = subprocess.run(
            job.command, shell=True, capture_output=True, text=True
        )
        if result.stdout:
            db.add(JobLog(job_id=job.id, message=result.stdout))
        if result.stderr:
            db.add(JobLog(job_id=job.id, message=result.stderr))
        job.status = (
            JobStatus.SUCCEEDED.value if result.returncode == 0 else JobStatus.FAILED.value
        )
    except Exception as exc:
        db.add(JobLog(job_id=job.id, message=f"worker error: {exc}"))
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