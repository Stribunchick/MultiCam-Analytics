from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Slot, Signal

from temp.redactcamerawindow_ui import Ui_camera_redact_window

class CameraRedactWindow(QWidget, Ui_camera_redact_window):

    camera_changed = Signal()
    def __init__(self, camera_id, data, dbworker):
        super().__init__()
        self.setupUi(self)

        self.dbworker = dbworker
        self.camera_id = camera_id

        self.connect_signals()
        self._load_data_from_camera(data)
    
    def connect_signals(self):
        self.ok_button.clicked.connect(self._confirm_edit)
        self.cancel_button.clicked.connect(self.close)

    def _load_data_from_camera(self, data):
        if data is not None:
            _, name, location, username, password, ip = data[0]
        else:
            _, name, location, username, password, ip = (0, "", "", "", "", "")
        self.camera_name_lineEdit.setText(name)
        self.location_lineEdit.setText(location)
        self.username_lineEdit.setText(username)
        self.password_lineEdit.setText(password)
        self.ip_lineEdit.setText(ip)

    def _confirm_edit(self):
        name = self.camera_name_lineEdit.text()
        location = self.location_lineEdit.text()
        username = self.username_lineEdit.text()
        password = self.password_lineEdit.text()
        ip = self.ip_lineEdit.text()
        data = {
            "name": name,
            "location": location,
            "username": username,
            "password": password,
            "ip": ip
        }
        if self.camera_id is None:
            self.dbworker.add_camera(data)
        else:
            self.dbworker.edit_camera(self.camera_id, data)

        self.camera_changed.emit()
        self.close()
