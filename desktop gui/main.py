import tkinter as tk
from PIL import Image, ImageTk
import uuid
from kafka import KafkaProducer
import json
from datetime import datetime
import pytz
import cv2
import numpy as np

class VideoStreamingApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Video Streaming App")

        self.camera_uuid = str(uuid.uuid4())

        # Initialize Kafka producer
        self.producer = KafkaProducer(bootstrap_servers='localhost:9092',
                                      value_serializer=lambda v: json.dumps(v).encode('utf-8'))

        self.israeli_tz = pytz.timezone('Asia/Jerusalem')

        # Create GUI elements
        self.label = tk.Label(master)
        self.label.pack()

        self.start_button = tk.Button(master, text="Start Streaming", command=self.start_streaming)
        self.start_button.pack()

        self.stop_button = tk.Button(master, text="Stop Streaming", command=self.stop_streaming, state=tk.DISABLED)
        self.stop_button.pack()

        self.quit_button = tk.Button(master, text="Quit", command=master.quit)
        self.quit_button.pack()

        # Initialize video capture
        self.cap = cv2.VideoCapture(0)
        self.streaming = False

    def start_streaming(self):
        self.streaming = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.capture_frame()

    def capture_frame(self):
        if self.streaming:
            ret, frame = self.cap.read()
            if ret:
                # Encode frame as JPEG
                _, buffer = cv2.imencode('.jpg', frame)
                jpg_as_text = buffer.tobytes()

                # Create message
                timestamp = datetime.now(self.israeli_tz).isoformat()
                message = {
                    'uuid': self.camera_uuid,
                    'timestamp': timestamp,
                    'frame': jpg_as_text.hex()
                }

                # Send message to Kafka
                self.producer.send('video-stream', message)

                # Convert frame to ImageTk format and update label
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(image=img)
                self.label.imgtk = imgtk
                self.label.config(image=imgtk)

                # Schedule the next frame capture
                self.master.after(10, self.capture_frame)
            else:
                self.stop_streaming()

    def stop_streaming(self):
        self.streaming = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

        # Release video capture
        self.cap.release()

        # Destroy OpenCV window (if it was created)
        cv2.destroyAllWindows()

def main():
    root = tk.Tk()
    app = VideoStreamingApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()