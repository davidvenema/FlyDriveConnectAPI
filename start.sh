#!/bin/bash

echo "From start.sh: Setting PYTHONPATH and executing uvicorn module."

# Explicitly add the site-packages directory to PYTHONPATH where the 'uvicorn' module resides.
# This bypasses any system PATH issues.
export PYTHONPATH="/usr/local/lib/python3.11/site-packages:$PYTHONPATH"

# Run uvicorn using the python module directly, which should now be discoverable.
# We remove 'exec' to ensure the shell handles the script fully before starting the process.
python3 -m uvicorn main:app --host 0.0.0.0 --port 8080
