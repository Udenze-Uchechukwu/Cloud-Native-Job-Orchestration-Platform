import time

import pytest

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

POLL_INTERVAL = 0.2
POLL_TIMEOUT = 15


def _wait_for_terminal_status(job_id: str) -> dict:
    deadline = time.monotonic() + POLL_TIMEOUT
    while time.monotonic() < deadline:
        job = client.get(f"/jobs/{job_id}").json()
        if job["status"] in ("SUCCEEDED", "FAILED"):
            return job
        time.sleep(POLL_INTERVAL)
    raise TimeoutError(f"job {job_id} did not reach a terminal status in time")


@pytest.mark.e2e
def test_happy_path_end_to_end(running_worker):
    response = client.post("/jobs", json={"command": "echo e2e-marker"})
    job_id = response.json()["id"]

    job = _wait_for_terminal_status(job_id)
    assert job["status"] == "SUCCEEDED"

    logs = client.get(f"/jobs/{job_id}/logs").json()
    assert any("e2e-marker" in log["message"] for log in logs)


@pytest.mark.e2e
def test_retry_end_to_end(running_worker, running_scheduler):
    response = client.post("/jobs", json={"command": "echo attempt-failing && exit 1"})
    job_id = response.json()["id"]

    job = _wait_for_terminal_status(job_id)
    assert job["status"] == "FAILED"
    assert job["attempts"] == 3

    logs = client.get(f"/jobs/{job_id}/logs").json()
    assert len(logs) == 3
    assert {log["attempt"] for log in logs} == {1, 2, 3}