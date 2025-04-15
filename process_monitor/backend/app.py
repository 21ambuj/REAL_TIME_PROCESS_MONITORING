from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import threading
import time
from process_manager import ProcessManager

app = Flask(__name__, static_folder='../frontend')
CORS(app)

# Initialize the process manager from the dedicated module
manager = ProcessManager()

# Background monitoring thread for both process threats and system stats history
def monitor_system():
    while True:
        # Check for processes that exceed the CPU threshold and log them as potential threats
        manager.check_threats()
        # Update the system statistics history with current metrics
        manager.update_system_stats()
        time.sleep(5)  # Adjust the frequency as needed

monitor_thread = threading.Thread(target=monitor_system)
monitor_thread.daemon = True
monitor_thread.start()

# API Endpoints

@app.route('/api/processes', methods=['GET'])
def get_processes():
    """Return a list of all active processes with details."""
    return jsonify(manager.get_all_processes())

@app.route('/api/threats', methods=['GET'])
def get_threats():
    """Return processes that have exceeded the defined CPU threshold."""
    return jsonify(manager.check_threats())

@app.route('/api/terminate', methods=['POST'])
def terminate_process():
    """Terminate a process, given its PID."""
    data = request.json
    if 'pid' not in data:
        return jsonify({'success': False, 'error': 'PID not provided'}), 400
    success = manager.terminate_process(data['pid'])
    return jsonify({'success': success})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Return current system statistics including CPU and memory usage."""
    return jsonify(manager.get_system_stats())

@app.route('/api/history', methods=['GET'])
def get_history():
    """Return the history of potential threats and process events."""
    return jsonify(manager.get_history())

@app.route('/api/historic_stats', methods=['GET'])
def get_historic_stats():
    """Return historical system stats to support trend analysis."""
    return jsonify(manager.get_stats_history())

# Serve the frontend dashboard
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

# Error Handling
@app.errorhandler(404)
def not_found(e):
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
