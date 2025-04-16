#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
# Attempt to get the user who invoked sudo, default to 'ubuntu' if not found
if [ -n "$SUDO_USER" ]; then
    TARGET_USER="$SUDO_USER"
else
    # If not run via sudo or SUDO_USER is not set, try logname, else default
    TARGET_USER=$(logname 2>/dev/null || echo "ubuntu")
    echo "Warning: Could not determine user who invoked sudo reliably. Assuming '$TARGET_USER'."
    echo "If this is incorrect, please edit this script and the .service files."
    # Add a small delay for the user to potentially see this warning
    sleep 3
fi
TARGET_USER_HOME=$(eval echo ~$TARGET_USER)
REPO_PATH=$(pwd) # Assumes script is run from the repo root
REPO_NAME=$(basename "$REPO_PATH")
SERVICE_NAME="jetson-automation"
WEBUI_SERVICE_NAME="jetson-webui"
PYTHON_EXEC=$(which python3) # Use system python3

echo "--- Starting Jetson Automation Setup ---"
echo "User: $TARGET_USER"
echo "User Home: $TARGET_USER_HOME"
echo "Repository Path: $REPO_PATH"
echo "Python Executable: $PYTHON_EXEC"

# --- Check if running as root ---
if [ "$EUID" -ne 0 ]; then
  echo "ERROR: Please run this script using sudo."
  exit 1
fi

# --- Update Package List ---
echo "Updating apt package list..."
apt-get update

# --- Install Core Dependencies ---
echo "Installing core dependencies (git, python3, pip, venv, curl)..."
apt-get install -y git python3 python3-pip python3-venv curl

# --- Install Web UI & System Stats Dependencies ---
echo "Installing web UI dependencies (flask, psutil)..."
apt-get install -y python3-flask python3-psutil
# Alternatively, use pip (might get newer versions):
# pip3 install Flask psutil

# --- Install Global APT Requirements (Optional) ---
if [ -f "apt_requirements.txt" ]; then
    echo "Installing global apt requirements from apt_requirements.txt..."
    # Filter out comments and empty lines
    grep -v '^#' apt_requirements.txt | grep -v '^$' | xargs sudo apt-get install -y
else
    echo "No global apt_requirements.txt found, skipping."
fi

# --- Install Global Python Requirements (Optional) ---
# We install this for the TARGET_USER, not root
if [ -f "requirements.txt" ]; then
    echo "Installing global Python requirements from requirements.txt for user $TARGET_USER..."
    sudo -u "$TARGET_USER" $PYTHON_EXEC -m pip install --user -r requirements.txt
else
    echo "No global requirements.txt found, skipping."
fi


# --- Create Systemd Service for Auto Execution ---
echo "Creating systemd service file: /etc/systemd/system/${SERVICE_NAME}.service"
cat << EOF > /etc/systemd/system/${SERVICE_NAME}.service
[Unit]
Description=Jetson Automation Service (Git Pull, Dependencies, Run)
After=network-online.target
Wants=network-online.target

[Service]
User=$TARGET_USER
Group=$(id -gn $TARGET_USER)
WorkingDirectory=$REPO_PATH
ExecStart=/bin/bash $REPO_PATH/autoexec.sh
Restart=on-failure
RestartSec=10
# Add user's local bin to PATH for pip installed packages
Environment="PATH=/usr/bin:/usr/local/bin:$TARGET_USER_HOME/.local/bin"
StandardOutput=append:/var/log/${SERVICE_NAME}.log
StandardError=append:/var/log/${SERVICE_NAME}.log

[Install]
WantedBy=multi-user.target
EOF

# --- Create Systemd Service for Web UI ---
echo "Creating systemd service file: /etc/systemd/system/${WEBUI_SERVICE_NAME}.service"
# Ensure web directory exists
mkdir -p "$REPO_PATH/web"
cat << EOF > /etc/systemd/system/${WEBUI_SERVICE_NAME}.service
[Unit]
Description=Jetson Web UI Service
After=network-online.target ${SERVICE_NAME}.service
Wants=network-online.target

