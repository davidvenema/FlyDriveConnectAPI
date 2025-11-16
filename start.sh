#!/bin/bash

# Fail fast
set -e

echo "From start.sh: Starting FastAPI with uvicorn..."

# App Runner's default Python environment often puts installed packages here.
# Source this path to ensure Uvicorn is in the PATH/environment.
source /usr/local/bin/activate || true

# Run using the same python as App Runner's runtime
exec python3 -m uvicorn main:app --host 0.0.0.0 --port 8080
