import tkinter as tk
from PIL import Image, ImageTk
import uuid
from kafka import KafkaProducer
import json
import cv2
import base64


class VideoStreamingApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Video Streaming App")

        self.camera_uuid = str(uuid.uuid4())

        # Initialize Kafka producer
        self.producer = KafkaProducer(bootstrap_servers='localhost:9092',
                                      value_serializer=lambda v: json.dumps(v).encode('utf-8'))

        # Create GUI elements
        self.label = tk.Label(master)
        self.label.pack()

        self.start_button = tk.Button(master, text="Start Streaming", command=self.start_streaming)
        self.start_button.pack()

        self.stop_button = tk.Button(master, text="Stop Streaming", command=self.stop_streaming, state=tk.DISABLED)
        self.stop_button.pack()

        self.quit_button = tk.Button(master, text="Quit", command=self.quit)
        self.quit_button.pack()

        # Initialize video capture
        self.cap = None
        self.streaming = False

    def start_streaming(self):
        self.streaming = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        # Reinitialize video capture
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)

        self.capture_frame()

    def capture_frame(self):
        if self.streaming:
            ret, frame = self.cap.read()
            if ret:
                # Encode frame as PNG and then as base64
                _, buffer = cv2.imencode('.png', frame)
                png_as_base64 = base64.b64encode(buffer)

                # Create message
                message = {
                    'uuid': self.camera_uuid,
                    'frame': png_as_base64.decode('utf-8')
                }

                # Send message to Kafka
                self.producer.send('video-stream', message)

                # Convert frame to ImageTk format and update label
                imgtk = self.convert_frame_to_imgtk(frame)
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
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def quit(self):
        self.stop_streaming()
        self.master.quit()

    @staticmethod
    def convert_frame_to_imgtk(frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        return imgtk


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoStreamingApp(root)
    print(app.camera_uuid)
    root.mainloop()
