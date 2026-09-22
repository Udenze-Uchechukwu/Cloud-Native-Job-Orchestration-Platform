import uuid

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Job, JobLog, JobStatus
from app.schemas import JobCreate, JobRead, LogRead

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/jobs", response_model=JobRead, status_code=201)
def create_job(job_in: JobCreate, db: Session = Depends(get_db)):
    job = Job(command=job_in.command, status=JobStatus.PENDING.value)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@app.get("/jobs/{job_id}", response_model=JobRead)
def get_job(job_id: uuid.UUID, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.get("/jobs/{job_id}/logs", response_model=list[LogRead])
def get_job_logs(job_id: uuid.UUID, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return db.query(JobLog).filter(JobLog.job_id == job_id).order_by(JobLog.timestamp).all()
