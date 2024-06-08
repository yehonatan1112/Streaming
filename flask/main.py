# server.py
from flask import Flask, jsonify, request, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from kafka import KafkaConsumer
import json

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
KAFKA_TOPIC = 'video-stream'

consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

frame_history = []

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/history')
def history():
    return jsonify(frame_history)

def consume_kafka():
    for message in consumer:
        try:
            frame_data = {
                'frame': message.value['frame'],
                'timestamp': message.timestamp
            }
            frame_history.append(frame_data)
            # Send message to the frontend
            socketio.emit('video_frame', message.value)
        except Exception as e:
            print(f"Error processing Kafka message: {e}")

if __name__ == '__main__':
    socketio.start_background_task(target=consume_kafka)
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
