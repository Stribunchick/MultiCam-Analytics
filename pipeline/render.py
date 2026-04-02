import queue
import numpy as np

from PySide6.QtCore import QPoint, QRect, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QGridLayout, QLabel, QWidget


class CameraView(QLabel):
    roi_changed = Signal(int, object)

    def __init__(self, cam_id, roi_state):
        super().__init__()
        self.cam_id = cam_id
        self.roi_state = roi_state
        self.current_roi = self._read_roi()
        self.drag_start = None
        self.drag_current = None

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setScaledContents(True)
        self.setMouseTracking(True)
        self.setMinimumSize(320, 180)
        self.setToolTip("Left drag: set ROI, right click: clear ROI")

    def _read_roi(self):
        roi = self.roi_state.get(self.cam_id)
        if roi is None:
            return None
        return tuple(float(value) for value in roi)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            point = self._clamp_point(event.position().toPoint())
            self.drag_start = point
            self.drag_current = point
            self.update()
            event.accept()
            return

        if event.button() == Qt.MouseButton.RightButton:
            self._set_roi(None)
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.drag_start is None:
            super().mouseMoveEvent(event)
            return

        self.drag_current = self._clamp_point(event.position().toPoint())
        self.update()
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton or self.drag_start is None:
            super().mouseReleaseEvent(event)
            return

        self.drag_current = self._clamp_point(event.position().toPoint())
        rect = QRect(self.drag_start, self.drag_current).normalized()
        roi = self._normalized_roi_from_rect(rect)

        if roi is not None:
            self._set_roi(roi)

        self.drag_start = None
        self.drag_current = None
        self.update()
        event.accept()

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.current_roi is not None:
            painter.setPen(QPen(QColor(0, 255, 255), 2))
            painter.drawRect(self._rect_from_roi(self.current_roi))

        if self.drag_start is not None and self.drag_current is not None:
            painter.setPen(QPen(QColor(255, 215, 0), 2, Qt.PenStyle.DashLine))
            painter.drawRect(QRect(self.drag_start, self.drag_current).normalized())

        painter.end()

    def _set_roi(self, roi):
        self.current_roi = roi
        self.roi_state[self.cam_id] = roi
        self.roi_changed.emit(self.cam_id, roi)
        self.update()

    def _normalized_roi_from_rect(self, rect):
        bounds = self.contentsRect()
        if bounds.width() <= 0 or bounds.height() <= 0:
            return None

        if rect.width() < 10 or rect.height() < 10:
            return None

        x1 = max(0.0, min(1.0, (rect.left() - bounds.left()) / bounds.width()))
        y1 = max(0.0, min(1.0, (rect.top() - bounds.top()) / bounds.height()))
        x2 = max(0.0, min(1.0, (rect.right() - bounds.left()) / bounds.width()))
        y2 = max(0.0, min(1.0, (rect.bottom() - bounds.top()) / bounds.height()))

        if x2 <= x1 or y2 <= y1:
            return None

        return (x1, y1, x2, y2)

    def _rect_from_roi(self, roi):
        bounds = self.contentsRect()
        x1, y1, x2, y2 = roi
        left = bounds.left() + int(round(x1 * bounds.width()))
        top = bounds.top() + int(round(y1 * bounds.height()))
        right = bounds.left() + int(round(x2 * bounds.width()))
        bottom = bounds.top() + int(round(y2 * bounds.height()))
        return QRect(QPoint(left, top), QPoint(right, bottom)).normalized()

    def _clamp_point(self, point):
        bounds = self.contentsRect()
        if bounds.width() <= 0 or bounds.height() <= 0:
            return QPoint(0, 0)

        x = min(max(point.x(), bounds.left()), bounds.right())
        y = min(max(point.y(), bounds.top()), bounds.bottom())
        return QPoint(x, y)


class VideoWall(QWidget):
    destroyed = Signal()

    def __init__(self, render_queues: dict, cam_ids, roi_state, cameras_per_row=4, fps=15):
        super().__init__()

        self.cam_ids = cam_ids
        self.render_queues = render_queues
        self.roi_state = roi_state
        self.last_frames = {cam_id: None for cam_id in cam_ids}

        layout = QGridLayout()
        layout.setSpacing(2)
        self.setLayout(layout)

        self.labels = {}

        for idx, cam_id in enumerate(cam_ids):
            lbl = CameraView(cam_id, roi_state)
            self.labels[cam_id] = lbl

            row = idx // cameras_per_row
            col = idx % cameras_per_row
            layout.addWidget(lbl, row, col)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(int(1000 / fps))
        print("RENDER INIT")

    def update_ui(self):
        for cam_id, rq in self.render_queues.items():
            packet = None
            while True:
                try:
                    packet = rq.get_nowait()
                except queue.Empty:
                    break

            if packet is None:
                continue

            frame = packet["frame"].image
            qimg = self.numpy_bgr_to_qimage(frame)
            pix = QPixmap.fromImage(qimg)
            self.last_frames[cam_id] = pix
            self.labels[cam_id].setPixmap(pix)

    @staticmethod
    def numpy_bgr_to_qimage(frame_bgr: np.ndarray) -> QImage:
        h, w, ch = frame_bgr.shape
        rgb = np.ascontiguousarray(frame_bgr[:, :, ::-1])

        return QImage(
            rgb.data,
            w,
            h,
            ch * w,
            QImage.Format.Format_RGB888,
        )

    def closeEvent(self, event):
        print("Window closing")
        self.destroyed.emit()
        event.accept()
