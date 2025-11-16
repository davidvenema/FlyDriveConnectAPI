#!/bin/bash

# The full path to the site-packages directory must be known and exported
# as a custom environment variable named SITE_PACKAGES_DIR in your App Runner config.
# If you cannot set a variable in App Runner, you can try setting the path manually
# after checking the build logs.

# This line uses the SITE_PACKAGES_DIR variable we will set in the App Runner service configuration
export PYTHONPATH=$PYTHONPATH:$SITE_PACKAGES_DIR

echo "From start.sh UPDATED: Starting FastAPI with uvicorn..."

exec python3 -m uvicorn main:app --host 0.0.0.0 --port 8080
