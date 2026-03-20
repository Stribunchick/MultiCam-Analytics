import queue
import numpy as np

from PySide6.QtWidgets import QWidget, QLabel, QGridLayout
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPixmap, QImage

class VideoWall(QWidget):
    def __init__(self, render_queues: dict, cam_ids, cameras_per_row=4, fps=15):
        super().__init__()

        
        self.cam_ids = cam_ids
        self.render_queues = render_queues
        # последнее состояние на камеру
        self.last_frames = {cam_id: None for cam_id in cam_ids}

        # UI
        layout = QGridLayout()
        layout.setSpacing(2)
        self.setLayout(layout)

        self.labels = {}

        for idx, cam_id in enumerate(cam_ids):
            lbl = QLabel()
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setScaledContents(True)

            self.labels[cam_id] = lbl

            row = idx // cameras_per_row
            col = idx % cameras_per_row
            layout.addWidget(lbl, row, col)

        # фиксированный FPS UI
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(int(1000 / fps))
        print("RENDER INIT")

    def update_ui(self):
        packets = []
        for rq in self.render_queues.values():
            try:
                packet = rq.get_nowait()
                packets.append(packet)
            except queue.Empty:
                continue
        for packet in packets:
            cam_id = packet["frame"].cam_id
            frame = packet["frame"].image
            qimg = self.numpy_bgr_to_qimage(frame)
            pix = QPixmap.fromImage(qimg)
            self.labels[cam_id].setPixmap(pix)

    @staticmethod
    def numpy_bgr_to_qimage(frame_bgr: np.ndarray) -> QImage:
        """
            Zero-copy конвертация BGR numpy → QImage
            """
        h, w, ch = frame_bgr.shape
        rgb = np.ascontiguousarray(frame_bgr[:, :, ::-1])

        return QImage(
            rgb.data,
            w,
            h,
            ch * w,
            QImage.Format.Format_RGB888,
        )