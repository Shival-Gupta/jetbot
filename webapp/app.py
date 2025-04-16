from flask import Flask, jsonify, request
from flask_cors import CORS
import psutil
import subprocess
import os

app = Flask(__name__)
CORS(app)  # Allow CORS for React frontend

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        # System stats
        cpu_usage = psutil.cpu_percent(interval=0.1)
        ram_usage = psutil.virtual_memory().percent
        gpu_usage = "N/A"  # Requires tegrastats for Jetson GPU
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                thermals = int(f.read()) / 1000  # Convert to Celsius
        except:
            thermals = "N/A"

        # Neofetch output
        try:
            neofetch_output = subprocess.check_output(['neofetch', '--stdout'], text=True)
        except:
            neofetch_output = "Neofetch not available"

        # Automation log
        automation_log = ""
        if os.path.exists('/var/log/automation.log'):
            with open('/var/log/automation.log', 'r') as f:
                automation_log = f.read()

        return jsonify({
            'cpu_usage': cpu_usage,
            'ram_usage': ram_usage,
            'gpu_usage': gpu_usage,
            'thermals': thermals,
            'neofetch': neofetch_output,
            'automation_log': automation_log
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/action', methods=['POST'])
def perform_action():
    try:
        action = request.json.get('action')
        if action == 'restart':
            os.system('sudo reboot')
            return jsonify({'status': 'Restart initiated'})
        elif action == 'poweroff':
            os.system('sudo poweroff')
            return jsonify({'status': 'Power off initiated'})
        else:
            return jsonify({'error': 'Invalid action'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)