import time

from app.queue import promote_ready_retries

POLL_INTERVAL_SECONDS = 1


def main() -> None:
    print("scheduler started, watching for ready retries...")
    while True:
        promoted = promote_ready_retries()
        if promoted:
            print(f"promoted {promoted} job(s) to the main queue")
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
