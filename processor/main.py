import base64
import json
from google.cloud import firestore

# Ініціалізація клієнта Firestore
db = firestore.Client()

def process_iot_message(event, context):
    """
    Обробляє повідомлення, опубліковане в Pub/Sub.
    Це основна функція Cloud Function.
    
    Аргументи:
        event (dict): Вміст повідомлення Pub/Sub.
        context (google.cloud.functions.Context): Метадані.
    """
    
    # 1. Декодування вхідних даних (обов'язково для Pub/Sub тригера)
    if 'data' not in event:
        print("Помилка: Повідомлення не містить даних.")
        return
        
    try:
        # Дані закодовані в Base64
        data_bytes = base64.b64decode(event['data'])
        payload = json.loads(data_bytes.decode('utf-8'))
    except Exception as e:
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
        # Назва колекції (по суті, таблиці) в Firestore.
        # Кожен тип датчика матиме окрему колекцію для чистоти даних.
        collection_name = f'iot_readings_{device_type}'
        
        # Записуємо дані у відповідну колекцію
        db.collection(collection_name).add(data_to_save)
        
        print(f"Дані успішно збережено у колекції: {collection_name}")
    except Exception as e:
        print(f"Помилка при збереженні у Firestore: {e}")
