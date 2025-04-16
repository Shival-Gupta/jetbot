#!/usr/bin/env python3
"""
main.py
Description: Entry point script that runs the Streamlit-based Mecanum Line Follower Controller.
"""
print("Main script running")

import subprocess
import sys
import time

def run_streamlit_app(serial_port="/dev/ttyACM0", baud=115200, port=8800):
    """
    Run the Streamlit app (webapp.py) with specified arguments.
    
    Args:
        serial_port (str): Serial port for the robot (default: /dev/ttyACM0)
        baud (int): Baud rate for serial communication (default: 115200)
        port (int): Streamlit server port (default: 8800)
    """
    try:
        # Construct the command to run webapp.py with arguments
        cmd = [
            sys.executable,  # Use the same Python interpreter as main.py
            "webapp.py",
            "--serial-port", serial_port,
            "--baud", str(baud),
            "--port", str(port)
        ]
        
        # Launch the Streamlit app as a subprocess
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        print(f"Started Streamlit app on port {port} with serial port {serial_port} and baud {baud}")
        
        # Optionally, monitor the subprocess output (for debugging)
        # This is commented out to avoid blocking, but can be enabled if needed
        """
        while process.poll() is None:
            output = process.stdout.readline()
            if output:
                print(output.strip())
            error = process.stderr.readline()
            if error:
                print(f"Error: {error.strip()}")
        """
        
        return process
    except Exception as e:
        print(f"Failed to start Streamlit app: {e}")
        sys.exit(1)

def main():
    """Main function to run the script."""
    print("Main script running")
    
    # Configure arguments for webapp.py
    serial_port = "/dev/ttyACM0"  # Adjust as needed
    baud = 115200
    streamlit_port = 8800
    
    # Run the Streamlit app
    process = run_streamlit_app(serial_port, baud, streamlit_port)
    
    # Keep main.py running or perform other tasks
    try:
        # Wait for the subprocess to complete (optional)
        # Alternatively, you can let it run in the background
        process.wait()
    except KeyboardInterrupt:
        print("\nTerminating Streamlit app...")
        process.terminate()
        try:
            process.wait(timeout=5)  # Give it some time to shut down gracefully
        except subprocess.TimeoutExpired:
            process.kill()  # Force kill if it doesn't terminate
        print("Streamlit app terminated")
        sys.exit(0)

if __name__ == "__main__":
    main()