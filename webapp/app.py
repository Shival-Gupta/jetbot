from flask import Flask, render_template, request
import psutil
import subprocess
import os

app = Flask(__name__)

@app.route('/')
def index():
    # System stats
    cpu_usage = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent
    # Placeholder for GPU and thermals (expand as needed)
    gpu_usage = "N/A"  # Requires tegrastats or similar
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            thermals = int(f.read()) / 1000  # Convert to Celsius
    except:
        thermals = "N/A"

    # Neofetch output
    neofetch_output = subprocess.check_output(['neofetch', '--stdout']).decode('utf-8')

    # Automation log
    automation_log = ""
    if os.path.exists('/var/log/automation.log'):
        with open('/var/log/automation.log', 'r') as f:
            automation_log = f.read()

    return render_template('index.html', cpu_usage=cpu_usage, ram_usage=ram_usage, gpu_usage=gpu_usage, thermals=thermals, neofetch=neofetch_output, automation_log=automation_log)

@app.route('/action', methods=['POST'])
def action():
    action = request.form['action']
    if action == 'restart':
        os.system('sudo reboot')
    elif action == 'poweroff':
        os.system('sudo poweroff')
    return 'Action performed'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)