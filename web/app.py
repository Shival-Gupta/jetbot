import os
import subprocess
from flask import Flask, render_template, jsonify, request, Response
import psutil
import logging
from logging.handlers import RotatingFileHandler

# --- Configuration ---
LOG_FILE = '/var/log/jetson-webui.log' # Matches setup.sh
SERVICE_NAME = "jetson-automation.service" # Matches setup.sh
REPO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) # Assumes app.py is in web/

# --- Logging Setup ---
log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
log_handler = RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=5) # 10MB per file, 5 backups
log_handler.setFormatter(log_formatter)

app = Flask(__name__)
app.logger.addHandler(log_handler)
app.logger.setLevel(logging.INFO)
app.logger.info("Web UI Flask App Starting...")

# --- Helper Functions ---
def run_sudo_command(command_args):
    """Runs a command using sudo and captures output."""
    try:
        # Prepend sudo to the command arguments
        full_command = ["sudo"] + command_args
        app.logger.info(f"Running sudo command: {' '.join(full_command)}")
        result = subprocess.run(full_command, capture_output=True, text=True, check=True, timeout=30)
        app.logger.info(f"Command successful: {result.stdout}")
        return {"success": True, "message": result.stdout or "Command executed successfully."}
    except subprocess.CalledProcessError as e:
        error_message = f"Command failed: {e.stderr or e.stdout or 'No output'}"
        app.logger.error(error_message)
        return {"success": False, "message": error_message}
    except subprocess.TimeoutExpired:
        error_message = "Command timed out after 30 seconds."
        app.logger.error(error_message)
        return {"success": False, "message": error_message}
    except Exception as e:
        error_message = f"An unexpected error occurred: {str(e)}"
        app.logger.error(error_message)
        return {"success": False, "message": error_message}

# --- Routes ---
@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/stats')
def get_stats():
    """Returns system statistics as JSON."""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        stats = {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_used_gb": round(disk.used / (1024**3), 2),
        }
        return jsonify(stats)
    except Exception as e:
        app.logger.error(f"Error getting stats: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/reboot', methods=['POST'])
def reboot_system():
    """Initiates system reboot."""
    app.logger.warning("Received request to REBOOT system.")
    result = run_sudo_command(["/sbin/shutdown", "-r", "now"])
    return jsonify(result)

@app.route('/shutdown', methods=['POST'])
def shutdown_system():
    """Initiates system shutdown."""
    app.logger.warning("Received request to SHUTDOWN system.")
    result = run_sudo_command(["/sbin/shutdown", "-h", "now"])
    return jsonify(result)

@app.route('/refresh', methods=['POST'])
def refresh_automation():
    """Restarts the automation service to pull code and re-run."""
    app.logger.info(f"Received request to REFRESH automation (restart {SERVICE_NAME}).")
    result = run_sudo_command(["/bin/systemctl", "restart", SERVICE_NAME])
    # Check if the command seemed successful based on output/return code proxy
    if result["success"]:
         # It might take a moment for the service to actually start the script
        result["message"] = f"Automation service '{SERVICE_NAME}' restart initiated. Check logs for details."
    return jsonify(result)

@app.route('/logs')
def stream_logs():
    """Streams the automation service log file."""
    log_file = f'/var/log/{SERVICE_NAME}.log' # Match service file
    app.logger.info(f"Streaming logs from {log_file}")
    try:
        def generate():
            # Check if file exists first
            if not os.path.exists(log_file):
                yield f"data: Log file not found: {log_file}\n\n"
                return

            with open(log_file, 'r') as f:
                # Seek to the end initially or send last N lines
                f.seek(0, os.SEEK_END)
                # Send a marker indicating start of streaming
                yield "data: --- Streaming logs started ---\n\n"
                while True:
                    line = f.readline()
                    if not line:
                        time.sleep(1) # Wait for new lines
                        continue
                    # Format as Server-Sent Event
                    yield f"data: {line.strip()}\n\n"
        return Response(generate(), mimetype='text/event-stream')
    except Exception as e:
        app.logger.error(f"Error streaming logs: {str(e)}")
        return Response(f"data: Error streaming logs: {str(e)}\n\n", mimetype='text/event-stream')


if __name__ == '__main__':
    # Use 0.0.0.0 to be accessible on the network, port 5000
    # Debug=False for production/service use
    # Let systemd service handle host/port via Environment variables
    app.run(host=os.environ.get("FLASK_RUN_HOST", "0.0.0.0"),
            port=int(os.environ.get("FLASK_RUN_PORT", 5000)),
            debug=False) # Important: Debug mode should be OFF when run as a service