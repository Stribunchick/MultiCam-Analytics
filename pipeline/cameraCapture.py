import threading
import queue
import cv2
import time

from pipeline.runtime_metrics import capture_key, now_iso
from pipeline.frameClass import Frame


class CameraCapture(threading.Thread):
    def __init__(self, camera_path, to_process_queue, cam_id, fps, metrics_state=None):
        super().__init__()
        self.camera_path = camera_path
        self.stop_evt = threading.Event()
        self.to_process_queue = to_process_queue
        self.cam_id = cam_id
        self.fps = fps
        self.metrics_state = metrics_state
        print(f"CAMERACAPTURE [{cam_id}] INIT")
        
        
    def run(self):
        cap = cv2.VideoCapture(self.camera_path, cv2.CAP_FFMPEG)
        
        frame_interval = 1.0 / self.fps
        last_emit = 0
        emitted_frames_total = 0
        queue_drops = 0
        read_errors = 0
        emitted_since_report = 0
        last_report_at = time.monotonic()

        while not self.stop_evt.is_set():
            ok, frame = cap.read() # Get the image
            if not ok:
                read_errors += 1
                self._maybe_publish_metrics(
                    emitted_frames_total,
                    queue_drops,
                    read_errors,
                    emitted_since_report,
                    last_emit,
                    last_report_at,
                )
                if time.monotonic() - last_report_at >= 1.0:
                    emitted_since_report = 0
                    last_report_at = time.monotonic()
                time.sleep(0.02)
                continue
            now = time.time()

            if now - last_emit < frame_interval:
                continue

            last_emit = now

            packet = Frame(frame, self.cam_id) # Pack the frame into a class

            if self._put_latest_packet(packet):
                queue_drops += 1

            emitted_frames_total += 1
            emitted_since_report += 1

            if time.monotonic() - last_report_at >= 1.0:
                self._publish_metrics(
                    emitted_frames_total,
                    queue_drops,
                    read_errors,
                    emitted_since_report / max(time.monotonic() - last_report_at, 1e-6),
                    last_emit,
                )
                emitted_since_report = 0
                last_report_at = time.monotonic()

        cap.release()

    def _put_latest_packet(self, packet):
        try:
            self.to_process_queue.put_nowait(packet)
            return False
        except queue.Full:
            pass

        try:
            self.to_process_queue.get_nowait()
        except queue.Empty:
            pass

        try:
            self.to_process_queue.put_nowait(packet)
        except queue.Full:
            pass

        return True

    def _maybe_publish_metrics(
        self,
        emitted_frames_total,
        queue_drops,
        read_errors,
        emitted_since_report,
        last_emit,
        last_report_at,
    ):
        if time.monotonic() - last_report_at < 1.0:
            return

        self._publish_metrics(
            emitted_frames_total,
            queue_drops,
            read_errors,
            emitted_since_report / max(time.monotonic() - last_report_at, 1e-6),
            last_emit,
        )

    def _publish_metrics(self, emitted_frames_total, queue_drops, read_errors, fps, last_emit):
        if self.metrics_state is None:
            return

        self.metrics_state[capture_key(self.cam_id)] = {
            "camera_id": self.cam_id,
            "camera_name": self.metrics_state.get(capture_key(self.cam_id), {}).get(
                "camera_name",
                f"Camera {self.cam_id}",
            ),
            "fps": round(fps, 2),
            "frames_total": emitted_frames_total,
            "queue_drops": queue_drops,
            "read_errors": read_errors,
            "last_frame_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_emit)) if last_emit else "",
            "updated_at": now_iso(),
        }

    def stop(self):
        self.stop_evt.set()
            
