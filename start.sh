#!/bin/bash

# Explicitly set the path where pip installed the packages.
# For Python 3.11, this is the most common location in App Runner's base image.
export PYTHONPATH=$PYTHONPATH:/usr/local/lib/python3.11/site-packages

echo "From start.sh: Starting FastAPI with uvicorn..."

# Execute the application start command
exec python3 -m uvicorn main:app --host 0.0.0.0 --port 8080
