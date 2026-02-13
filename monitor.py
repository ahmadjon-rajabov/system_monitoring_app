import psutil  
import time    

def start_monitoring():
    print("System Monitor: ON. Press Ctrl+C to stop.")

    while True:
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            
            print(f"Current CPU Load: {cpu_usage}%")

            ALERT_THRESHOLD = 20 

            if cpu_usage > ALERT_THRESHOLD:
                print("⚠️  ALERT: HIGH CPU USAGE DETECTED! ⚠️")
            
            time.sleep(2)

        except KeyboardInterrupt:
            print("\nStopping Monitor...")
            break

if __name__ == "__main__":
    start_monitoring()