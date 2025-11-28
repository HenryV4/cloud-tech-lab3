import time
import json
import random
import os
import threading
from datetime import datetime
from google.cloud import pubsub_v1
from flask import Flask

# --- WEB SERVER PART (Щоб Cloud Run не вбивав контейнер) ---
app = Flask(__name__)

@app.route("/")
def index():
    return "Emulator is running...", 200

# --- EMULATOR PART ---
# Налаштування
PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT')
TOPIC_ID = "iot-topic"

# Ініціалізація Pub/Sub
try:
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)
except Exception as e:
    print(f"Error init PubSub: {e}")

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
        if self.sensor_type == "Temperature":
            data["unit"] = "C"
        elif self.sensor_type == "Humidity":
            data["unit"] = "%"
        elif self.sensor_type == "Light":
            data["unit"] = "Lux"
        return data

sensors = [
    Sensor("Temperature", "Room-101", 18.0, 28.0),
    Sensor("Humidity", "Room-101", 30.0, 60.0),
    Sensor("Light", "Garden-A", 100.0, 1000.0)
]

def run_emulator():
    print(f"Start emulation... Project: {PROJECT_ID}")
    while True:
        try:
            sensor = random.choice(sensors)
            payload = sensor.generate_data()
            message_bytes = json.dumps(payload).encode("utf-8")
            
            if PROJECT_ID: # Перевірка, щоб локально не падало без ID
                publisher.publish(topic_path, data=message_bytes)
                print(f"Sent: {payload}")
            else:
                print(f"Simulation (No Project ID): {payload}")
                
        except Exception as e:
            print(f"Error sending: {e}")

        # Емуляція затримки 20-100 мс
        time.sleep(random.uniform(0.02, 0.1))

# --- MAIN ---
if __name__ == "__main__":
    # Запускаємо емулятор у фоновому потоці
    thread = threading.Thread(target=run_emulator)
    thread.daemon = True
    thread.start()

    # Запускаємо веб-сервер на порту, який дає Cloud Run (або 8080)
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
