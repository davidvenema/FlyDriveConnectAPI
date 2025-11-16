#!/bin/bash

# Fail fast
set -e

echo "From start.sh: Starting FastAPI with uvicorn..."

# Run using the same python as App Runner's runtime
exec python3 -m uvicorn main:app --host 0.0.0.0 --port 8080
