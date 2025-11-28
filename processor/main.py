import base64
import json
from google.cloud import firestore
import os # ДОДАТИ: Імпорт модуля os

# Ініціалізація клієнта Firestore
# Читаємо DB_ID зі змінної середовища. Якщо не знайдено, використовуємо "(default)".
DB_ID = os.environ.get("DB_ID", "(default)") 
db = firestore.Client(database=DB_ID) # ВИКОРИСТОВУЄМО ЯВНИЙ ID

def process_iot_message(event, context):
    """
    Обробляє повідомлення, опубліковане в Pub/Sub.
    Це основна функція Cloud Function.
    
    Аргументи:
        event (dict): Вміст повідомлення Pub/Sub.
        context (google.cloud.functions.Context): Метадані.
    """
    
    print("!!! FUNCTION STARTED SUCCESSFULLY !!!") # <<< ДОДАТИ ЦЕЙ ЛОГ!

    # 1. Декодування вхідних даних (обов'язково для Pub/Sub тригера)
    if 'data' not in event:
        print("Помилка: Повідомлення не містить даних.")
        return
        
    try:
        # Дані закодовані в Base64
        data_bytes = base64.b64decode(event['data'])
        payload = json.loads(data_bytes.decode('utf-8'))
    except Exception as e:
        # Додати логування помилки декодування
        print(f"Помилка декодування або парсингу JSON: {e}")
        return
        
    # 2. Обробка та Валідація
    device_id = payload.get('device_id', 'unknown')
    device_type = payload.get('device_type', 'unknown')
    timestamp = payload.get('timestamp')
    value = payload.get('value')
    location = payload.get('location')
    
    if not all([device_id, device_type, timestamp, value]):
        print(f"Помилка: Неповні дані. Payload: {payload}")
        return

    print(f"Отримано дані від {device_id} ({device_type}): Значення {value}")

    # 3. Маршрутизація та Специфічна Обробка (Приклад)
    # Тут ми можемо додати логіку, специфічну для типу датчика
    
    data_to_save = {
        'device_id': device_id,
        'type': device_type,
        'value': value,
        'timestamp': firestore.SERVER_TIMESTAMP, # Використовуємо серверний час для точності
        'sensor_time': timestamp, # Час, коли дані були згенеровані емулятором
        'location': location
    }
    
    if device_type == 'temperature' and value > 28.0:
        print(f"!!! Аномалія: Висока температура ({value}) !!!")
        # Тут може бути логіка для надсилання сповіщення
        
    # 4. Збереження в Базі Даних (Завдання 4)
    try:
        # ... (Зберігання)
        db.collection(collection_name).add(data_to_save)
        # ...
    except Exception as e:
        # Додати логування помилки збереження
        print(f"!!! CRITICAL: Помилка при збереженні у Firestore: {e}")


