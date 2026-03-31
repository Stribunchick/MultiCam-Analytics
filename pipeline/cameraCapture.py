import threading
import queue
import cv2
import time
from pipeline.frameClass import Frame


class CameraCapture(threading.Thread):
    def __init__(self, camera_path, to_process_queue, cam_id, fps):
        super().__init__()
        self.camera_path = camera_path
        self.stop_evt = threading.Event()
        self.to_process_queue = to_process_queue
        self.cam_id = cam_id
        self.fps = fps
        print(f"CAMERACAPTURE [{cam_id}] INIT")
        
        
    def run(self):
        cap = cv2.VideoCapture(self.camera_path, cv2.CAP_FFMPEG)
        
        frame_interval = 1.0 / self.fps
        last_emit = 0
        while not self.stop_evt.is_set():
            ok, frame = cap.read() # Get the image
            if not ok:
                continue
            now = time.time()

            if now - last_emit < frame_interval:
                continue

            last_emit = now

            packet = Frame(frame, self.cam_id) # Pack the frame into a class

            try:
                self.to_process_queue.put_nowait(packet) # Send frame
            except:
                self.to_process_queue.get_nowait()
                self.to_process_queue.put_nowait(packet)

        cap.release()
    def stop(self):
        self.stop_evt.set()
            