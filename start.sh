#!/bin/bash

echo "From start.sh: Attempting direct execution of Uvicorn script..."

# We are bypassing 'python3 -m uvicorn' and calling the Uvicorn executable directly.
# This executable should be located in the system's PATH if the build succeeded.
# If /usr/local/bin/ is in the PATH, we just use 'uvicorn'.
exec uvicorn main:app --host 0.0.0.0 --port 8080
