import threading
import queue
import cv2
import time

from pipeline.runtime_metrics import capture_key, now_iso
from pipeline.frameClass import Frame


class CameraCapture(threading.Thread):
    def __init__(self, camera_path, to_process_queue, cam_id, fps, metrics_state=None):
        super().__init__(daemon=True)
        self.camera_path = camera_path
        self.stop_evt = threading.Event()
        self.to_process_queue = to_process_queue
        self.cam_id = cam_id
        self.fps = fps
        self.metrics_state = metrics_state
        self.cap = None
        print(f"CAMERACAPTURE [{cam_id}] INIT")

    def _open_capture(self):
        cap = cv2.VideoCapture()

        # Ask FFmpeg/OpenCV to fail reads quickly during shutdown instead of
        # blocking for a long time inside read().
        params = []
        if hasattr(cv2, "CAP_PROP_OPEN_TIMEOUT_MSEC"):
            params.extend([cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 2000])
        if hasattr(cv2, "CAP_PROP_READ_TIMEOUT_MSEC"):
            params.extend([cv2.CAP_PROP_READ_TIMEOUT_MSEC, 1000])
        if hasattr(cv2, "CAP_PROP_BUFFERSIZE"):
            params.extend([cv2.CAP_PROP_BUFFERSIZE, 1])

        try:
            if hasattr(cap, "setExceptionMode"):
                cap.setExceptionMode(True)
        except Exception:
            pass

        opened = False
        if params:
            try:
                opened = cap.open(self.camera_path, cv2.CAP_FFMPEG, params)
            except TypeError:
                opened = False
            except cv2.error:
                opened = False

        if not opened:
            try:
                opened = cap.open(self.camera_path, cv2.CAP_FFMPEG)
            except cv2.error:
                opened = False

        return cap

    def run(self):
        self.cap = self._open_capture()
        cap = self.cap
        
        frame_interval = 1.0 / self.fps
        last_emit = 0
        emitted_frames_total = 0
        queue_drops = 0
        read_errors = 0
        emitted_since_report = 0
        last_report_at = time.monotonic()

        while not self.stop_evt.is_set():
            try:
                ok, frame = cap.read() # Get the image
            except cv2.error:
                if self.stop_evt.is_set():
                    break
                read_errors += 1
                self._maybe_publish_metrics(
                    emitted_frames_total,
                    queue_drops,
                    read_errors,
                    emitted_since_report,
                    last_emit,
                    last_report_at,
                )
                time.sleep(0.02)
                continue
            except Exception:
                if self.stop_evt.is_set():
                    break
                read_errors += 1
                self._maybe_publish_metrics(
                    emitted_frames_total,
                    queue_drops,
                    read_errors,
                    emitted_since_report,
                    last_emit,
                    last_report_at,
                )
                time.sleep(0.02)
                continue

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

        try:
            cap.release()
        except Exception:
            pass
        self.cap = None

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
            
