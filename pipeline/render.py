import queue
import time
from math import ceil

import numpy as np

from PySide6.QtCore import QPoint, QRect, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from gui.classDangerLevels import level_color, level_label
from pipeline.runtime_metrics import (
    DISPLAY_KEY,
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
        self.setScaledContents(False)
        self.setMouseTracking(True)
        self.setMinimumSize(280, 158)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
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


class CameraTile(QWidget):
    def __init__(self, cam_id, roi_state, camera_name):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        title = QLabel(camera_name)
        title.setObjectName("cameraTileTitle")
        layout.addWidget(title)

        self.view = CameraView(cam_id, roi_state)
        layout.addWidget(self.view, 1)

        self.counters_label = QLabel("Объекты: нет")
        self.counters_label.setObjectName("cameraCounters")
        self.counters_label.setWordWrap(True)
        self.counters_label.setMinimumHeight(34)
        layout.addWidget(self.counters_label)

    def set_counters(self, counters):
        if not counters:
            self.counters_label.setText("Объекты: нет")
            return

        parts = [
            f"{cls_name}: {count}"
            for cls_name, count in sorted(counters.items())
        ]
        self.counters_label.setText("Объекты: " + " | ".join(parts))


class PendingAlertWindow(QDialog):
    confirmed = Signal(str)
    rejected = Signal(str)

    def __init__(self, alert_id, alert_data, camera_name):
        super().__init__()
        self.alert_id = alert_id
        self.alert_data = dict(alert_data)
        self.camera_name = camera_name

        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setWindowTitle(f"{camera_name} - {self.alert_data.get('event_type', '')}")
        self.resize(920, 700)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        title = QLabel(f"{camera_name} - {self.alert_data.get('event_type', '')}")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        meta = QLabel(
            f"Начало: {self.alert_data.get('datetimeStart', '-')}\n"
            f"Уровень: {level_label(self.alert_data.get('danger_level'))}"
        )
        meta.setWordWrap(True)
        root.addWidget(meta)

        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setMinimumSize(640, 360)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(image_label)
        root.addWidget(scroll_area, 1)

        snapshot_path = self.alert_data.get("snapshot_path")
        pixmap = QPixmap(snapshot_path or "")
        if pixmap.isNull():
            image_label.setText("Снимок недоступен.")
        else:
            image_label.setPixmap(pixmap)
            image_label.adjustSize()

        buttons = QHBoxLayout()
        buttons.addStretch(1)

        reject_button = QPushButton("Ложное срабатывание")
        reject_button.setProperty("variant", "secondary")
        reject_button.clicked.connect(self._reject)
        buttons.addWidget(reject_button)

        confirm_button = QPushButton("Подтвердить тревогу")
        confirm_button.clicked.connect(self._confirm)
        buttons.addWidget(confirm_button)

        root.addLayout(buttons)

    def _confirm(self):
        self.confirmed.emit(self.alert_id)
        self.accept()

    def _reject(self):
        self.rejected.emit(self.alert_id)
        self.reject()


class VideoWall(QWidget):
    closing = Signal()
    roi_changed = Signal(int, object)
    analytics_requested = Signal()
    main_window_requested = Signal()

    def __init__(
        self,
        render_queues: dict,
        cam_ids,
        roi_state,
        cameras_per_row=4,
        fps=15,
        metrics_state=None,
        camera_names=None,
        alert_queue=None,
        alert_decisions=None,
        class_danger_levels=None,
    ):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
        self._is_closing = False

        self.cam_ids = cam_ids
        self.cameras_per_row = max(1, cameras_per_row)
        self.render_queues = render_queues
        self.roi_state = roi_state
        self.metrics_state = metrics_state
        self.camera_names = camera_names or {
            cam_id: f"Камера {cam_id}"
            for cam_id in cam_ids
        }
        self.alert_queue = alert_queue
        self.alert_decisions = alert_decisions
        self.class_danger_levels = class_danger_levels or {}
        self.pending_alerts = {}
        self.alert_review_windows = {}
        self.last_frames = {cam_id: None for cam_id in cam_ids}
        self.last_counters = {cam_id: {} for cam_id in cam_ids}
        self.display_stats = {
            cam_id: {
                "frames_total": 0,
                "frames_since_report": 0,
                "fps": 0.0,
                "last_render_ms": 0.0,
                "render_ms_sum": 0.0,
                "last_latency_ms": 0.0,
                "latency_ms_sum": 0.0,
                "max_latency_ms": 0.0,
                "last_report_at": time.monotonic(),
            }
            for cam_id in cam_ids
        }
        self.display_global_stats = {
            "frames_total": 0,
            "frames_since_report": 0,
            "last_render_ms": 0.0,
            "render_ms_sum": 0.0,
            "last_latency_ms": 0.0,
            "latency_ms_sum": 0.0,
            "max_latency_ms": 0.0,
            "last_report_at": time.monotonic(),
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

        self.main_window_button = QPushButton("Главное окно")
        self.main_window_button.setProperty("variant", "secondary")
        self.main_window_button.clicked.connect(self._request_main_window)
        self.main_window_button.style().unpolish(self.main_window_button)
        self.main_window_button.style().polish(self.main_window_button)
        controls_layout.addWidget(self.main_window_button, 0, Qt.AlignmentFlag.AlignLeft)

        self.alerts_toggle_button = QPushButton("Показать оповещения")
        self.alerts_toggle_button.setProperty("variant", "secondary")
        self.alerts_toggle_button.clicked.connect(self._toggle_alerts_panel)
        self.alerts_toggle_button.setEnabled(self.alert_queue is not None)
        self.alerts_toggle_button.style().unpolish(self.alerts_toggle_button)
        self.alerts_toggle_button.style().polish(self.alerts_toggle_button)
        controls_layout.addWidget(self.alerts_toggle_button, 0, Qt.AlignmentFlag.AlignLeft)

        controls_layout.addStretch(1)
        root.addLayout(controls_layout)

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)
        root.addLayout(content_layout, 1)

        self.metrics_panel = self._build_metrics_panel()
        self.metrics_panel.hide()
        self.alerts_panel = self._build_alerts_panel()
        if self.alert_queue is not None:
            self.alerts_panel.show()
            self.alerts_toggle_button.setText("Скрыть оповещения")
        else:
            self.alerts_panel.hide()

        video_container = QWidget()
        self.video_grid = QGridLayout()
        self.video_grid.setContentsMargins(0, 0, 0, 0)
        self.video_grid.setSpacing(10)
        video_container.setLayout(self.video_grid)

        video_scroll = QScrollArea()
        video_scroll.setWidgetResizable(True)
        video_scroll.setWidget(video_container)
        content_layout.addWidget(video_scroll, 1)
        content_layout.addWidget(self.metrics_panel, 0)
        content_layout.addWidget(self.alerts_panel, 0)

        self.labels = {}
        self.camera_tiles = {}

        for idx, cam_id in enumerate(cam_ids):
            tile = CameraTile(
                cam_id,
                roi_state,
                self.camera_names.get(cam_id, f"Камера {cam_id}"),
            )
            label = tile.view
            label.roi_changed.connect(self._on_roi_changed)
            self.labels[cam_id] = label
            self.camera_tiles[cam_id] = tile

            row = idx // self.cameras_per_row
            col = idx % self.cameras_per_row
            self.video_grid.addWidget(tile, row, col)

        for col in range(self.cameras_per_row):
            self.video_grid.setColumnStretch(col, 1)
        total_rows = max(1, ceil(len(cam_ids) / self.cameras_per_row))
        for row in range(total_rows):
            self.video_grid.setRowStretch(row, 1)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(int(1000 / fps))

        self.metrics_timer = QTimer(self)
        self.metrics_timer.timeout.connect(self.refresh_metrics)
        self.metrics_timer.start(500)
        self.alert_timer = QTimer(self)
        self.alert_timer.timeout.connect(self.refresh_alerts)
        self.alert_timer.start(250)
        self.refresh_metrics()
        self.refresh_alerts()
        print("RENDER INIT")

    def _build_metrics_panel(self):
        panel = QWidget()
        panel.setMinimumWidth(430)
        panel.setMaximumWidth(520)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        summary_box = QGroupBox("Состояние системы")
        summary_grid = QGridLayout(summary_box)
        summary_grid.setSpacing(8)

        self.session_value = QLabel("-")
        self.pipeline_value = QLabel("-")
        self.latency_value = QLabel("-")

        summary_grid.addWidget(QLabel("Сессия"), 0, 0)
        summary_grid.addWidget(self.session_value, 0, 1)
        summary_grid.addWidget(QLabel("Этапы, мс"), 1, 0)
        summary_grid.addWidget(self.pipeline_value, 1, 1)
        summary_grid.addWidget(QLabel("Задержка"), 2, 0)
        summary_grid.addWidget(self.latency_value, 2, 1)

        layout.addWidget(summary_box)

        self.metrics_table = None

        return panel

    def _build_alerts_panel(self):
        panel = QWidget()
        panel.setMinimumWidth(300)
        panel.setMaximumWidth(420)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        alerts_box = QGroupBox("Оповещения на подтверждение")
        alerts_layout = QVBoxLayout(alerts_box)

        self.alerts_summary_label = QLabel("Ожидают подтверждения: 0")
        alerts_layout.addWidget(self.alerts_summary_label)

        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(1)
        self.alerts_table.setHorizontalHeaderLabels([
            "Ожидающие тревоги",
        ])
        header = self.alerts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.alerts_table.verticalHeader().setVisible(False)
        self.alerts_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.alerts_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.alerts_table.cellClicked.connect(self._open_pending_snapshot_from_row)
        alerts_layout.addWidget(self.alerts_table)

        layout.addWidget(alerts_box, 1)
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

            if isinstance(packet, dict):
                frame_obj = packet["frame"]
                counters = dict(packet.get("counters") or {})
            else:
                frame_obj = packet
                counters = {}

            render_started_at = time.perf_counter()
            frame = frame_obj.image
            qimg = self.numpy_bgr_to_qimage(frame)
            pixmap = QPixmap.fromImage(qimg)
            self.last_frames[cam_id] = pixmap
            self.last_counters[cam_id] = counters
            self._apply_frame_to_label(cam_id)
            self.camera_tiles[cam_id].set_counters(counters)

            render_ms = (time.perf_counter() - render_started_at) * 1000.0
            latency_ms = 0.0
            captured_at_monotonic = getattr(frame_obj, "captured_at_monotonic", None)
            if captured_at_monotonic is not None:
                latency_ms = max(0.0, (time.monotonic() - captured_at_monotonic) * 1000.0)
            self._update_display_metrics(cam_id, render_ms, latency_ms)

    def _apply_frame_to_label(self, cam_id):
        pixmap = self.last_frames.get(cam_id)
        label = self.labels.get(cam_id)
        if pixmap is None or label is None:
            return

        target_size = label.size()
        if target_size.width() <= 1 or target_size.height() <= 1:
            label.setPixmap(pixmap)
            return

        scaled = pixmap.scaled(
            target_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        label.setPixmap(scaled)

    def _update_display_metrics(self, cam_id, render_ms, latency_ms):
        if self.metrics_state is None:
            return

        stats = self.display_stats[cam_id]
        stats["frames_total"] += 1
        stats["frames_since_report"] += 1
        stats["last_render_ms"] = render_ms
        stats["render_ms_sum"] += render_ms
        stats["last_latency_ms"] = latency_ms
        stats["latency_ms_sum"] += latency_ms
        stats["max_latency_ms"] = max(stats["max_latency_ms"], latency_ms)

        global_stats = self.display_global_stats
        global_stats["frames_total"] += 1
        global_stats["frames_since_report"] += 1
        global_stats["last_render_ms"] = render_ms
        global_stats["render_ms_sum"] += render_ms
        global_stats["last_latency_ms"] = latency_ms
        global_stats["latency_ms_sum"] += latency_ms
        global_stats["max_latency_ms"] = max(global_stats["max_latency_ms"], latency_ms)

        now_monotonic = time.monotonic()
        report_interval = now_monotonic - stats["last_report_at"]
        if report_interval >= 1.0:
            stats["fps"] = stats["frames_since_report"] / max(report_interval, 1e-6)
            self.metrics_state[display_key(cam_id)] = {
                "camera_id": cam_id,
                "camera_name": self.camera_names.get(cam_id, f"Камера {cam_id}"),
                "fps": round(stats["fps"], 2),
                "frames_total": stats["frames_total"],
                "last_render_ms": round(stats["last_render_ms"], 2),
                "avg_render_ms": round(stats["render_ms_sum"] / max(stats["frames_total"], 1), 2),
                "last_latency_ms": round(stats["last_latency_ms"], 2),
                "avg_latency_ms": round(stats["latency_ms_sum"] / max(stats["frames_total"], 1), 2),
                "max_latency_ms": round(stats["max_latency_ms"], 2),
                "updated_at": now_iso(),
            }
            stats["frames_since_report"] = 0
            stats["last_report_at"] = now_monotonic

        self._maybe_publish_global_display_metrics(now_monotonic)

    def _maybe_publish_global_display_metrics(self, now_monotonic):
        if self.metrics_state is None:
            return

        global_stats = self.display_global_stats
        report_interval = now_monotonic - global_stats["last_report_at"]
        if report_interval < 1.0:
            return

        fps = global_stats["frames_since_report"] / max(report_interval, 1e-6)
        self.metrics_state[DISPLAY_KEY] = {
            "frames_total": global_stats["frames_total"],
            "last_render_ms": round(global_stats["last_render_ms"], 2),
            "avg_render_ms": round(global_stats["render_ms_sum"] / max(global_stats["frames_total"], 1), 2),
            "last_latency_ms": round(global_stats["last_latency_ms"], 2),
            "avg_latency_ms": round(global_stats["latency_ms_sum"] / max(global_stats["frames_total"], 1), 2),
            "max_latency_ms": round(global_stats["max_latency_ms"], 2),
            "fps": round(fps, 2),
            "updated_at": now_iso(),
        }
        global_stats["frames_since_report"] = 0
        global_stats["last_report_at"] = now_monotonic

    def refresh_metrics(self):
        if self.metrics_state is None:
            return

        session = dict(self.metrics_state.get(SESSION_KEY, {}))
        preprocess = dict(self.metrics_state.get(PREPROCESS_KEY, {}))
        inference = dict(self.metrics_state.get(INFERENCE_KEY, {}))
        postprocess = dict(self.metrics_state.get(POSTPROCESS_KEY, {}))
        display_global = dict(self.metrics_state.get(DISPLAY_KEY, {}))

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

        total_display_fps = sum(item.get("fps", 0.0) for item in display_metrics.values())

        self.session_value.setText(
            f"Камер: {session.get('camera_count', 0)}"
            f"\nМоделей: {session.get('model_count', 0)}"
            f"\nFPS: {session.get('target_fps', 0)}"
        )
        self.pipeline_value.setText(
            f"Пре: {preprocess.get('last_batch_ms', 0.0)} / {preprocess.get('avg_batch_ms', 0.0)}"
            f"\nИнфер: {inference.get('last_inference_ms', 0.0)} / {inference.get('avg_inference_ms', 0.0)}"
            f"\nПост: {postprocess.get('last_packet_ms', 0.0)} / {postprocess.get('avg_packet_ms', 0.0)}"
        )
        self.latency_value.setText(
            f"Последняя: {display_global.get('last_latency_ms', 0.0)} мс"
            f"\nСредняя: {display_global.get('avg_latency_ms', 0.0)} мс"
            f"\nUI FPS: {total_display_fps:.1f}"
        )

        self._fill_camera_metrics_table(capture_metrics, output_metrics, display_metrics)

    def _fill_camera_metrics_table(self, capture_metrics, output_metrics, display_metrics):
        if self.metrics_table is None:
            return

        self.metrics_table.setRowCount(len(self.cam_ids))

        for row, cam_id in enumerate(self.cam_ids):
            capture = capture_metrics.get(cam_id, {})
            output = output_metrics.get(cam_id, {})
            display = display_metrics.get(cam_id, {})
            camera_name = self.camera_names.get(cam_id, f"Камера {cam_id}")
            values = [
                camera_name,
                f"{capture.get('fps', 0.0):.1f}",
                f"{output.get('fps', 0.0):.1f}",
                f"{display.get('fps', 0.0):.1f}",
                f"{display.get('last_render_ms', 0.0):.1f}",
                f"{display.get('last_latency_ms', 0.0):.1f}",
                f"{capture.get('queue_drops', 0)}/{output.get('queue_drops', 0)}",
                str(output.get("active_tracks", 0)),
            ]
            for col, value in enumerate(values):
                self.metrics_table.setItem(row, col, QTableWidgetItem(value))

    def refresh_alerts(self):
        if self.alert_queue is not None:
            while True:
                try:
                    alert = self.alert_queue.get_nowait()
                except queue.Empty:
                    break

                if not alert:
                    continue

                self.pending_alerts[alert["id"]] = dict(alert)

        self._fill_alerts_table()

    def _fill_alerts_table(self):
        alerts = sorted(
            self.pending_alerts.values(),
            key=lambda item: item.get("datetimeStart") or "",
            reverse=True,
        )
        self.alerts_summary_label.setText(f"Ожидают подтверждения: {len(alerts)}")
        self.alerts_table.clearContents()
        self.alerts_table.setRowCount(len(alerts))

        for row, alert in enumerate(alerts):
            alert_id = alert["id"]
            camera_name = self.camera_names.get(alert["cam_id"], f"Камера {alert['cam_id']}")
            item = QTableWidgetItem(f"{camera_name} - {alert.get('event_type', '')}")
            item.setData(Qt.ItemDataRole.UserRole, alert_id)
            item.setData(Qt.ItemDataRole.UserRole + 1, alert.get("snapshot_path"))
            item.setToolTip("Нажмите, чтобы открыть карточку тревоги")
            self._apply_alert_level_style(item, alert.get("danger_level"))
            self.alerts_table.setItem(row, 0, item)

        self.alerts_table.resizeRowsToContents()

    def _apply_alert_level_style(self, item, danger_level):
        if not danger_level:
            return

        background = QColor(level_color(danger_level))
        foreground = QColor("black") if background.lightness() > 150 else QColor("white")
        item.setBackground(background)
        item.setForeground(foreground)

    def _confirm_alert(self, alert_id):
        if self.alert_decisions is not None:
            self.alert_decisions[alert_id] = "confirm"
        self._close_alert_window(alert_id)
        self.pending_alerts.pop(alert_id, None)
        self._fill_alerts_table()

    def _reject_alert(self, alert_id):
        if self.alert_decisions is not None:
            self.alert_decisions[alert_id] = "reject"
        self._close_alert_window(alert_id)
        self.pending_alerts.pop(alert_id, None)
        self._fill_alerts_table()

    def _open_pending_snapshot_from_row(self, row, column):
        item = self.alerts_table.item(row, 0)
        if item is None:
            return

        alert_id = item.data(Qt.ItemDataRole.UserRole)
        if not alert_id:
            return

        alert = self.pending_alerts.get(alert_id)
        if alert is None:
            return

        existing = self.alert_review_windows.get(alert_id)
        if existing is not None:
            existing.raise_()
            existing.activateWindow()
            return

        camera_name = self.camera_names.get(alert["cam_id"], f"Камера {alert['cam_id']}")
        window = PendingAlertWindow(alert_id, alert, camera_name)
        window.confirmed.connect(self._confirm_alert)
        window.rejected.connect(self._reject_alert)
        window.destroyed.connect(lambda *_args, aid=alert_id: self._forget_alert_window(aid))
        self.alert_review_windows[alert_id] = window
        window.show()

    def _forget_alert_window(self, alert_id):
        self.alert_review_windows.pop(alert_id, None)

    def _close_alert_window(self, alert_id):
        window = self.alert_review_windows.pop(alert_id, None)
        if window is not None:
            window.close()

    def recommended_size(self):
        columns = max(1, min(self.cameras_per_row, len(self.cam_ids)))
        rows = max(1, ceil(len(self.cam_ids) / columns))
        width = max(1080, min(1820, 60 + columns * 340))
        height = max(640, min(1080, 120 + rows * 280))
        return width, height

    def _toggle_metrics_panel(self):
        if self.metrics_panel.isVisible():
            self.metrics_panel.hide()
            self.metrics_toggle_button.setText("Показать метрики")
            return

        self.metrics_panel.show()
        self.metrics_toggle_button.setText("Скрыть метрики")
        self.refresh_metrics()

    def _toggle_alerts_panel(self):
        if self.alerts_panel.isVisible():
            self.alerts_panel.hide()
            self.alerts_toggle_button.setText("Показать оповещения")
            return

        self.alerts_panel.show()
        self.alerts_toggle_button.setText("Скрыть оповещения")
        self.refresh_alerts()

    def _request_analytics(self):
        self.analytics_requested.emit()

    def _request_main_window(self):
        self.main_window_requested.emit()

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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        for cam_id in self.cam_ids:
            self._apply_frame_to_label(cam_id)

    def closeEvent(self, event):
        if self._is_closing:
            event.accept()
            return

        self._is_closing = True
        print("Window closing")
        self.timer.stop()
        self.metrics_timer.stop()
        self.alert_timer.stop()
        self.metrics_state = None
        self.roi_state = {}
        self.render_queues = {}
        self.alert_queue = None
        self.alert_decisions = None
        self.pending_alerts.clear()
        for window in list(self.alert_review_windows.values()):
            window.close()
        self.alert_review_windows.clear()
        self.closing.emit()
        event.accept()
