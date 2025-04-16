# Jetson Nano Automation Framework

This repository contains scripts to automate setup, updates, and execution of projects on a Jetson Nano.

## Features

* **One-Time Setup:** `setup.sh` installs dependencies and configures the system.
* **Auto-Update & Execute:** An `autoexec.sh` script runs on boot (via systemd):
    * Waits for network connectivity.
    * Force pulls the latest code from the `main` branch of this repository, overwriting local changes.
    * Installs/updates Python package requirements (`requirements.txt`) found within the `src/` subdirectories.
    * Executes the main application logic defined in `run.sh`.
* **Web Interface:** A simple Flask web server (`web/app.py`) provides:
    * Basic system stats (CPU, RAM, Disk).
    * Buttons for Reboot, Shutdown.
    * A "Refresh Automation" button to re-trigger the update and execution process.
* **Project Structure:** Place your individual projects within the `src/` directory.

## Setup Instructions

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/your-username/jetson-automation.git](https://github.com/your-username/jetson-automation.git)
    cd jetson-automation
    ```
    *(Replace with your actual repository URL)*

2.  **Run Setup Script:**
    *Ensure you are in the `jetson-automation` directory.*
    ```bash
    sudo bash setup.sh
    ```
    This script will:
    * Install necessary `apt` packages (git, python3, pip, venv, flask, psutil, etc.).
    * Install global Python requirements (if `requirements.txt` exists in the root).
    * Configure and enable the `jetson-automation.service` systemd service.
    * Configure `sudoers` to allow passwordless control via the web interface.
    * Start the automation service and the web UI service.

3.  **Access Web Interface:**
    Open a web browser and navigate to `http://<JETSON_NANO_IP>:5000`.

## Usage

* The system will automatically update and run the code defined in `run.sh` on every boot.
* Modify `run.sh` to define how your projects in `src/` should be started.
* Add project-specific Python dependencies to `src/<your_project>/requirements.txt`.
* Commit and push changes to the `main` branch of your GitHub repository. The Jetson Nano will automatically pull these changes on the next boot or when "Refresh Automation" is clicked.

## Customization

* **Target User:** The scripts assume the user running `setup.sh` (before `sudo`) is the target user (e.g., `ubuntu`). If different, modify `setup.sh` and the `.service` files.
* **Branch:** The default branch is `main`. Modify `autoexec.sh` if using a different branch.
* **Web Port:** Change the port in `web/webui.service` and `web/app.py` if needed.