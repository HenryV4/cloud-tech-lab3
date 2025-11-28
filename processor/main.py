import base64
import json
from google.cloud import firestore
import os 

# --- КЕШУВАННЯ КЛІЄНТА FIRESTORE ---
# Це вирішує проблему падіння при холодному старті
cached_db_client = None

def get_db_client():
    """Повертає кешований клієнт Firestore, ініціалізуючи його при першому виклику."""
    global cached_db_client
    
    if cached_db_client is None:
        # Читаємо DB_ID зі змінної середовища. Вона має бути встановлена на "lab3-db"
        DB_ID = os.environ.get("DB_ID", "(default)")
        try:
            # Ініціалізуємо лише один раз
            cached_db_client = firestore.Client(database=DB_ID)
            print(f"Firestore Client initialized successfully for DB: {DB_ID}")
        except Exception as e:
            # Якщо ініціалізація падає, ми це залогіруємо
            print(f"!!! CRITICAL GLOBAL INIT ERROR: Failed to initialize Firestore Client: {e}")
            raise # Примусове падіння, якщо ініціалізація неможлива
    return cached_db_client

# --- ОСНОВНА ФУНКЦІЯ ОБРОБКИ ---

def generate_value(device_type):
    """(Просто заглушка для коректності)"""
    # Ми не використовуємо цей метод в обробнику, але залишаємо його для чистоти, якщо він потрібен в іншому місці
    return None 


def process_iot_message(event, context):
    """
    Обробляє повідомлення, опубліковане в Pub/Sub, і зберігає його у Firestore.
    """
    
    print("!!! FUNCTION STARTED SUCCESSFULLY !!!") # Це має з'явитися в логах

    # 1. Отримати клієнта (створюється при першому виклику)
    try:
        db = get_db_client()
    except Exception as e:
        print(f"FATAL: Cannot get Firestore client. Skipping message. Error: {e}")
        return # Зупиняємо обробку, якщо немає підключення до БД

    # 2. Декодування вхідних даних 
    if 'data' not in event:
        print("Error: Pub/Sub message contains no data.")
        return
        
    try:
        # Дані закодовані в Base64
        data_bytes = base64.b64decode(event['data'])
        payload = json.loads(data_bytes.decode('utf-8'))
    except Exception as e:
        print(f"Error decoding or parsing JSON from Pub/Sub: {e}")
        return
        
    # 3. Валідація та Обробка
    device_id = payload.get('device_id', 'unknown')
    device_type = payload.get('device_type', 'unknown')
    timestamp = payload.get('timestamp')
    value = payload.get('value')
    location = payload.get('location')
    
    if not all([device_id, device_type, timestamp, value]):
        print(f"Error: Incomplete data. Payload: {payload}")
        return

    print(f"Received data from {device_id} ({device_type}): Value {value}")

    # 4. Підготовка даних для зберігання
    data_to_save = {
        'device_id': device_id,
        'type': device_type,
        'value': value,
        'timestamp': firestore.SERVER_TIMESTAMP, # Використовуємо серверний час
        'sensor_time': timestamp, # Час, коли дані були згенеровані емулятором
        'location': location
    }
    
    # 5. Збереження в Базі Даних 
    try:
        # Колекція залежить від типу датчика
        collection_name = f'iot_readings_{device_type}'
        
        # Записуємо дані у відповідну колекцію
        db.collection(collection_name).add(data_to_save)
        
        print(f"Data successfully saved to collection: {collection_name}")
    except Exception as e:
        print(f"!!! CRITICAL: Error saving to Firestore. Check IAM permissions. Error: {e}")
        # Тут не використовуємо return, якщо ви налаштували Pub/Sub на повтор (хоча ми вимкнули його)
