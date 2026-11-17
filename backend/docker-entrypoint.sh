#!/bin/sh
# Apply database migrations (when a database is configured), then start the API.
set -e
if [ -n "$DATABASE_URL" ] && [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    alembic upgrade head
fi
exec uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --no-access-log
