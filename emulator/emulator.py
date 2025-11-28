import time
import json
import random
import os
from datetime import datetime
from google.cloud import pubsub_v1

# Налаштування
PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT')
TOPIC_ID = "iot-topic"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

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

print(f"Start emulation... Project: {PROJECT_ID}")

try:
    while True:
        sensor = random.choice(sensors)
        payload = sensor.generate_data()
        message_bytes = json.dumps(payload).encode("utf-8")
        
        try:
            publisher.publish(topic_path, data=message_bytes)
            print(f"Sent: {payload}")
        except Exception as e:
            print(f"Error: {e}")

        # Емуляція затримки 20-100 мс
        time.sleep(random.uniform(0.02, 0.1))

except KeyboardInterrupt:
    print("Stopped.")
