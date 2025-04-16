#!/usr/bin/env python3
"""
main.py
Description: Entry point script that runs the Flask-based Mecanum Line Follower Controller.
"""

import subprocess
import sys
import time
import os

def run_flask_app(serial_port="/dev/ttyACM0", baud=115200, port=8800):
    """
    Run the Flask app (control/webapp.py) with specified arguments.
    
    Args:
        serial_port (str): Serial port for the robot (default: /dev/ttyACM0)
        baud (int): Baud rate for serial communication (default: 115200)
        port (int): Flask server port (default: 8800)
    """
    try:
        # Construct the command to run webapp.py with arguments
        webapp_path = os.path.join("control", "webapp.py")
        cmd = [
            sys.executable,  # Use the same Python interpreter as main.py
            webapp_path,
            "--serial-port", serial_port,
            "--baud", str(baud),
            "--port", str(port)
        ]
        
        # Launch the Flask app as a subprocess
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        print(f"Started Flask app on port {port} with serial port {serial_port} and baud {baud}")
        
        return process
    except Exception as e:
        print(f"Failed to start Flask app: {e}")
        sys.exit(1)

def main():
    """Main function to run the script."""
    print("Main script running")
    
    # Configure arguments for webapp.py
    serial_port = "/dev/ttyACM0"  # Adjust to your Arduino's port if needed
    baud = 115200
    flask_port = 8800
    
    # Run the Flask app
    process = run_flask_app(serial_port, baud, flask_port)
    
    # Keep main.py running or perform other tasks
    try:
        # Wait for the subprocess to complete
        process.wait()
    except KeyboardInterrupt:
        print("\nTerminating Flask app...")
        process.terminate()
        try:
            process.wait(timeout=5)  # Give it some time to shut down gracefully
        except subprocess.TimeoutExpired:
            process.kill()  # Force kill if it doesn't terminate
        print("Flask app terminated")
        sys.exit(0)

if __name__ == "__main__":
    main()