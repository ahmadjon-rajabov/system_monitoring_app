import psutil
import time, os
from src.database import DatabaseManager

class SystemMonitor:
    def __init__(self):
        print("System Monitor starting...")
        self.db = DatabaseManager()
    
    def collect_metrics(self):
        """
        Gathers system stats
        """
        try:
            cpu = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent

            return cpu, memory, disk
        except Exception as e:
            print(f"Error collection metrics: {e}")
            return 0, 0, 0
    
    def start(self):
        """
        The main Loop
        """
        print("Monitoring Active. Press Ctrl+C to stop")
        try:
            while True:
                cpu, memory, disk = self.collect_metrics()
                print(f"Stats -> CPU: {cpu}% | RAM: {memory}% | Disk: {disk}%")
                self.db.save_metric(cpu, memory, disk)
                time.sleep(2)
        except KeyboardInterrupt:
            print("\nMonitor Stopped")

if __name__ == "__main__":
    app = SystemMonitor()
    app.start()