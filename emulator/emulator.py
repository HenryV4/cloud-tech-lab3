import asyncio
import json
import random
import threading
import time
import os
from datetime import datetime
from google.cloud import pubsub_v1
from flask import Flask, jsonify, request

# --- Конфігурація та Ініціалізація ---

try:
    with open('config.json', 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    print("Помилка: Файл config.json не знайдено.")
    exit()

PUBSUB_PROJECT_ID = config['pubsub_project_id']
PUBSUB_TOPIC_ID = config['pubsub_topic_id']

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PUBSUB_PROJECT_ID, PUBSUB_TOPIC_ID)

# --- Глобальні змінні для керування ---
IS_RUNNING = True
emulators_thread = None

# --- Логіка емуляції (без змін, крім виходу) ---

def generate_value(device_type):
    if device_type == "temperature":
        return round(random.uniform(15.0, 30.0), 2)
    elif device_type == "humidity":
        return random.randint(30, 80)
    elif device_type == "light":
        return random.randint(100, 1000)
    return None

async def device_emulator(device_config):
    device_id = device_config['id']
    device_type = device_config['type']
    frequency_ms = device_config['frequency_ms']
    location = device_config['location']
    
    interval_sec = frequency_ms / 1000.0
    print(f"[{device_id}] Емулятор запущено. Частота: {frequency_ms} ms")
    
    while IS_RUNNING: # Перевірка глобального прапорця
        start_time = time.monotonic()
        try:
            payload = {
                "device_id": device_id,
                "device_type": device_type,
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "location": location,
                "value": generate_value(device_type)
            }
            
            data = json.dumps(payload).encode("utf-8")
            future = publisher.publish(topic_path, data, device_type=device_type)
            print(f"[{device_id}] Надсилання: {payload['value']} {device_type}. Future ID: {future.result()}")
            
        except Exception as e:
            print(f"[{device_id}] Помилка надсилання: {e}")
            
        elapsed_time = time.monotonic() - start_time
        sleep_time = max(0, interval_sec - elapsed_time)
        
        await asyncio.sleep(sleep_time)

def run_emulators_in_loop():
    """Запускає асинхронний цикл для всіх емуляторів."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    tasks = [asyncio.create_task(device_emulator(cfg)) for cfg in config['devices']]
    
    print("Усі асинхронні завдання емуляторів запущені.")
    loop.run_until_complete(asyncio.gather(*tasks))


# --- Веб-сервер Flask для Cloud Run ---

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    """Перевірка стану та головна сторінка."""
    status = "працює" if IS_RUNNING else "зупинено"
    return jsonify({
        "status": f"IoT Емулятор {status}",
        "message": "Перейдіть до /stop, щоб зупинити емуляцію і заощадити кошти."
    }), 200

@app.route('/stop', methods=['POST', 'GET'])
def stop_emulator():
    """Керування: зупиняє цикл емуляції."""
    global IS_RUNNING
    if IS_RUNNING:
        IS_RUNNING = False
        print("!!! ОТРИМАНО КОМАНДУ /stop. ЕМУЛЯТОРИ ЗУПИНЯЮТЬСЯ !!!")
        return jsonify({"status": "Success", "message": "Емуляцію зупинено. Cloud Run буде чекати тарифікованих запитів, але фоновий worker вимкнено."}), 200
    else:
        return jsonify({"status": "Already Stopped", "message": "Емулятори вже не працюють."}), 200


# Запуск фонового потоку при старті
if __name__ == '__main__':
    emulators_thread = threading.Thread(target=run_emulators_in_loop)
    emulators_thread.start()
    
    # Визначення порту, який надає Cloud Run
    port = int(os.environ.get("PORT", 8080))
    print(f"Flask запущено на порту {port}")
    app.run(host="0.0.0.0", port=port)
