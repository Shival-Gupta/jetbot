#!/usr/bin/env python3
"""
mecanum_line_controller_streamlit.py
Version: 2.1

Description: Streamlit-based controller for a line-following Mecanum robot.
Provides a web interface with press-and-hold buttons for forward/backward
and a stop button, accessible over a network. Supports serial communication
with error handling and response reading.

Compatible with:
  - mecanum-line-follower-basic.ino
  - mecanum-line-follower-advanced.ino

Usage:
    python3 mecanum_line_controller_streamlit.py [--serial-port PORT] [--baud BAUD] [--port STREAMLIT_PORT]

Arguments:
    --serial-port  Serial port (default: /dev/ttyACM0)
    --baud         Baud rate (default: 115200)
    --port         Streamlit server port (default: 8800)
"""

import streamlit as st
import serial
import argparse
import time
import sys
from typing import Optional
import threading
import queue

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

    def connect(self) -> bool:
        """Establish serial connection to the robot."""
        try:
            self.serial = serial.Serial(self.port, self.baud_rate, timeout=1)
            time.sleep(2)  # Allow Arduino to reset
            st.success(f"Connected to {self.port} at {self.baud_rate} baud")
            self.running = True
            self.thread = threading.Thread(target=self._read_responses, daemon=True)
            self.thread.start()
            return True
        except serial.SerialException as e:
            st.error(f"Failed to connect: {e}")
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
            except serial.SerialException:
                self.response_queue.put("Error: Failed to close serial connection")

def main():
    """Main function to run the Streamlit controller."""
    parser = argparse.ArgumentParser(description="Mecanum Line Follower Streamlit Controller")
    parser.add_argument('--serial-port', default='/dev/ttyACM0', help='Serial port (e.g., /dev/ttyACM0 or COM3)')
    parser.add_argument('--baud', type=int, default=115200, help='Baud rate (e.g., 115200)')
    parser.add_argument('--port', type=int, default=8800, help='Streamlit server port (e.g., 8800)')
    args = parser.parse_args()

    # Initialize controller
    controller = RobotController(args.serial_port, args.baud)
    if not controller.connect():
        st.error("Exiting due to connection failure")
        sys.exit(1)

    # Streamlit UI
    st.title("Mecanum Line Follower Controller")
    st.markdown("""
    Control your Mecanum wheel robot using the buttons below.
    - **Forward**: Move the robot forward along the line
    - **Backward**: Move the robot backward along the line
    - **Stop**: Halt the robot
    """)

    # Button states for press-and-hold simulation
    if 'forward_active' not in st.session_state:
        st.session_state.forward_active = False
    if 'backward_active' not in st.session_state:
        st.session_state.backward_active = False

    # Create columns for buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Forward", key="forward"):
            if not st.session_state.forward_active:
                st.session_state.forward_active = True
                controller.send_command('f')
        if st.session_state.forward_active and st.button("Release Forward", key="release_forward"):
            st.session_state.forward_active = False
            controller.send_command('s')

    with col2:
        if st.button("Backward", key="backward"):
            if not st.session_state.backward_active:
                st.session_state.backward_active = True
                controller.send_command('b')
        if st.session_state.backward_active and st.button("Release Backward", key="release_backward"):
            st.session_state.backward_active = False
            controller.send_command('s')

    with col3:
        if st.button("Stop", key="stop"):
            st.session_state.forward_active = False
            st.session_state.backward_active = False
            controller.send_command('s')

    # Display responses
    st.subheader("Robot Responses")
    response_container = st.empty()
    
    # Continuously update responses
    while not controller.response_queue.empty():
        response = controller.response_queue.get()
        with response_container.container():
            st.text(response)

    # Ensure clean exit
    def on_exit():
        controller.close()
        sys.exit(0)

    if st.button("Exit"):
        on_exit()

if __name__ == "__main__":
    main()