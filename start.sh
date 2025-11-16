#!/bin/bash

# CONFIRMED INSTALLATION PATH from the Build Logs
# This line ensures the installed packages are available to the runtime environment.
export PYTHONPATH="/usr/local/lib/python3.11/site-packages:$PYTHONPATH"

echo "From start.sh: Launching Uvicorn with final pathing fix."

# Use 'exec' to replace the current shell with the python process, 
# which passes the environment variables correctly.
exec python3 -m uvicorn main:app --host 0.0.0.0 --port 8080
