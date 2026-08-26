#!/bin/sh
set -eu

/app/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 &
server_pid=$!

stop_server() {
    kill -TERM "$server_pid" 2>/dev/null || true
    wait "$server_pid" 2>/dev/null || true
}

trap stop_server INT TERM

if ! /app/.venv/bin/python scripts/ingest_samples.py; then
    stop_server
    exit 1
fi

wait "$server_pid"
