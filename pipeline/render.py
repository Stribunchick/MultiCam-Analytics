import queue
import time

import numpy as np

from PySide6.QtCore import QPoint, QRect, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pipeline.runtime_metrics import (
    INFERENCE_KEY,
    POSTPROCESS_KEY,
    PREPROCESS_KEY,
    SESSION_KEY,
    capture_key,
    display_key,
    now_iso,
    output_key,
)


class CameraView(QLabel):
    roi_changed = Signal(int, object)

    def __init__(self, cam_id, roi_state):
        super().__init__()
        self.cam_id = cam_id
        self.roi_state = roi_state
        self.current_roi = self._read_roi()
        self.drag_start = None
        self.drag_current = None

        self.setObjectName("cameraTile")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setScaledContents(True)
        self.setMouseTracking(True)
        self.setMinimumSize(320, 180)
        self.setText(f"Камера {cam_id}")
        self.setToolTip("Левая кнопка: выделить ROI, правая кнопка: очистить ROI")

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
    roi_changed = Signal(int, object)
    analytics_requested = Signal()

    def __init__(
        self,
        render_queues: dict,
        cam_ids,
        roi_state,
        cameras_per_row=4,
        fps=15,
        metrics_state=None,
        camera_names=None,
    ):
        super().__init__()

        self.cam_ids = cam_ids
        self.render_queues = render_queues
        self.roi_state = roi_state
        self.metrics_state = metrics_state
        self.camera_names = camera_names or {
            cam_id: f"Camera {cam_id}"
            for cam_id in cam_ids
        }
        self.last_frames = {cam_id: None for cam_id in cam_ids}
        self.display_stats = {
            cam_id: {
                "frames_total": 0,
                "frames_since_report": 0,
                "fps": 0.0,
                "last_report_at": time.monotonic(),
            }
            for cam_id in cam_ids
        }

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(10)

        self.metrics_toggle_button = QPushButton("Показать метрики")
        self.metrics_toggle_button.clicked.connect(self._toggle_metrics_panel)
        controls_layout.addWidget(self.metrics_toggle_button, 0, Qt.AlignmentFlag.AlignLeft)

        self.analytics_button = QPushButton("Аналитика")
        self.analytics_button.setProperty("variant", "secondary")
        self.analytics_button.clicked.connect(self._request_analytics)
        self.analytics_button.style().unpolish(self.analytics_button)
        self.analytics_button.style().polish(self.analytics_button)
        controls_layout.addWidget(self.analytics_button, 0, Qt.AlignmentFlag.AlignLeft)

        controls_layout.addStretch(1)
        root.addLayout(controls_layout)

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)
        root.addLayout(content_layout, 1)

        self.metrics_panel = self._build_metrics_panel()
        self.metrics_panel.hide()

        video_container = QWidget()
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        video_container.setLayout(layout)
        content_layout.addWidget(video_container, 1)
        content_layout.addWidget(self.metrics_panel, 0)

        self.labels = {}

        for idx, cam_id in enumerate(cam_ids):
            label = CameraView(cam_id, roi_state)
            label.roi_changed.connect(self._on_roi_changed)
            self.labels[cam_id] = label

            row = idx // cameras_per_row
            col = idx % cameras_per_row
            layout.addWidget(label, row, col)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(int(1000 / fps))

        self.metrics_timer = QTimer(self)
        self.metrics_timer.timeout.connect(self.refresh_metrics)
        self.metrics_timer.start(500)
        self.refresh_metrics()
        print("RENDER INIT")

    def _build_metrics_panel(self):
        panel = QWidget()
        panel.setMinimumWidth(360)
        panel.setMaximumWidth(420)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        summary_box = QGroupBox("Состояние системы")
        summary_grid = QGridLayout(summary_box)
        summary_grid.setSpacing(8)

        self.session_value = QLabel("-")
        self.pipeline_value = QLabel("-")
        self.batch_value = QLabel("-")
        self.gpu_value = QLabel("-")
        self.drops_value = QLabel("-")
        self.tracks_value = QLabel("-")

        summary_grid.addWidget(QLabel("Сессия"), 0, 0)
        summary_grid.addWidget(self.session_value, 0, 1)
        summary_grid.addWidget(QLabel("Пайплайн"), 1, 0)
        summary_grid.addWidget(self.pipeline_value, 1, 1)
        summary_grid.addWidget(QLabel("Батчи"), 2, 0)
        summary_grid.addWidget(self.batch_value, 2, 1)
        summary_grid.addWidget(QLabel("GPU"), 3, 0)
        summary_grid.addWidget(self.gpu_value, 3, 1)
        summary_grid.addWidget(QLabel("Дропы"), 4, 0)
        summary_grid.addWidget(self.drops_value, 4, 1)
        summary_grid.addWidget(QLabel("Треки"), 5, 0)
        summary_grid.addWidget(self.tracks_value, 5, 1)

        layout.addWidget(summary_box)

        cameras_box = QGroupBox("Метрики по камерам")
        cameras_layout = QVBoxLayout(cameras_box)
        self.metrics_table = QTableWidget()
        self.metrics_table.setColumnCount(8)
        self.metrics_table.setHorizontalHeaderLabels([
            "Камера",
            "In FPS",
            "Out FPS",
            "UI FPS",
            "In drops",
            "Out drops",
            "Read err",
            "Tracks",
        ])
        header = self.metrics_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in range(1, 8):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        self.metrics_table.verticalHeader().setVisible(False)
        self.metrics_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        cameras_layout.addWidget(self.metrics_table)
        layout.addWidget(cameras_box, 1)

        return panel

    def update_ui(self):
        for cam_id, render_queue in self.render_queues.items():
            packet = None
            while True:
                try:
                    packet = render_queue.get_nowait()
                except queue.Empty:
                    break

            if packet is None:
                continue

            frame = packet["frame"].image
            qimg = self.numpy_bgr_to_qimage(frame)
            pixmap = QPixmap.fromImage(qimg)
            self.last_frames[cam_id] = pixmap
            self.labels[cam_id].setPixmap(pixmap)
            self._update_display_metrics(cam_id)

    def _update_display_metrics(self, cam_id):
        if self.metrics_state is None:
            return

        stats = self.display_stats[cam_id]
        stats["frames_total"] += 1
        stats["frames_since_report"] += 1

        now_monotonic = time.monotonic()
        report_interval = now_monotonic - stats["last_report_at"]
        if report_interval < 1.0:
            return

        stats["fps"] = stats["frames_since_report"] / max(report_interval, 1e-6)
        self.metrics_state[display_key(cam_id)] = {
            "camera_id": cam_id,
            "camera_name": self.camera_names.get(cam_id, f"Camera {cam_id}"),
            "fps": round(stats["fps"], 2),
            "frames_total": stats["frames_total"],
            "updated_at": now_iso(),
        }
        stats["frames_since_report"] = 0
        stats["last_report_at"] = now_monotonic

    def refresh_metrics(self):
        if self.metrics_state is None:
            return

        session = dict(self.metrics_state.get(SESSION_KEY, {}))
        preprocess = dict(self.metrics_state.get(PREPROCESS_KEY, {}))
        inference = dict(self.metrics_state.get(INFERENCE_KEY, {}))
        postprocess = dict(self.metrics_state.get(POSTPROCESS_KEY, {}))

        capture_metrics = {
            cam_id: dict(self.metrics_state.get(capture_key(cam_id), {}))
            for cam_id in self.cam_ids
        }
        output_metrics = {
            cam_id: dict(self.metrics_state.get(output_key(cam_id), {}))
            for cam_id in self.cam_ids
        }
        display_metrics = {
            cam_id: dict(self.metrics_state.get(display_key(cam_id), {}))
            for cam_id in self.cam_ids
        }

        total_capture_fps = sum(item.get("fps", 0.0) for item in capture_metrics.values())
        total_output_fps = sum(item.get("fps", 0.0) for item in output_metrics.values())
        total_display_fps = sum(item.get("fps", 0.0) for item in display_metrics.values())
        total_input_drops = sum(item.get("queue_drops", 0) for item in capture_metrics.values())
        total_output_drops = sum(item.get("queue_drops", 0) for item in output_metrics.values())
        total_read_errors = sum(item.get("read_errors", 0) for item in capture_metrics.values())

        self.session_value.setText(
            f"{session.get('status', '-')}"
            f"\nКамер: {session.get('camera_count', 0)}"
            f"\nМоделей: {session.get('model_count', 0)}"
            f"\nTarget FPS: {session.get('target_fps', 0)}"
        )
        self.pipeline_value.setText(
            f"Capture: {total_capture_fps:.1f}"
            f"\nPre: {preprocess.get('fps', 0.0):.1f}"
            f"\nInfer: {inference.get('fps', 0.0):.1f}"
            f"\nPost/UI: {postprocess.get('fps', 0.0):.1f}/{total_display_fps:.1f}"
        )
        self.batch_value.setText(
            f"Cfg: {session.get('configured_batch_size', 0)}"
            f"\nLast: {preprocess.get('last_batch_size', 0)}"
            f"\nAvg: {preprocess.get('avg_batch_size', 0.0)}"
            f"\nInfer ms: {inference.get('last_inference_ms', 0.0)}"
        )
        self.gpu_value.setText(
            f"Alloc: {inference.get('gpu_allocated_mb', 0.0)} MB"
            f"\nReserved: {inference.get('gpu_reserved_mb', 0.0)} MB"
            f"\nPeak: {inference.get('gpu_peak_mb', 0.0)} MB"
        )
        self.drops_value.setText(
            f"In: {total_input_drops}"
            f"\nTensor: {preprocess.get('queue_overwrites', 0)}"
            f"\nResult: {inference.get('queue_drops', 0)}"
            f"\nOut: {total_output_drops}"
        )
        self.tracks_value.setText(
            f"Visible: {postprocess.get('visible_tracks', 0)}"
            f"\nActive: {postprocess.get('active_tracks', 0)}"
            f"\nRead err: {total_read_errors}"
            f"\nOut FPS: {total_output_fps:.1f}"
        )

        self._fill_camera_metrics_table(capture_metrics, output_metrics, display_metrics)

    def _fill_camera_metrics_table(self, capture_metrics, output_metrics, display_metrics):
        self.metrics_table.setRowCount(len(self.cam_ids))

        for row, cam_id in enumerate(self.cam_ids):
            capture = capture_metrics.get(cam_id, {})
            output = output_metrics.get(cam_id, {})
            display = display_metrics.get(cam_id, {})
            camera_name = self.camera_names.get(cam_id, f"Camera {cam_id}")
            values = [
                camera_name,
                f"{capture.get('fps', 0.0):.1f}",
                f"{output.get('fps', 0.0):.1f}",
                f"{display.get('fps', 0.0):.1f}",
                str(capture.get("queue_drops", 0)),
                str(output.get("queue_drops", 0)),
                str(capture.get("read_errors", 0)),
                str(output.get("active_tracks", 0)),
            ]
            for col, value in enumerate(values):
                self.metrics_table.setItem(row, col, QTableWidgetItem(value))

    def _toggle_metrics_panel(self):
        if self.metrics_panel.isVisible():
            self.metrics_panel.hide()
            self.metrics_toggle_button.setText("Показать метрики")
            return

        self.metrics_panel.show()
        self.metrics_toggle_button.setText("Скрыть метрики")
        self.refresh_metrics()

    def _request_analytics(self):
        self.analytics_requested.emit()

    def _on_roi_changed(self, cam_id, roi):
        self.roi_changed.emit(cam_id, roi)

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
