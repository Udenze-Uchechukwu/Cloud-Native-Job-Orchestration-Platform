#!/usr/bin/env bash
# Spins up an isolated, disposable Postgres+Redis (different ports from the
# dev stack so this can run even while dev containers/worker/scheduler are
# live), runs the full test suite - including end-to-end tests, which are
# excluded from a plain `pytest` run by default - then tears everything down
# regardless of whether the tests passed.
set -e

# anchored to this script's own location, not the shell's cwd at call time -
# the compose file still needs to resolve correctly from inside cleanup(),
# which runs after `cd backend` below has already changed the working directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE="docker compose -f $SCRIPT_DIR/docker-compose.test.yml -p jobplatform-test"

cleanup() {
  $COMPOSE down -v
}
trap cleanup EXIT

$COMPOSE up -d --wait

export DATABASE_URL="postgresql+psycopg://jobplatform:jobplatform@localhost:5433/jobplatform"
export REDIS_URL="redis://localhost:6380/0"

cd "$SCRIPT_DIR/backend"
.venv/bin/alembic upgrade head

# capture pytest's real exit code rather than letting `set -e` kill the
# script before `trap cleanup` gets a chance to tear the stack down
set +e
.venv/bin/pytest -o addopts=""
TEST_EXIT_CODE=$?
set -e

exit $TEST_EXIT_CODE
