#!/bin/bash

# This script defines what applications/processes to run after updates.
# It is executed by autoexec.sh.
# Make sure scripts/commands here are compatible with the user running the service.

echo "--- Starting User Applications ($(date)) ---"
REPO_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PYTHON_EXEC=$(which python3)

# Example: Kill previous instances if necessary (use pkill carefully)
# pkill -f "python3 src/project1/main.py" || true
# pkill -f "bash src/project2/start.sh" || true

# Example: Run a Python script in the background
echo "Starting Project 1..."
$PYTHON_EXEC "$REPO_PATH/src/project1/main.py" &

# Example: Run a shell script in the background
echo "Starting Project 2..."
bash "$REPO_PATH/src/project2/start.sh" &

# Example: Run a simple command
echo "Running a simple command..."
echo "Current date: $(date)" > "$REPO_PATH/last_run.log"

echo "--- User Applications Launched ---"

# If this script needs to keep running (e.g., monitoring children), add 'wait' or a loop.
# Otherwise, it will exit, but the background processes (&) will continue.
# For systemd, it's often better if this script exits once tasks are launched,
# unless it *is* the main long-running process itself.