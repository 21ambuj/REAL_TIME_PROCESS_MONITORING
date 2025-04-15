import psutil
import time
from datetime import datetime
import json
import os

class ProcessManager:
    def __init__(self):
        self.whitelist = ["System Idle Process", "System", "explorer.exe", "svchost.exe"]
        self.history_file = "process_history.json"
        self.history = self._load_history()
        # List to store historical system stats (e.g., CPU and memory usage over time)
        self.stats_history = []

    def _load_history(self):
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f:
                return json.load(f)
        return []

    def _save_history(self):
        # Save only the last 100 threat/historical events to limit file size
        with open(self.history_file, 'w') as f:
            json.dump(self.history[-100:], f)

    def get_all_processes(self):
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cpu': proc.info['cpu_percent'],
                    'memory': proc.info['memory_percent'],
                    'status': proc.info['status']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes

    def check_threats(self, cpu_threshold=50):
        """
        Identify processes (outside the whitelist) that exceed the CPU usage threshold.
        Log such events with a timestamp.
        """
        threats = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                if proc.info['name'] not in self.whitelist and proc.info['cpu_percent'] > cpu_threshold:
                    threat = {
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cpu': proc.info['cpu_percent'],
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    threats.append(threat)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if threats:
            self.history.extend(threats)
            self._save_history()
        
        return threats

    def terminate_process(self, pid):
        try:
            process = psutil.Process(pid)
            process.terminate()
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def get_system_stats(self):
        """Return current system statistics including CPU usage, memory usage, and boot time."""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'boot_time': datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"),
            'running_processes': len(psutil.pids()),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def update_system_stats(self):
        """Append the current system statistics to the historical record.
           Only the last 100 entries are maintained."""
        current_stats = self.get_system_stats()
        self.stats_history.append(current_stats)
        # Maintain a fixed-size history for efficient retrieval and storage
        if len(self.stats_history) > 100:
            self.stats_history = self.stats_history[-100:]

    def get_stats_history(self):
        """Return the history of system stats for trend analysis."""
        return self.stats_history

    def get_history(self):
        """Return the event history from process threat checks."""
        return self.history
