import time
import os

print(f"Hello from Project 1! Running in directory: {os.getcwd()}")
print("This script will print time every 10 seconds.")

count = 0
while True:
    print(f"Project 1: Count {count} - Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    count += 1
    time.sleep(10)