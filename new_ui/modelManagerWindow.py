from PySide6.QtWidgets import QFileDialog, QHeaderView, QMessageBox, QTableWidgetItem, QVBoxLayout, QWidget
from PySide6.QtCore import Slot, Signal
import os
import shutil

from ultralytics import YOLO

from temp.modelmanagerwindow_ui import Ui_models_manager_window
from tables.mytable import MyTable

class ModelManagerWindow(QWidget, Ui_models_manager_window):
    def __init__(self, dbworker):
        self.dbworker = dbworker
        super().__init__()
        self.setupUi(self)
        self._setup_table()
        self._connect_signals()
        self._load_models()
    
    def _connect_signals(self):
        self.ok_button.clicked.connect(self.close)
        self.cancel_button.clicked.connect(self.close)

    def _setup_table(self):
        self.models_table = MyTable()
        temp_layout = QVBoxLayout()
        self.models_table.add_requested.connect(self._on_add)
        self.models_table.delete_requested.connect(self._on_delete)
        self.models_table_groupBox.setLayout(temp_layout)
        self.models_table_groupBox.layout().addWidget(self.models_table)
    
    def _load_models(self):
        models = self.dbworker.load_models()
        self._display_models(models)

    def _display_models(self, models):
        table = self.models_table.table

        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["ID", "Path"])
        table.setRowCount(len(models))

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        for row, (model_id, path) in enumerate(models):
            table.setItem(row, 0, QTableWidgetItem(str(model_id)))
            table.setItem(row, 1, QTableWidgetItem(path))
    
    def _on_add(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выбрать модель",
            "",
            "Model files (*.pt *.onnx *.engine)"
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

            # ТРАНЗАКЦИЯ

            model_id = self.dbworker.add_model(new_path)

            classes = self._extract_classes(new_path)

            for name in classes:
                self.dbworker.add_class(name, model_id)


        except Exception as e:
            self.dbworker.conn.rollback()
            QMessageBox.critical(self, "Ошибка", str(e))
            return

        self._load_models()

    def _on_delete(self, model_id, model_name):
        """
        Удалить модель: файл + БД + связи
        """
        reply = QMessageBox.question(
            self,
            "Удаление",
            f"Удалить модель {model_name}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        try:
            self.dbworker.cur.execute(
                "SELECT model_path FROM models WHERE id = ?",
                (model_id,)
            )
            result = self.dbworker.cur.fetchone()

            if not result:
                raise Exception("Модель не найдена в БД")

            file_path = result[0]

            if os.path.exists(file_path):
                os.remove(file_path)
            else:
                print(f"Файл не найден: {file_path}")

            self.dbworker.delete_model(model_id)

            self._load_models()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def _extract_classes(self, mp):
        model = YOLO(mp)
        names = model.names
        clss = list(names.values())
        print(clss)
        return clss
    