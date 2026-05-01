import os
import shutil

from PySide6.QtCore import Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHeaderView,
    QMessageBox,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from ultralytics import YOLO

from gui.classDangerLevels import level_color, level_label
from gui.redactClassWindow import ClassRedactWindow
from tables.mytable import MyTable
from ui_build.modelmanagerwindow_ui import Ui_models_manager_window


class ModelManagerWindow(QWidget, Ui_models_manager_window):
    def __init__(self, dbworker):
        self.dbworker = dbworker
        self.models_by_id = {}
        super().__init__()
        self.setupUi(self)
        self.resize(860, 620)
        self.setMinimumSize(760, 540)
        self._setup_tables()
        self._connect_signals()
        self._load_data()

    def _connect_signals(self):
        self.ok_button.clicked.connect(self.close)
        self.cancel_button.clicked.connect(self.close)

    def _setup_tables(self):
        self.models_table_groupBox.setTitle("Модели")
        self.models_table = MyTable(allow_add=True, allow_edit=False, allow_delete=True)
        models_layout = QVBoxLayout()
        self.models_table.add_requested.connect(self._on_add)
        self.models_table.delete_requested.connect(self._on_delete)
        self.models_table_groupBox.setLayout(models_layout)
        self.models_table_groupBox.layout().addWidget(self.models_table)

        self.gridLayout.removeItem(self.verticalSpacer)
        self.classes_table_groupBox = QGroupBox("Загруженные классы", self)
        self.classes_table = MyTable(allow_add=False, allow_edit=True, allow_delete=False)
        classes_layout = QVBoxLayout()
        self.classes_table_groupBox.setLayout(classes_layout)
        self.classes_table_groupBox.layout().addWidget(self.classes_table)
        self.gridLayout.addWidget(self.classes_table_groupBox, 1, 0, 1, 2)

        self.classes_table.edit_requested.connect(self._open_class_edit_window)
        self.classes_table.table.cellDoubleClicked.connect(self._on_class_double_clicked)

    def _load_data(self):
        self._load_models()
        self._load_classes()

    def _load_models(self):
        models = self.dbworker.load_models()
        self.models_by_id = {model_id: path for model_id, path in models}
        self._display_models(models)

    def _load_classes(self):
        classes = self.dbworker.fetch_all_classes_with_models()
        self._display_classes(classes)

    def _display_models(self, models):
        table = self.models_table.table
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["ID", "Путь к модели"])
        table.setRowCount(len(models))

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        for row, (model_id, path) in enumerate(models):
            table.setItem(row, 0, QTableWidgetItem(str(model_id)))
            table.setItem(row, 1, QTableWidgetItem(path))

    def _display_classes(self, classes):
        table = self.classes_table.table
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "ID",
            "Класс",
            "Модель",
            "Уровень опасности",
            "Оповещение",
            "Задержка, сек",
        ])
        table.setRowCount(len(classes))

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        for row, (class_id, name, model_id, danger_level, alert_enabled, alert_delay_sec, model_path) in enumerate(classes):
            table.setItem(row, 0, QTableWidgetItem(str(class_id)))
            table.setItem(row, 1, QTableWidgetItem(name))
            table.setItem(row, 2, QTableWidgetItem(model_path or f"Model {model_id}"))

            level_item = QTableWidgetItem(level_label(danger_level))
            color = QColor(level_color(danger_level))
            level_item.setBackground(color)
            text_color = QColor("black") if color.lightness() > 150 else QColor("white")
            level_item.setForeground(text_color)
            table.setItem(row, 3, level_item)
            table.setItem(row, 4, QTableWidgetItem("Да" if alert_enabled else "Нет"))
            table.setItem(row, 5, QTableWidgetItem(f"{float(alert_delay_sec):.1f}"))

    def _on_add(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выбрать модель",
            "",
            "Model files (*.pt *.onnx *.engine)",
        )

        if not file_path:
            return

        weights_dir = "./weights"
        os.makedirs(weights_dir, exist_ok=True)

        filename = os.path.basename(file_path)
        new_path = os.path.join(weights_dir, filename)

        if os.path.exists(new_path):
            QMessageBox.warning(self, "Ошибка", "Файл уже существует")
            return

        try:
            shutil.copy(file_path, new_path)
            model_id = self.dbworker.add_model(new_path.split("\\")[-1])

            classes = self._extract_classes(new_path)
            for name in classes:
                self.dbworker.add_class(name, model_id)
        except Exception as exc:
            self.dbworker.conn.rollback()
            QMessageBox.critical(self, "Ошибка", str(exc))
            return

        self._load_data()

    def _on_delete(self, model_id, model_name):
        reply = QMessageBox.question(
            self,
            "Удаление",
            f"Удалить модель {model_name}?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        try:
            self.dbworker.cur.execute(
                "SELECT model_path FROM models WHERE id = ?",
                (model_id,),
            )
            result = self.dbworker.cur.fetchone()

            if not result:
                raise Exception("Модель не найдена в БД")

            file_name = result[0]
            file_path = os.path.join(".", "weights", file_name)

            if os.path.exists(file_path):
                os.remove(file_path)

            self.dbworker.delete_model(model_id)
            self._load_data()
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", str(exc))

    def _extract_classes(self, model_path):
        model = YOLO(model_path)
        names = model.names
        return list(names.values())

    @Slot(int)
    def _open_class_edit_window(self, class_id):
        data = self.dbworker.fetch_class_by_id(class_id)
        self.class_edit_window = ClassRedactWindow(class_id, data, self.dbworker)
        self.class_edit_window.class_changed.connect(self._load_classes)
        self.class_edit_window.show()

    @Slot(int, int)
    def _on_class_double_clicked(self, row, column):
        table = self.classes_table.table
        item = table.item(row, 0)
        class_id = int(item.text())
        self._open_class_edit_window(class_id)
