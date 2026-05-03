from PySide6.QtCore import QTimer, Slot
from PySide6.QtWidgets import (
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidgetItem,
    QVBoxLayout,
)

from gui.cameraManagerWindow import CameraManagerWindow
from gui.dashboardWindow import DashboardWindow
from gui.db_worker import DBWorker
from gui.modelManagerWindow import ModelManagerWindow
from gui.redactConfigWindow import RedactConfigWindow
from tables.mytable import MyTable
from ui_build.mainconfigwindow_ui import Ui_main_config_window
from videoWall import VideoWallExec


class ConfigMainWindow(QMainWindow, Ui_main_config_window):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setMinimumSize(760, 520)
        self.db_path = "./db/logs.db"
        self.dbworker = DBWorker(self.db_path)
        self.vw = None
        self._allow_close = False
        self._pending_app_exit = False
        self._shutdown_poll_timer = QTimer(self)
        self._shutdown_poll_timer.setInterval(150)
        self._shutdown_poll_timer.timeout.connect(self._poll_videowall_shutdown)

        self._setup_header()
        self._setup_dashboard_button()
        self._setup_table()
        self._load_config_table()
        self.connect_signals()

    def _setup_header(self):
        self.title_label = QLabel("MultiCam Analytics")
        self.title_label.setObjectName("pageTitle")
        self.subtitle_label = QLabel("Конфигурации камер, моделей и запуск видеостены")
        self.subtitle_label.setObjectName("pageSubtitle")
        self.verticalLayout.insertWidget(0, self.subtitle_label)
        self.verticalLayout.insertWidget(0, self.title_label)

    def connect_signals(self):
        self.camera_manage_button.clicked.connect(self._on_camera_manage_button_clicked)
        self.model_manage_button.clicked.connect(self._on_model_manage_button_clicked)
        self.dashboard_button.clicked.connect(self._on_dashboard_button_clicked)
        self.config_table.run_videowall_requested.connect(self._run_video_wall)

    def _setup_dashboard_button(self):
        self.dashboard_button = QPushButton("Аналитика")
        for button in (self.camera_manage_button, self.model_manage_button):
            button.setProperty("variant", "secondary")
            button.style().unpolish(button)
            button.style().polish(button)
        self.buttons_groupBox.layout().addWidget(self.dashboard_button)

    def _load_config_table(self):
        configs = self.dbworker.fetch_all_configs()
        self._display_configs(configs)

    def _setup_table(self):
        self.config_table = MyTable(show_videowall=True)
        self.config_table.add_requested.connect(self._on_add)
        self.config_table.edit_requested.connect(self._open_edit_window)
        self.config_table.delete_requested.connect(self._on_delete)

        temp_layout = QVBoxLayout()
        temp_layout.setContentsMargins(0, 0, 0, 0)
        self.config_table_groupbox.setLayout(temp_layout)
        self.config_table_groupbox.layout().addWidget(self.config_table)
        self.config_table.table.cellDoubleClicked.connect(self._on_row_double_clicked)

    def _display_configs(self, configs):
        table = self.config_table.table
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["id", "Имя"])
        table.setRowCount(len(configs))
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        for row, (config_id, name) in enumerate(configs):
            table.setItem(row, 0, QTableWidgetItem(str(config_id)))
            table.setItem(row, 1, QTableWidgetItem(name))

    @Slot()
    def _on_row_double_clicked(self, row, column):
        del column
        table = self.config_table.table
        item = table.item(row, 0)
        if item is None:
            return
        self._open_edit_window(int(item.text()))

    @Slot()
    def _on_camera_manage_button_clicked(self):
        self.cmw = CameraManagerWindow(self.dbworker)
        self.cmw.show()

    @Slot()
    def _open_edit_window(self, config_id):
        data = self.dbworker.fetch_config_by_id(config_id)
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
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        try:
            self.dbworker.delete_config(config_id)
            self._load_config_table()
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка удаления", str(exc))

    def _on_model_manage_button_clicked(self):
        self.mmw = ModelManagerWindow(self.dbworker)
        self.mmw.show()

    def _on_dashboard_button_clicked(self):
        self.dashboard_window = DashboardWindow(self.dbworker)
        self.dashboard_window.show()

    def _run_video_wall(self, config_id):
        try:
            self._pending_app_exit = False
            config = self.dbworker.fetch_config_by_id(config_id)[0]
            cameras = self.dbworker.fetch_cameras_by_id(config_id)
            classes = self.dbworker.fetch_classes_by_id(config_id)
            models = self.dbworker.get_models_by_id(classes)

            cameras_data = []
            for camera in cameras:
                cam_id, name, location, username, pwd, ip = camera
                cameras_data.append(
                    {
                        "id": cam_id,
                        "name": name,
                        "location": location,
                        "username": username,
                        "pwd": pwd,
                        "ip": ip,
                    }
                )

            self.hide()
            self.vw = VideoWallExec(
                cameras_data,
                models,
                config,
                self.db_path,
                classes,
                main_window=self,
            )
            self.vw.start_videowall()
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", str(exc))

    def _poll_videowall_shutdown(self):
        if self.vw is None or self.vw.is_shutdown_complete():
            self._shutdown_poll_timer.stop()
            self.vw = None
            if self._pending_app_exit:
                self._allow_close = True
                self.close()

    def closeEvent(self, event):
        if self._allow_close:
            event.accept()
            return

        if self.vw is not None and not self.vw.is_shutdown_complete():
            self._pending_app_exit = True
            self.hide()
            self.vw.request_shutdown()
            if not self._shutdown_poll_timer.isActive():
                self._shutdown_poll_timer.start()
            event.ignore()
            return

        event.accept()
