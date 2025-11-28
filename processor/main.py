import base64
import json
import os
from flask import Flask, request, jsonify, render_template_string
from google.cloud import firestore

app = Flask(__name__)
db = firestore.Client()
COLLECTION_NAME = 'iot_data'

# HTML-шаблон прямо в коді (щоб не створювати зайві файли)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>IoT Dashboard</title>
    <meta http-equiv="refresh" content="5"> <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; padding: 20px; }
        .card { box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        .temp-high { color: red; font-weight: bold; }
        .temp-norm { color: green; }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="mb-4 text-center">🎛️ IoT Control Center</h1>
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Live Sensor Data</h5>
                <table class="table table-hover">
                    <thead class="table-dark">
                        <tr>
                            <th>Time</th>
                            <th>Sensor Type</th>
                            <th>Location</th>
                            <th>Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for item in data %}
                        <tr>
                            <td>{{ item.timestamp }}</td>
                            <td>
                                <span class="badge bg-primary">{{ item.sensor_type }}</span>
                            </td>
                            <td>{{ item.location }}</td>
                            <td>
                                <strong>{{ item.value }} {{ item.unit }}</strong>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        <div class="text-center mt-3 text-muted">
            Auto-refreshing every 5 seconds...
        </div>
    </div>
</body>
</html>
"""

@app.route('/', methods=['POST'])
def receive_pubsub_message():
    envelope = request.get_json()
    if not envelope: return 'No message', 400
    if 'message' not in envelope: return 'Invalid', 400

    pubsub_message = envelope['message']
    if 'data' in pubsub_message:
        try:
            data_str = base64.b64decode(pubsub_message['data']).decode('utf-8')
            sensor_data = json.loads(data_str)
            sensor_data['server_processed_at'] = firestore.SERVER_TIMESTAMP
            db.collection(COLLECTION_NAME).add(sensor_data)
            return 'OK', 200
        except Exception as e:
            return f'Error: {e}', 500
    return 'No data', 400

@app.route('/history', methods=['GET'])
def get_history():
    docs = db.collection(COLLECTION_NAME).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(20).stream()
    history = [doc.to_dict() for doc in docs]
    return jsonify(history), 200

@app.route('/dashboard', methods=['GET'])
def dashboard():
    docs = db.collection(COLLECTION_NAME).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(20).stream()
    history = [doc.to_dict() for doc in docs]
    return render_template_string(HTML_TEMPLATE, data=history)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
