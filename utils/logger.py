import datetime
import os

def log(message):
    os.makedirs("outputs/logs", exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    with open("outputs/logs/run.txt", "a") as f:
        f.write(f"[{timestamp}] {message}\n")