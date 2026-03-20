from PySide6.QtWidgets import QHeaderView, QMainWindow, QMessageBox, QVBoxLayout, QTableWidgetItem
from PySide6.QtCore import Slot

from temp.mainconfigwindow_ui import Ui_main_config_window

from cameraManagerWindow import CameraManagerWindow
from redactConfigWindow import RedactConfigWindow
from modelManagerWindow import ModelManagerWindow
# from videoWall import VideoWallExec
from tables.mytable import MyTable

from db_worker2 import DBWorker

class ConfigMainWindow(QMainWindow, Ui_main_config_window):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.db_path = "./db/logs.db"
        self.dbworker = DBWorker(self.db_path)
        self._setup_table()
        self._load_config_table()
        self.connect_signals()

    def connect_signals(self):
        self.camera_manage_button.clicked.connect(self._on_camera_manage_button_clicked)
        self.model_manage_button.clicked.connect(self._on_model_manage_button_clicked)
        self.config_table.run_videowall_requested.connect(self._run_video_wall)
    def _load_config_table(self):
        configs = self.dbworker.fetch_all_configs()
        self._display_configs(configs)
        
    def _setup_table(self):
        self.config_table = MyTable(show_videowall=True)
        self.config_table.add_requested.connect(self._on_add)
        self.config_table.edit_requested.connect(self._open_edit_window)
        self.config_table.delete_requested.connect(self._on_delete)
        temp_layout = QVBoxLayout()
        self.config_table_groupbox.setLayout(temp_layout)
        
        self.config_table_groupbox.layout().addWidget(self.config_table)
        self.config_table.table.cellDoubleClicked.connect(self._on_row_double_clicked)
        # self.config_table.set_headers()
    
    def _display_configs(self, configs):
        table = self.config_table.table
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["id", "Имя"])
        table.setRowCount(len(configs))
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        
        for row, (id, name) in enumerate(configs):
            config_id = id
            name = name
            table.setItem(row, 0, QTableWidgetItem(str(config_id)))
            table.setItem(row, 1, QTableWidgetItem(name))

    @Slot()
    def _on_row_double_clicked(self, row, column):
        table = self.config_table.table
        item: QTableWidgetItem = table.item(row, 0)
        config_id = int(item.text())

        self._open_edit_window(config_id)

    @Slot()
    def _on_camera_manage_button_clicked(self):
        self.cmw = CameraManagerWindow(self.dbworker)
        self.cmw.show()
    
    @Slot()
    def _open_edit_window(self, config_id):
        data = self.dbworker.fetch_config_by_id(config_id)
        # print(data)
        self.edit_window = RedactConfigWindow(config_id, data, self.dbworker)
        self.edit_window.config_changed.connect(self._load_config_table)
        self.edit_window.show()
    
    def _on_add(self):
        self.edit_window = RedactConfigWindow(None, None, self.dbworker)
        self.edit_window.config_changed.connect(self._load_config_table)
        self.edit_window.show()

    @Slot(int, str)
    def _on_delete(self, config_id, config_name):
        reply = QMessageBox.question(
            self,
            "Удаление",
            f"Удалить конфиг {config_name}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.dbworker.delete_config(config_id)
            self._load_config_table()
        

    def _on_model_manage_button_clicked(self):
        self.mmw = ModelManagerWindow(self.dbworker)
        self.mmw.show()

    def _run_video_wall(self, config_id):
        data = self.dbworker.fetch_config_by_id(config_id)
        # print(data)
        self.edit_window = RedactConfigWindow(config_id, data, self.dbworker)
        try:
            config = self.dbworker.fetch_config_by_id(config_id)[0]
            cameras = self.dbworker.fetch_cameras_by_id(config_id)
            classes = self.dbworker.fetch_classes_by_id(config_id)
            models = self.dbworker.get_models_by_id(classes)
            print(config)
            print(cameras)
            print(classes)
            print(models)
            self.close() 
            
            self.vw = VideoWallExec(cameras, models, config, self.db_path, classes)
            # self.vw.show()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))