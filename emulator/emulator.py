import time
import json
import random
import os
import threading
from datetime import datetime
from google.cloud import pubsub_v1
from flask import Flask, render_template_string, redirect, url_for

app = Flask(__name__)

# --- GLOBAL STATE ---
IS_RUNNING = True 
PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT')
TOPIC_ID = "iot-topic"
LAST_LOG = "Waiting for data..."

# --- PUBSUB INIT ---
try:
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)
except:
    publisher = None

# --- HTML TEMPLATE (UI) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>IoT Emulator Control</title>
    <meta http-equiv="refresh" content="3">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #e9ecef; padding-top: 50px; }
        .container { max-width: 600px; }
        .card { border-radius: 15px; box-shadow: 0 10px 20px rgba(0,0,0,0.1); }
        .status-indicator { font-size: 1.2rem; font-weight: bold; }
        .log-box { background: #000; color: #0f0; padding: 10px; border-radius: 5px; font-family: monospace; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card text-center p-4">
            <h2 class="mb-3">📡 IoT Device Emulator</h2>
            
            <div class="mb-4">
                Status: 
                {% if is_running %}
                    <span class="badge bg-success status-indicator">ONLINE (SENDING)</span>
                {% else %}
                    <span class="badge bg-danger status-indicator">OFFLINE (PAUSED)</span>
                {% endif %}
            </div>

            <div class="d-grid gap-2 d-sm-flex justify-content-sm-center mb-4">
                {% if is_running %}
                    <a href="/stop" class="btn btn-danger btn-lg px-5">STOP Simulation</a>
                {% else %}
                    <a href="/start" class="btn btn-success btn-lg px-5">START Simulation</a>
                {% endif %}
            </div>

            <div class="text-start">
                <label class="text-muted">Last Action:</label>
                <div class="log-box">{{ last_log }}</div>
            </div>
            
            <div class="mt-3 text-muted small">
                Project ID: {{ project_id }} <br>
                Target Topic: {{ topic_id }}
            </div>
        </div>
    </div>
</body>
</html>
"""

# --- SENSORS ---
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
    global LAST_LOG
    print("Emulator thread started.")
    while True:
        if IS_RUNNING and publisher and PROJECT_ID:
            try:
                sensor = random.choice(sensors)
                payload = sensor.generate_data()
                msg = json.dumps(payload).encode("utf-8")
                publisher.publish(topic_path, data=msg)
                
                log_msg = f"Sent {payload['sensor_type']} value={payload['value']} to Pub/Sub"
                print(log_msg)
                LAST_LOG = log_msg
            except Exception as e:
                print(f"Error: {e}")
                LAST_LOG = f"Error: {e}"
        
        time.sleep(random.uniform(0.2, 0.8))

# --- ROUTES ---
@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, 
                                is_running=IS_RUNNING, 
                                last_log=LAST_LOG,
                                project_id=PROJECT_ID,
                                topic_id=TOPIC_ID)

@app.route("/stop")
def stop():
    global IS_RUNNING, LAST_LOG
    IS_RUNNING = False
    LAST_LOG = "Simulation Paused by User"
    return redirect(url_for('index'))

@app.route("/start")
def start():
    global IS_RUNNING, LAST_LOG
    IS_RUNNING = True
    LAST_LOG = "Simulation Resumed"
    return redirect(url_for('index'))

if __name__ == "__main__":
    t = threading.Thread(target=run_emulator)
    t.daemon = True
    t.start()
    
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
