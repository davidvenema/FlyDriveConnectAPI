#!/bin/bash

echo "From start.sh: Attempting final PATH setting and execution."

# 1. Add the site-packages directory (for modules, from previous failed attempt)
export PYTHONPATH="/usr/local/lib/python3.11/site-packages:$PYTHONPATH"

# 2. Add the /usr/local/bin directory (where Python executables usually land)
export PATH="/usr/local/bin:$PATH"

# 3. Use 'python3 -m uvicorn' again, as the Python module is the primary way.
# Now that PATH and PYTHONPATH are explicitly set, this should resolve the module.
exec python3 -m uvicorn main:app --host 0.0.0.0 --port 8080
