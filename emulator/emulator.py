import asyncio
import json
import random
from datetime import datetime
from google.cloud import pubsub_v1

# --- Конфігурація та Ініціалізація ---

try:
    with open('config.json', 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    print("Помилка: Файл config.json не знайдено.")
    exit()
except json.JSONDecodeError:
    print("Помилка: Невірний формат JSON у config.json.")
    exit()

# Ініціалізація клієнта Pub/Sub
PUBSUB_PROJECT_ID = config['pubsub_project_id']
PUBSUB_TOPIC_ID = config['pubsub_topic_id']

# Клієнт Pub/Sub (автоматично використовує облікові дані Cloud Run Service Account)
try:
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PUBSUB_PROJECT_ID, PUBSUB_TOPIC_ID)
    print(f"Pub/Sub ініціалізовано. Топік: {topic_path}")
except Exception as e:
    print(f"Помилка ініціалізації Pub/Sub клієнта: {e}")
    # Не виходимо, щоб дати можливість запуститися, але це критична помилка

# --- Генерація Даних ---

def generate_value(device_type):
    """Генерує унікальний параметр для типу датчика."""
    if device_type == "temperature":
        # Температура: 15.0 - 30.0 °C
        return round(random.uniform(15.0, 30.0), 2)
    elif device_type == "humidity":
        # Вологість: 30 - 80 %
        return random.randint(30, 80)
    elif device_type == "light":
        # Освітленість: 100 - 1000 lux
        return random.randint(100, 1000)
    return None

# --- Емулятор Пристрою ---

async def device_emulator(device_config):
    """Асинхронна функція для емуляції одного пристрою."""
    
    device_id = device_config['id']
    device_type = device_config['type']
    frequency_ms = device_config['frequency_ms']
    location = device_config['location']
    
    # Інтервал очікування в секундах
    interval_sec = frequency_ms / 1000.0
    
    print(f"[{device_id}] Емулятор запущено. Частота: {frequency_ms} ms")
    
    while True:
        start_time = time.monotonic()
        try:
            # 1. Згенерувати дані
            unique_value = generate_value(device_type)
            
            payload = {
                "device_id": device_id,
                "device_type": device_type,
                "timestamp": datetime.utcnow().isoformat() + 'Z', # Дата передачі (ISO 8601 UTC)
                "location": location,
                "value": unique_value
            }
            
            # 2. Підготовка та надсилання даних до Pub/Sub
            data = json.dumps(payload).encode("utf-8")
            
            # Надсилаємо, додаючи атрибут device_type для майбутньої фільтрації
            future = publisher.publish(
                topic_path, 
                data, 
                device_type=device_type
            )
            
            # Не чекаємо future.result() тут, щоб не блокувати асинхронний цикл
            # і підтримувати високу частоту. Результат перевіряється в фоні.
            
            print(f"[{device_id}] Надсилання: {payload['value']} {device_type}. Future ID: {future.result()}")
            
        except Exception as e:
            print(f"[{device_id}] Помилка надсилання: {e}")
            
        # 3. Обчислення часу очікування
        elapsed_time = time.monotonic() - start_time
        sleep_time = max(0, interval_sec - elapsed_time)
        
        # Емуляція затримки, щоб забезпечити частоту виконання
        await asyncio.sleep(sleep_time)

# --- Основна Функція ---

async def main():
    """Запускає всі емулятори пристроїв паралельно."""
    # Перевірка: чи відповідає частота вимогам (20-100 ms)
    for device_cfg in config['devices']:
        freq = device_cfg['frequency_ms']
        if not (20 <= freq <= 100):
            print(f"Помилка конфігурації: частота {freq} ms не в діапазоні 20-100 ms.")
            exit()

    tasks = []
    for device_cfg in config['devices']:
        # Створюємо завдання для кожного датчика
        task = asyncio.create_task(device_emulator(device_cfg))
        tasks.append(task)
    
    print("Усі емулятори пристроїв запущені.")
    
    # Чекаємо завершення всіх завдань (нескінченний цикл)
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    import time
    try:
        # Запуск асинхронного циклу
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nЕмулятори зупинено.")
