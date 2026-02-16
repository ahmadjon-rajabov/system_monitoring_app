import psutil
import time, os
from src.database import DatabaseManager

class SystemMonitor:
    def __init__(self):
        print("System Monitor starting...")
        self.db = DatabaseManager()
        self.last_net = psutil.net_io_counters()
        self.last_time = time.time()
    
    def collect_metrics(self):
        """
        Gathers system stats
        """
        try:
            cpu = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent

            current_net = psutil.net_io_counters()
            current_time = time.time()
            # delta (change)
            bytes_sent = current_net.bytes_sent - self.last_net.bytes_sent
            bytes_recv = current_net.bytes_recv - self.last_net.bytes_recv
            # convert to megabytes
            total_bytes = bytes_sent + bytes_recv
            mb_total = total_bytes / (1024 * 1024)
            # update state for next loop
            self.last_net = current_net
            self.last_time = current_time
            return cpu, memory, disk, round(mb_total, 2)
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
                time.sleep(1)
                cpu, memory, disk, net = self.collect_metrics()
                print(f"Stats -> CPU: {cpu}% | RAM: {memory}% | Disk: {disk}% | Net: {net} MB/s")
                self.db.save_metric(cpu, memory, disk, net)
        except KeyboardInterrupt:
            print("\nMonitor Stopped")

if __name__ == "__main__":
    app = SystemMonitor()
    app.start()