#!/bin/bash
set -e

echo "From start.sh: Activating venv and Starting uvicorn..."

# App Runner sets WORKDIR to /app//, but be explicit:
cd /app

# Activate the virtual environment that we create in the build step
source .venv/bin/activate

# Run uvicorn from the venv
exec uvicorn main:app --host 0.0.0.0 --port 8080
