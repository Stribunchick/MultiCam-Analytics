from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gui.classDangerLevels import LEVEL_OPTIONS, level_color, level_label, normalize_level


class ClassRedactWindow(QWidget):
    class_changed = Signal()

    def __init__(self, class_id, data, dbworker):
        super().__init__()
        self.dbworker = dbworker
        self.class_id = class_id

        self._setup_ui()
        self._connect_signals()
        self._load_data_from_class(data)

    def _setup_ui(self):
        self.setWindowTitle("Редактирование класса")
        self.resize(420, 320)

        root = QVBoxLayout(self)

        class_group_box = QGroupBox("Параметры класса")
        class_form = QFormLayout(class_group_box)

        self.class_name_line_edit = QLineEdit()
        class_form.addRow("Название класса", self.class_name_line_edit)

        self.model_value_label = QLabel("-")
        class_form.addRow("Модель", self.model_value_label)

        self.danger_level_combo = QComboBox()
        for level_key, label, _ in LEVEL_OPTIONS:
            self.danger_level_combo.addItem(label, level_key)
        class_form.addRow("Уровень опасности", self.danger_level_combo)

        self.level_preview = QLabel()
        self.level_preview.setMinimumHeight(32)
        self.level_preview.setStyleSheet("border-radius: 6px; padding: 6px 10px;")
        class_form.addRow("Цвет", self.level_preview)
        root.addWidget(class_group_box)

        alert_group_box = QGroupBox("Реакция на событие")
        alert_form = QFormLayout(alert_group_box)

        self.alert_enabled_checkbox = QCheckBox("Включить оповещение для этого класса")
        alert_form.addRow(self.alert_enabled_checkbox)

        self.alert_delay_spinbox = QDoubleSpinBox()
        self.alert_delay_spinbox.setDecimals(1)
        self.alert_delay_spinbox.setRange(0.0, 600.0)
        self.alert_delay_spinbox.setSingleStep(0.5)
        self.alert_delay_spinbox.setSuffix(" сек")
        alert_form.addRow("Задержка до оповещения", self.alert_delay_spinbox)

        self.alert_hint_label = QLabel(
            "0 сек означает мгновенное оповещение после появления объекта."
        )
        self.alert_hint_label.setWordWrap(True)
        alert_form.addRow(self.alert_hint_label)
        root.addWidget(alert_group_box)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        self.ok_button = QPushButton("Ок")
        self.cancel_button = QPushButton("Отмена")
        buttons_layout.addWidget(self.ok_button)
        buttons_layout.addWidget(self.cancel_button)
        root.addLayout(buttons_layout)

    def _connect_signals(self):
        self.ok_button.clicked.connect(self._confirm_edit)
        self.cancel_button.clicked.connect(self.close)
        self.danger_level_combo.currentIndexChanged.connect(self._update_level_preview)
        self.alert_enabled_checkbox.toggled.connect(self._update_alert_controls)

    def _load_data_from_class(self, data):
        if data is not None:
            _, name, model_id, danger_level, alert_enabled, alert_delay_sec = data[0]
        else:
            _, name, model_id, danger_level, alert_enabled, alert_delay_sec = (
                0,
                "",
                None,
                "safe",
                1,
                0.0,
            )

        self.class_name_line_edit.setText(name)
        self.model_value_label.setText(str(model_id) if model_id is not None else "-")

        normalized_level = normalize_level(danger_level)
        index = self.danger_level_combo.findData(normalized_level)
        if index < 0:
            index = 0
        self.danger_level_combo.setCurrentIndex(index)

        self.alert_enabled_checkbox.setChecked(bool(alert_enabled))
        self.alert_delay_spinbox.setValue(float(alert_delay_sec))
        self._update_level_preview()
        self._update_alert_controls()

    def _update_level_preview(self):
        level_key = self.danger_level_combo.currentData()
        color = level_color(level_key)
        label = level_label(level_key)
        self.level_preview.setText(label)
        self.level_preview.setStyleSheet(
            f"background-color: {color}; color: white; border-radius: 6px; padding: 6px 10px;"
        )

    def _update_alert_controls(self):
        enabled = self.alert_enabled_checkbox.isChecked()
        self.alert_delay_spinbox.setEnabled(enabled)
        self.alert_hint_label.setEnabled(enabled)

    def _confirm_edit(self):
        data = {
            "name": self.class_name_line_edit.text(),
            "danger_level": normalize_level(self.danger_level_combo.currentData()),
            "alert_enabled": self.alert_enabled_checkbox.isChecked(),
            "alert_delay_sec": round(self.alert_delay_spinbox.value(), 1),
        }
        self.dbworker.edit_class(self.class_id, data)
        self.class_changed.emit()
        self.close()
