#!/bin/bash

# This script is executed by the jetson-automation.service

# --- Configuration ---
GIT_BRANCH="main" # Or your preferred branch
REPO_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )" # Get repo path based on script location
PYTHON_EXEC=$(which python3)
PIP_EXEC=$(which pip3)

echo "--- Starting Auto Execution Sequence ($(date)) ---"
echo "Repository Path: $REPO_PATH"
echo "Current User: $(whoami)"
echo "Python: $PYTHON_EXEC, Pip: $PIP_EXEC"
cd "$REPO_PATH" || { echo "ERROR: Failed to change directory to $REPO_PATH"; exit 1; }

# --- 1. Wait for Internet Connection (Optional - systemd handles initial wait) ---
MAX_WAIT_SECONDS=100
WAIT_INTERVAL=5
ELAPSED_TIME=0
echo "Checking for internet connection (ping 8.8.8.8)..."
while ! ping -c 1 -W 1 8.8.8.8 &> /dev/null; do
    echo "No internet connection detected. Waiting..."
    sleep $WAIT_INTERVAL
    ELAPSED_TIME=$((ELAPSED_TIME + WAIT_INTERVAL))
    if [ $ELAPSED_TIME -ge $MAX_WAIT_SECONDS ]; then
        echo "ERROR: Internet connection timeout after $MAX_WAIT_SECONDS seconds. Skipping Git pull and dependency install."
        # Decide if you should proceed to run.sh or exit
        # Proceeding to run.sh might be desired if offline operation is possible
         echo "Proceeding to execute run.sh with potentially outdated code/dependencies."
         bash run.sh
         exit 0 # Exit successfully even if offline, allowing run.sh to execute
        # Alternatively, exit with error:
        # exit 1
    fi
done
echo "Internet connection established."

# --- 2. Force Pull Latest Code from GitHub ---
echo "Fetching latest code from origin/$GIT_BRANCH..."
# Ensure git commands run as the user owning the directory, in case service runs as root initially
# This might not be necessary if the service User= directive works correctly.
CURRENT_USER=$(whoami)
TARGET_USER=$(stat -c '%U' "$REPO_PATH/.git") # Find owner of .git dir
echo "Running Git commands as user: $CURRENT_USER (target should be $TARGET_USER)"

# Use sudo -u if current user is root but target is different
# Handle potential errors during git operations
if [ "$CURRENT_USER" == "root" ] && [ "$CURRENT_USER" != "$TARGET_USER" ]; then
    echo "Switching to user $TARGET_USER for Git operations."
    SUDO_CMD="sudo -u $TARGET_USER"
else
    SUDO_CMD=""
fi

($SUDO_CMD git fetch --all && \
 $SUDO_CMD git reset --hard origin/$GIT_BRANCH && \
 $SUDO_CMD git clean -fdx) || { echo "ERROR: Git update failed. Proceeding with existing code."; } # Don't exit on failure, maybe repo is okay

echo "Git repository updated to latest origin/$GIT_BRANCH."

# --- 3. Install/Update Project Python Dependencies ---
echo "Checking for project-specific requirements.txt files in src/..."
find src -mindepth 1 -maxdepth 1 -type d | while read -r project_dir; do
    if [ -f "$project_dir/requirements.txt" ]; then
        echo "Found requirements.txt in $project_dir. Installing/updating..."
        # Install dependencies for the user running the service
        $PIP_EXEC install --user -r "$project_dir/requirements.txt"
        if [ $? -ne 0 ]; then
            echo "WARNING: Failed to install dependencies from $project_dir/requirements.txt"
        fi
    fi
done
echo "Finished checking project dependencies."

# --- 4. Execute Main Application Logic ---
echo "Executing run.sh..."
if [ -f "run.sh" ]; then
    # Ensure run.sh is executable
    chmod +x run.sh
    # Execute run.sh
    bash run.sh
else
    echo "ERROR: run.sh not found in $REPO_PATH."
    exit 1
fi

echo "--- Auto Execution Sequence Finished ($(date)) ---"
exit 0 # Ensure systemd knows the script finished successfully