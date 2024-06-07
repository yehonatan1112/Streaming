from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from kafka import KafkaConsumer
import json
from pymongo import MongoClient
import pytz

app = Flask(__name__)
socketio = SocketIO(app)

# Initialize MongoDB client
client = MongoClient('mongodb://localhost:27017/')
db = client['video_streams']
collection = db['frames']

consumer = KafkaConsumer(
    'video-stream',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

israeli_tz = pytz.timezone('Asia/Jerusalem')

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/history')
def history():
    uuid = request.args.get('uuid')
    frames = list(collection.find({'uuid': uuid}))

    # Convert ObjectId to string
    for frame in frames:
        frame['_id'] = str(frame['_id'])

    return jsonify(frames)


def consume_kafka():
    for message in consumer:
        try:
            # Save message to the database
            collection.insert_one(message.value)

            # Send message to the frontend
            socketio.emit('video_frame', message.value)
        except Exception as e:
            print(f"Error processing Kafka message: {e}")


@socketio.on('connect')
def handle_connect():
    print('Client connected')


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


if __name__ == '__main__':
    socketio.start_background_task(target=consume_kafka)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)