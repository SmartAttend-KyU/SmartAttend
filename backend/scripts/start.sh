#!/bin/sh
set -eu

echo "Applying database migrations..."
alembic upgrade head

if [ "${SEED_DEMO_DATA:-false}" = "true" ]; then
  echo "Loading demo data..."
  python -m scripts.seed_demo
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
