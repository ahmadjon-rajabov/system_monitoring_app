import time
from src.database import DatabaseManager
from src.actuator import Actuator

class AutoScaler:
    def __init__(self):
        self.db = DatabaseManager()
        self.actuator = Actuator()
        self.cooldown_end = 0 

        # Rules
        self.HIGH_LOAD_THRESHOLD = 50.0 # CPU > 50% Scale UP
        self.LOW_LOAD_THRESHOLD = 10.0  # CPU < 10% Scale DOWN
        self.COOLDOWN_SECONDS = 30      # Wait for 30s between actions
        
    def decide(self):
        metrics = self.db.get_recent_metrics(limit=1)
        if not metrics:
            print("Waiting for data...")
            return
        
        current_cpu = metrics[0]['cpu']
        current_time = time.time()

        if current_time < self.cooldown_end:
            remaining = int(self.cooldown_end - current_time)
            print(f"Cooldown active ({remaining}s reamining)...")
            return
        
        print(f"Analyzing: CPU is {current_cpu}")

        if current_cpu > self.HIGH_LOAD_THRESHOLD:
            print(f"High Load Detected! ({current_cpu}% > {self.HIGH_LOAD_THRESHOLD}%)")
            self.actuator.scale_up()
            self.cooldown_end = time.time() + self.COOLDOWN_SECONDS
        elif current_cpu < self.LOW_LOAD_THRESHOLD:
            print(f"Low Load Detected! ({current_cpu}% < {self.HIGH_LOAD_THRESHOLD}%)")
            self.actuator.scale_down()
            self.cooldown_end = time.time() + self.COOLDOWN_SECONDS
        
    def start(self):
        print("Auto-Scaler Agent: ONLINE")
        try:
            while True:
                self.decide()
                time.sleep(5)
        except KeyboardInterrupt:
            print("\nAuto-Scaler Stopped")

if __name__ == "__main__":
    bot = AutoScaler()
    bot.start()