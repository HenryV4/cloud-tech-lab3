import time
import json
import random
import os
import threading
from datetime import datetime
from google.cloud import pubsub_v1
from flask import Flask

app = Flask(__name__)

# --- CONTROL FLAGS ---
# Прапорець: чи слати дані? (За замовчуванням - True)
IS_RUNNING = True 

PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT')
TOPIC_ID = "iot-topic"

try:
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)
except:
    publisher = None

# --- SENSORS CONFIG ---
class Sensor:
    def __init__(self, sensor_type, location, min_val, max_val):
        self.sensor_type = sensor_type
        self.location = location
        self.min_val = min_val
        self.max_val = max_val

    def generate_data(self):
        data = {
            "sensor_type": self.sensor_type,
            "location": self.location,
            "timestamp": datetime.now().isoformat(),
            "value": round(random.uniform(self.min_val, self.max_val), 2)
        }
        if self.sensor_type == "Temperature": data["unit"] = "C"
        elif self.sensor_type == "Humidity": data["unit"] = "%"
        elif self.sensor_type == "Light": data["unit"] = "Lux"
        return data

sensors = [
    Sensor("Temperature", "Room-101", 18.0, 28.0),
    Sensor("Humidity", "Room-101", 30.0, 60.0),
    Sensor("Light", "Garden-A", 100.0, 1000.0)
]

# --- BACKGROUND THREAD ---
def run_emulator():
    print(f"Emulator started. Sending data: {IS_RUNNING}")
    while True:
        if IS_RUNNING and publisher and PROJECT_ID:
            try:
                sensor = random.choice(sensors)
                payload = sensor.generate_data()
                msg = json.dumps(payload).encode("utf-8")
                publisher.publish(topic_path, data=msg)
                print(f"Sent: {payload['sensor_type']}")
            except Exception as e:
                print(f"Error: {e}")
        elif not IS_RUNNING:
            print("Emulator PAUSED...")
        
        # Затримка
        time.sleep(random.uniform(0.1, 0.5))

# --- WEB CONTROLS ---
@app.route("/")
def status():
    state = "RUNNING" if IS_RUNNING else "PAUSED"
    return f"<h1>Status: {state}</h1><p>Use /stop to pause and /start to resume.</p>"

@app.route("/stop")
def stop_emu():
    global IS_RUNNING
    IS_RUNNING = False
    return "<h1>Emulator Stopped (Paused)</h1><a href='/'>Back</a>"

@app.route("/start")
def start_emu():
    global IS_RUNNING
    IS_RUNNING = True
    return "<h1>Emulator Started</h1><a href='/'>Back</a>"

if __name__ == "__main__":
    # Запускаємо емулятор у фоні
    t = threading.Thread(target=run_emulator)
    t.daemon = True
    t.start()
    
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
