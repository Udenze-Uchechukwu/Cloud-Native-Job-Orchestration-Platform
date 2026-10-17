import time

import structlog

from app.logging_config import configure_logging
from app.queue import promote_ready_retries

log = structlog.get_logger()

POLL_INTERVAL_SECONDS = 1


def main() -> None:
    """Poll the retry set once a second, promoting anything whose backoff elapsed."""
    configure_logging()
    log.info("scheduler_started")
    while True:
        promoted = promote_ready_retries()
        for job_id in promoted:
            log.info("retry_promoted", job_id=job_id)
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
