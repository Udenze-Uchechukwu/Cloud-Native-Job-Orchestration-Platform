import sys

import structlog


def configure_logging() -> None:
    """Configure structlog to emit one JSON object per line to stdout.

    Called once per process (API at import time, worker/scheduler at the start
    of their main() loops) — not per request/job.
    """
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )
