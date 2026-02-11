#!/bin/bash
# Production start script cho FastAPI backend

set -e

# Activate virtual environment if exists
if [ -d "../venv" ]; then
    source ../venv/bin/activate
fi

# Check if gunicorn is installed
if ! command -v gunicorn &> /dev/null; then
    echo "Installing gunicorn..."
    pip install gunicorn
fi

# Start with gunicorn
echo "Starting FastAPI backend with Gunicorn..."
gunicorn backend.main:app \
    --config backend/gunicorn_config.py \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --access-logfile - \
    --error-logfile - \
    --log-level info
