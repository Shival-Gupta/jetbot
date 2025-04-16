#!/bin/bash

# Change to the repository directory
cd "$(dirname "$0")"

# Ensure log file is writable
sudo touch /var/log/automation.log
sudo chown jetson:jetson /var/log/automation.log

# Install apt packages if apt_requirements.txt exists
if [ -f apt_requirements.txt ]; then
    sudo apt-get update
    sudo apt-get install -y $(cat apt_requirements.txt) >> /var/log/automation.log 2>&1
fi

# Install Python dependencies if requirements.txt exists
if [ -f requirements.txt ]; then
    pip3 install -r requirements.txt >> /var/log/automation.log 2>&1
fi

# Run preflight checks if preflightcheck.sh exists
if [ -f preflightcheck.sh ]; then
    bash preflightcheck.sh >> /var/log/automation.log 2>&1
fi

# Start the main Python script if main.py exists
if [ -f main.py ]; then
    python3 main.py >> /var/log/automation.log 2>&1 &
fi

# sudo ~/mecanum-robot-control/line-following/python3 mecanum-line-controller.py
