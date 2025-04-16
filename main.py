#!/usr/bin/env python3
"""
main.py
Version: 2.2

Description: Flask-based controller for a line-following Mecanum robot.
Provides a web interface with press-and-hold buttons for forward/backward
and a stop button, accessible over a network. Supports serial communication
with error handling and response reading.

Compatible with:
  - mecanum-line-follower-basic.ino
  - mecanum-line-follower-advanced.ino

Usage:
    python3 main.py [--serial-port PORT] [--baud BAUD] [--port FLASK_PORT]

Arguments:
    --serial-port  Serial port (default: /dev/ttyACM0)
    --baud         Baud rate (default: 115200)
    --port         Flask server port (default: 8800)
"""

import serial
import argparse
import time
import sys
from typing import Optional
import threading
import queue
from flask import Flask, render_template, jsonify, request
import os

app = Flask(__name__)

class RobotController:
    """Manages serial communication with the robot."""
    
    def __init__(self, port: str, baud_rate: int):
        """Initialize the controller with serial port and baud rate."""
        self.port = port
        self.baud_rate = baud_rate
        self.serial: Optional[serial.Serial] = None
        self.response_queue = queue.Queue()
        self.running = False
        self.thread = None
        self.responses = []  # Store responses for display

    def connect(self) -> bool:
        """Establish serial connection to the robot."""
        try:
            self.serial = serial.Serial(self.port, self.baud_rate, timeout=1)
            time.sleep(2)  # Allow Arduino to reset
            self.response_queue.put(f"Connected to {self.port} at {self.baud_rate} baud")
            self.running = True
            self.thread = threading.Thread(target=self._read_responses, daemon=True)
            self.thread.start()
            return True
        except serial.SerialException as e:
            self.response_queue.put(f"Failed to connect: {e}")
            return False

    def _read_responses(self):
        """Continuously read responses from the robot and put them in the queue."""
        while self.running and self.serial and self.serial.is_open:
            if self.serial.in_waiting > 0:
                try:
                    response = self.serial.readline().decode('utf-8').strip()
                    if response:
                        self.response_queue.put(f"Robot: {response}")
                except serial.SerialException:
                    self.response_queue.put("Error: Serial communication failed")
            time.sleep(0.01)

    def send_command(self, command: str) -> None:
        """Send a command to the robot."""
        if self.serial and self.serial.is_open:
            try:
                command_map = {'f': 'forward', 'b': 'backward', 's': 'stop'}
                full_command = command_map.get(command, command)
                self.serial.write(f"{full_command}\n".encode('utf-8'))
                self.response_queue.put(f"Sent: {full_command}")
            except serial.SerialException as e:
                self.response_queue.put(f"Error sending command: {e}")
        else:
            self.response_queue.put("Error: Not connected to robot")

    def close(self) -> None:
        """Close the serial connection."""
        self.running = False
        if self.serial and self.serial.is_open:
            try:
                self.serial.write("stop\n".encode('utf-8'))
                self.serial.close()
                self.response_queue.put("Serial connection closed")
            except serial.SerialException as e:
                self.response_queue.put(f"Error: Failed to close serial connection")

    def get_responses(self):
        """Retrieve all queued responses."""
        while not self.response_queue.empty():
            self.responses.append(self.response_queue.get())
        return self.responses

# Global controller instance
controller = None

@app.route('/')
def index():
    """Render the main control interface."""
    return render_template('index.html')

@app.route('/command', methods=['POST'])
def handle_command():
    """Handle robot control commands."""
    data = request.json
    command = data.get('command')
    if command in ['f', 'b', 's']:
        controller.send_command(command)
        return jsonify({'status': 'success', 'responses': controller.get_responses()})
    return jsonify({'status': 'error', 'message': 'Invalid command'})

@app.route('/responses')
def get_responses():
    """Return the latest responses from the robot."""
    return jsonify({'responses': controller.get_responses()})

def main():
    """Main function to run the Flask controller."""
    global controller
    print("Main script running")
    
    parser = argparse.ArgumentParser(description="Mecanum Line Follower Flask Controller")
    parser.add_argument('--serial-port', default='/dev/ttyACM0', help='Serial port (e.g., /dev/ttyACM0)')
    parser.add_argument('--baud', type=int, default=115200, help='Baud rate (e.g., 115200)')
    parser.add_argument('--port', type=int, default=8800, help='Flask server port (e.g., 8800)')
    args = parser.parse_args()

    # Initialize controller
    controller = RobotController(args.serial_port, args.baud)
    if not controller.connect():
        print("Exiting due to connection failure")
        sys.exit(1)

    try:
        # Run Flask app
        app.run(host='0.0.0.0', port=args.port, debug=False)
    except KeyboardInterrupt:
        print("\nShutting down Flask server...")
        controller.close()
        sys.exit(0)
    finally:
        controller.close()

if __name__ == "__main__":
    main()