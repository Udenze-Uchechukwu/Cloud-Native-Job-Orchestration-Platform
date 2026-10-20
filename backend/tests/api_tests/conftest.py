import subprocess
import sys

import pytest


def _start(module: str) -> subprocess.Popen:
    return subprocess.Popen([sys.executable, "-m", module])


def _stop(proc: subprocess.Popen) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


@pytest.fixture()
def running_worker():
    proc = _start("app.worker")
    yield
    _stop(proc)


@pytest.fixture()
def running_scheduler():
    proc = _start("app.scheduler")
    yield
    _stop(proc)