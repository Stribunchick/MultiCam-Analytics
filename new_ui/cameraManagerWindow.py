from PySide6.QtWidgets import QHeaderView, QMessageBox, QTableWidgetItem, QVBoxLayout, QWidget
from PySide6.QtCore import Slot, Signal
from temp.cameramanagerwindow_ui import Ui_camera_manager_window
from redactCameraWindow import CameraRedactWindow

from tables.mytable import MyTable

class CameraManagerWindow(QWidget, Ui_camera_manager_window):
    def __init__(self, dbworker):
        super().__init__()
        self.setupUi(self)
        self.cameras_table = MyTable()

        self.dbworker = dbworker
        self._setup_table()
        self._load_camera_table()
        self.connect_signals()
    
    def connect_signals(self):
        self.ok_button.clicked.connect(self.close)
        self.cancel_button.clicked.connect(self.close)

    def _setup_table(self):
        self.cameras_table = MyTable()
        temp_layout = QVBoxLayout()
        self.cameras_table.add_requested.connect(self._on_add)
        self.cameras_table.edit_requested.connect(self._open_edit_window)
        self.cameras_table.delete_requested.connect(self._on_delete)
        self.camera_list_groupBox.setLayout(temp_layout)
        self.camera_list_groupBox.layout().addWidget(self.cameras_table)
        
        self.camera_list_groupBox.layout().addWidget(self.cameras_table)
        self.cameras_table.table.cellDoubleClicked.connect(self._on_row_double_clicked)
    
    def _load_camera_table(self):
        cameras = self.dbworker.get_all_cameras()
        self._display_cameras(cameras)

    def _display_cameras(self, cameras):
        table = self.cameras_table.table
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["id", "Имя"])
        table.setRowCount(len(cameras))
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        
        for row, (id, name) in enumerate(cameras):
            camera_id = id
            name = name
            table.setItem(row, 0, QTableWidgetItem(str(camera_id)))
            table.setItem(row, 1, QTableWidgetItem(name))

    @Slot()
    def _open_edit_window(self, camera_id):
        data = self.dbworker.fetch_camera_by_id(camera_id)
        # print(data)
        self.edit_window = CameraRedactWindow(camera_id, data, self.dbworker)
        self.edit_window.camera_changed.connect(self._load_camera_table)
        self.edit_window.show()
    
    def _on_add(self):
        self.edit_window = CameraRedactWindow(None, None, self.dbworker)
        self.edit_window.camera_changed.connect(self._load_camera_table)
        self.edit_window.show()

    @Slot(int, str)
    def _on_delete(self, camera_id, camera_name):
        reply = QMessageBox.question(
            self,
            "Удаление",
            f"Удалить камеру {camera_name}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.dbworker.delete_camera(camera_id)
            self._load_camera_table()
    @Slot()
    def _on_row_double_clicked(self, row, column):
        table = self.cameras_table.table
        item: QTableWidgetItem = table.item(row, 0)
        config_id = int(item.text())

        self._open_edit_window(config_id)