import os
from datetime import datetime

from PySide6.QtCore import QDateTime, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateTimeEdit,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from gui.classDangerLevels import level_color


class BarChartWidget(QWidget):
    def __init__(self, title):
        super().__init__()
        self.title = title
        self.data = {}
        self.setMinimumHeight(220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_data(self, data):
        self.data = dict(sorted(data.items(), key=lambda item: item[1], reverse=True))
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(36, 50, 68)))
        painter.setBrush(QColor(17, 24, 39))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 8, 8)

        left = 18
        top = 16
        right = self.width() - 18

        painter.setPen(QPen(QColor(241, 245, 249)))
        painter.drawText(left, top, right - left, 24, Qt.AlignmentFlag.AlignLeft, self.title)

        if not self.data:
            painter.setPen(QPen(QColor(148, 163, 184)))
            painter.drawText(
                left,
                top + 48,
                right - left,
                24,
                Qt.AlignmentFlag.AlignCenter,
                "Нет данных",
            )
            painter.end()
            return

        max_value = max(self.data.values()) or 1
        chart_top = top + 40
        row_height = 30
        bar_left = left + 150
        bar_max_width = max(40, right - bar_left - 40)

        colors = [
            QColor(37, 99, 235),
            QColor(15, 118, 110),
            QColor(217, 119, 6),
            QColor(124, 58, 237),
            QColor(220, 38, 38),
        ]

        for idx, (label, value) in enumerate(list(self.data.items())[:5]):
            y = chart_top + idx * row_height
            painter.setPen(QPen(QColor(226, 232, 240)))
            text = str(label)
            if len(text) > 18:
                text = text[:17] + "..."
            painter.drawText(left, y, 125, 20, Qt.AlignmentFlag.AlignLeft, text)

            width = int((value / max_value) * bar_max_width)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(colors[idx % len(colors)])
            painter.drawRoundedRect(bar_left, y + 2, width, 16, 4, 4)
            painter.setPen(QPen(QColor(203, 213, 225)))
            painter.drawText(bar_left + width + 8, y, 36, 20, Qt.AlignmentFlag.AlignLeft, str(value))

        painter.end()


class EventSnapshotWindow(QWidget):
    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path

        self.setWindowTitle(f"Кадр события - {os.path.basename(image_path)}")
        self.resize(960, 640)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        path_label = QLabel(image_path)
        path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        root.addWidget(path_label)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.image_label)
        root.addWidget(scroll_area, 1)

        self._load_image()

    def _load_image(self):
        pixmap = QPixmap(self.image_path)
        if pixmap.isNull():
            self.image_label.setText("Не удалось открыть изображение.")
            return

        self.image_label.setPixmap(pixmap)
        self.image_label.adjustSize()