[Service]
User=$TARGET_USER
Group=$(id -gn $TARGET_USER)
WorkingDirectory=$REPO_PATH/web
# Make sure Flask uses the correct Python and handles PATH
ExecStart=$PYTHON_EXEC $REPO_PATH/web/app.py
Restart=always
RestartSec=10
Environment="PATH=/usr/bin:/usr/local/bin:$TARGET_USER_HOME/.local/bin"
Environment="FLASK_APP=app.py"
# Ensure Flask runs on 0.0.0.0 to be accessible network-wide
Environment="FLASK_RUN_HOST=0.0.0.0"
StandardOutput=append:/var/log/${WEBUI_SERVICE_NAME}.log
StandardError=append:/var/log/${WEBUI_SERVICE_NAME}.log


[Install]
WantedBy=multi-user.target
EOF

# Create log files and set permissions
echo "Creating log files..."
touch /var/log/${SERVICE_NAME}.log
chown $TARGET_USER:$(id -gn $TARGET_USER) /var/log/${SERVICE_NAME}.log
touch /var/log/${WEBUI_SERVICE_NAME}.log
chown $TARGET_USER:$(id -gn $TARGET_USER) /var/log/${WEBUI_SERVICE_NAME}.log


# --- Configure Sudoers for Passwordless Web UI Actions ---
echo "Configuring sudoers for passwordless actions..."
SUDOERS_FILE="/etc/sudoers.d/99-jetson-webui"
# Create the sudoers file with restrictive permissions
echo "# Allows user $TARGET_USER to run specific commands without password for WebUI" > $SUDOERS_FILE
echo "$TARGET_USER ALL=(ALL) NOPASSWD: /sbin/shutdown -r now" >> $SUDOERS_FILE
echo "$TARGET_USER ALL=(ALL) NOPASSWD: /sbin/shutdown -h now" >> $SUDOERS_FILE
# Allow restarting the automation service
echo "$TARGET_USER ALL=(ALL) NOPASSWD: /bin/systemctl restart ${SERVICE_NAME}.service" >> $SUDOERS_FILE
# Set correct permissions for the sudoers file
chmod 0440 $SUDOERS_FILE
echo "Sudoers configured in $SUDOERS_FILE"


# --- Enable and Start Services ---
echo "Reloading systemd daemon, enabling and starting services..."
systemctl daemon-reload
systemctl enable ${SERVICE_NAME}.service
systemctl enable ${WEBUI_SERVICE_NAME}.service

# Start the main automation first, then the web UI
systemctl restart ${SERVICE_NAME}.service || echo "Warning: Failed to start ${SERVICE_NAME}. Check logs: journalctl -u ${SERVICE_NAME} and /var/log/${SERVICE_NAME}.log"
# Give it a moment before starting web ui, though service dependency should handle this
sleep 5
systemctl restart ${WEBUI_SERVICE_NAME}.service || echo "Warning: Failed to start ${WEBUI_SERVICE_NAME}. Check logs: journalctl -u ${WEBUI_SERVICE_NAME} and /var/log/${WEBUI_SERVICE_NAME}.log"

echo "--- Setup Complete ---"
echo "Automation service '$SERVICE_NAME' is running."
echo "Web UI service '$WEBUI_SERVICE_NAME' is running."
echo "Access the web UI at http://<JETSON_NANO_IP>:5000"
echo "Logs:"
echo "  Automation: /var/log/${SERVICE_NAME}.log"
echo "  Web UI: /var/log/${WEBUI_SERVICE_NAME}.log"
echo "  Systemd (Automation): journalctl -u ${SERVICE_NAME}"
echo "  Systemd (Web UI): journalctl -u ${WEBUI_SERVICE_NAME}"
echo "Reboot the Jetson Nano to ensure services start correctly on boot."