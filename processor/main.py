import base64
import json
import os
from flask import Flask, request, jsonify
from google.cloud import firestore

app = Flask(__name__)

# Підключаємось до бази даних
db = firestore.Client()
COLLECTION_NAME = 'iot_data'

@app.route('/', methods=['POST'])
def receive_pubsub_message():
    """Ця функція приймає повідомлення від Pub/Sub (Push subscription)"""
    envelope = request.get_json()
    if not envelope:
        return 'No Pub/Sub message received', 400

    if not isinstance(envelope, dict) or 'message' not in envelope:
        return 'Invalid Pub/Sub message format', 400

    # Pub/Sub надсилає дані у полі message -> data (закодовані в base64)
    pubsub_message = envelope['message']

    if isinstance(pubsub_message, dict) and 'data' in pubsub_message:
        try:
            # Розкодовуємо дані
            data_str = base64.b64decode(pubsub_message['data']).decode('utf-8')
            sensor_data = json.loads(data_str)
            
            # Додаємо час отримання сервером (server_time)
            sensor_data['server_processed_at'] = firestore.SERVER_TIMESTAMP

            # ЗАПИС У БАЗУ ДАНИХ (Firestore)
            db.collection(COLLECTION_NAME).add(sensor_data)
            
            print(f"Saved to DB: {sensor_data}")
            return 'OK', 200
        except Exception as e:
            print(f"Error processing message: {e}")
            return f'Error: {e}', 500

    return 'No data found in message', 400

@app.route('/history', methods=['GET'])
def get_history():
    """Бонус: REST API для отримання історії"""
    try:
        # Беремо останні 20 записів, відсортовані за часом
        docs = db.collection(COLLECTION_NAME)\
                 .order_by('timestamp', direction=firestore.Query.DESCENDING)\
                 .limit(20)\
                 .stream()

        history = []
        for doc in docs:
            history.append(doc.to_dict())

        return jsonify(history), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