class DashboardWindow(QWidget):
    def __init__(self, dbworker):
        super().__init__()
        self.dbworker = dbworker
        self.snapshot_windows = []
        self.setWindowTitle("Аналитический дашборд")
        self.resize(980, 680)
        self.setMinimumSize(900, 620)

        self._setup_ui()
        self.class_danger_levels = {}
        self._load_filter_values()
        self.refresh()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        title = QLabel("Аналитический дашборд")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Сводка событий, активность камер и история обнаружений")
        subtitle.setObjectName("pageSubtitle")
        root.addWidget(title)
        root.addWidget(subtitle)

        filters_box = QGroupBox("Фильтры")
        filters = QHBoxLayout(filters_box)
        filters.setSpacing(8)

        self.start_filter = QDateTimeEdit()
        self.start_filter.setCalendarPopup(True)
        self.start_filter.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.start_filter.setDateTime(QDateTime.currentDateTime().addDays(-7))

        self.end_filter = QDateTimeEdit()
        self.end_filter.setCalendarPopup(True)
        self.end_filter.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.end_filter.setDateTime(QDateTime.currentDateTime())

        self.camera_filter = QComboBox()
        self.event_filter = QComboBox()

        refresh_button = QPushButton("Обновить")
        refresh_button.clicked.connect(self.refresh)

        filters.addWidget(QLabel("С"))
        filters.addWidget(self.start_filter)
        filters.addWidget(QLabel("По"))
        filters.addWidget(self.end_filter)
        filters.addWidget(QLabel("Камера"))
        filters.addWidget(self.camera_filter)
        filters.addWidget(QLabel("Событие"))
        filters.addWidget(self.event_filter)
        filters.addWidget(refresh_button)

        root.addWidget(filters_box)

        stats_grid = QGridLayout()
        stats_grid.setSpacing(12)
        self.total_label = self._metric_label("0", "Всего событий")
        self.active_label = self._metric_label("0", "Активные")
        self.finished_label = self._metric_label("0", "Завершенные")
        self.avg_duration_label = self._metric_label("0 сек", "Средняя длительность")

        stats_grid.addWidget(self.total_label, 0, 0)
        stats_grid.addWidget(self.active_label, 0, 1)
        stats_grid.addWidget(self.finished_label, 0, 2)
        stats_grid.addWidget(self.avg_duration_label, 0, 3)
        root.addLayout(stats_grid)

        charts = QHBoxLayout()
        charts.setSpacing(12)
        self.type_chart = BarChartWidget("События по типам")
        self.camera_chart = BarChartWidget("События по камерам")
        charts.addWidget(self.type_chart)
        charts.addWidget(self.camera_chart)
        root.addLayout(charts)

        self.events_table = QTableWidget()
        self.events_table.setColumnCount(8)
        self.events_table.setHorizontalHeaderLabels([
            "ID",
            "Камера",
            "Локация",
            "Начало",
            "Окончание",
            "Тип",
            "Источник",
            "Длительность",
        ])
        self.events_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.events_table.horizontalHeader().setStretchLastSection(True)
        self.events_table.cellClicked.connect(self._open_snapshot_from_row)
        root.addWidget(self.events_table)

    def _metric_label(self, value, caption):
        label = QLabel(f"<b>{value}</b><br>{caption}")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setMinimumHeight(72)
        label.setProperty("metric", True)
        label.style().unpolish(label)
        label.style().polish(label)
        return label

    def _load_filter_values(self):
        self.camera_filter.clear()
        self.camera_filter.addItem("Все камеры", None)
        for cam_id, name in self.dbworker.get_all_cameras():
            self.camera_filter.addItem(name, cam_id)

        self.event_filter.clear()
        self.event_filter.addItem("Все события", None)
        for event_type in self.dbworker.fetch_event_types_for_dashboard():
            self.event_filter.addItem(event_type, event_type)

    def refresh(self):
        start_dt = self.start_filter.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        end_dt = self.end_filter.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        camera_id = self.camera_filter.currentData()
        event_type = self.event_filter.currentData()

        snapshot = self.dbworker.fetch_dashboard_snapshot(
            start_dt=start_dt,
            end_dt=end_dt,
            camera_id=camera_id,
            event_type=event_type,
        )
        self.class_danger_levels = self.dbworker.fetch_class_danger_levels()
        events = self.dbworker.fetch_dashboard_events(
            start_dt=start_dt,
            end_dt=end_dt,
            camera_id=camera_id,
            event_type=event_type,
            limit=500,
        )

        self.total_label.setText(f"<b>{snapshot['total']}</b><br>Всего событий")
        self.active_label.setText(f"<b>{snapshot['active']}</b><br>Активные")
        self.finished_label.setText(f"<b>{snapshot['finished']}</b><br>Завершенные")
        self.avg_duration_label.setText(
            f"<b>{self._format_duration(snapshot['avg_duration'])}</b><br>Средняя длительность"
        )

        self.type_chart.set_data(snapshot["by_type"])
        self.camera_chart.set_data(snapshot["by_camera"])
        self._fill_events_table(events)

    def _fill_events_table(self, events):
        self.events_table.setRowCount(len(events))

        for row, event in enumerate(events):
            log_id, _, camera_name, location, start, stop, event_type, src, snapshot_path = event
            values = [
                log_id,
                camera_name,
                location,
                start,
                stop or "",
                event_type,
                src,
                self._duration_from_strings(start, stop),
            ]

            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value or ""))
                item.setData(Qt.ItemDataRole.UserRole, snapshot_path)
                if snapshot_path:
                    item.setToolTip("Нажмите, чтобы открыть сохраненный кадр события")
                if col == 5 and value:
                    self._apply_event_level_style(item, str(value))
                self.events_table.setItem(row, col, item)

        self.events_table.resizeColumnsToContents()

    def _apply_event_level_style(self, item, event_type):
        danger_level = self.class_danger_levels.get(event_type)
        if not danger_level:
            return

        background = QColor(level_color(danger_level))
        foreground = QColor("black") if background.lightness() > 150 else QColor("white")
        item.setBackground(background)
        item.setForeground(foreground)

    def _open_snapshot_from_row(self, row, column):
        item = self.events_table.item(row, 0)
        if item is None:
            return

        snapshot_path = item.data(Qt.ItemDataRole.UserRole)
        if not snapshot_path:
            return

        if not os.path.exists(snapshot_path):
            QMessageBox.warning(
                self,
                "Кадр не найден",
                f"Файл снимка не найден:\n{snapshot_path}",
            )
            return

        window = EventSnapshotWindow(snapshot_path)
        window.destroyed.connect(lambda *_: self._forget_snapshot_window(window))
        self.snapshot_windows.append(window)
        window.show()

    def _forget_snapshot_window(self, window):
        if window in self.snapshot_windows:
            self.snapshot_windows.remove(window)

    def _duration_from_strings(self, start, stop):
        if not stop:
            return "активно"

        start_dt = self._parse_log_datetime(start)
        stop_dt = self._parse_log_datetime(stop)
        if start_dt is None or stop_dt is None:
            return ""

        return self._format_duration(max(0.0, (stop_dt - start_dt).total_seconds()))

    @staticmethod
    def _format_duration(seconds):
        seconds = int(round(seconds))
        minutes, sec = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)

        if hours:
            return f"{hours} ч {minutes} мин"
        if minutes:
            return f"{minutes} мин {sec} сек"
        return f"{sec} сек"

    @staticmethod
    def _parse_log_datetime(value):
        if not value:
            return None

        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
