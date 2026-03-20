from PySide6.QtWidgets import QListWidgetItem, QWidget
from PySide6.QtCore import Qt, Slot, Signal

from temp.redactconfigwindow_ui import Ui_redact_config_window

class RedactConfigWindow(QWidget, Ui_redact_config_window):
    config_changed =  Signal()
    config_loaded = Signal(object)

    move_to_active_cameras = Signal()
    move_to_inactive_cameras = Signal()
    move_to_active_classes = Signal()
    move_to_inactive_classes = Signal()
    def __init__(self, config_id, data, dbworker):
        
        super().__init__()
        self.setupUi(self)
        self.config_id = config_id
        self.dbworker = dbworker
        self.connect_signals()
        self._load_data_from_config(data)

    def connect_signals(self):
        self.config_loaded.connect(self._load_data_from_config)
        self.ok_button.clicked.connect(self._confirm_edit)
        self.cancel_button.clicked.connect(self._close_window)
        self.transfer_selected_cameras_right.clicked.connect(self._move_cameras_to_active)
        self.transfer_selected_cameras_left.clicked.connect(self._move_cameras_to_inactive)
        self.transfer_selected_classes_right.clicked.connect(self._move_classes_to_inactive)
        self.transfer_selected_classes_left.clicked.connect(self._move_classes_to_active)
    
    def get_data_by_config_id(self):
        config = self.dbworker.get_config_by_id(self.config_id)
        self.config_loaded.emit(config)
    
    @Slot(object)
    def _load_data_from_config(self, config):
        """
        set the values for the line_edits, etc.
        """
        if config is not None:
            _, name, cpr, enabled, conf_thresh, fps = config[0]
        else:
            _, name, cpr, enabled, conf_thresh, fps = (0, "", 2, 1, 0.7, 24)
        self.config_name_lineEdit.setText(name)
        self.cameras_per_row_lineEdit.setText(str(cpr))
        self.enable_processing_checkBox.setChecked(bool(enabled))
        self.conf_thres_spinbox.setValue(conf_thresh)
        self.fps_lineEdit.setText(str(fps))
        self._load_cameras_by_id(self.config_id)
        self._load_classes_by_id(self.config_id)

    def _confirm_edit(self):
        """
        commit the changes to the database, close the window, emit the changed_signal
        """
        name = self.config_name_lineEdit.text()
        cpr = int(self.cameras_per_row_lineEdit.text())
        enabled = int(self.enable_processing_checkBox.isChecked())
        conf_thres = round(self.conf_thres_spinbox.value(), 2)
        fps = int(self.fps_lineEdit.text())
        data = {
            "name": name,
            "cameras_per_row": cpr,
            "enabled": enabled,
            "conf_thres": conf_thres,
            "fps": fps
        }
        if self.config_id is None:
            self.dbworker.add_config(data)
        else:
            self.dbworker.edit_config(self.config_id, data)

        self._save_cameras()
        self._save_classes()

        self.config_changed.emit()
        self.close()

    def _save_cameras(self):
        cam_ids = self._get_ids_from_list(self.active_cameras_listWidget)

        self.dbworker.clear_config_cameras(self.config_id)
        
        for cam_id in cam_ids:
            self.dbworker.add_camera_to_config(self.config_id, cam_id)

    def _save_classes(self):
        cls_ids = self._get_ids_from_list(self.active_classes_listWidget)

        self.dbworker.clear_config_classes(self.config_id)
        
        for cls_id in cls_ids:
            self.dbworker.add_class_to_config(self.config_id, cls_id)

    def _load_cameras_by_id(self, config_id):
        active_cameras = self.dbworker.fetch_cameras_by_id(config_id)
        all_cameras = self.dbworker.get_all_cameras()
        active_ids = {cam[0] for cam in active_cameras}
        self.active_cameras_listWidget.clear()
        self.inactive_cameras_listWidget.clear()
        for cam_id, name in all_cameras:
            if cam_id in active_ids:
                self._add_item(self.active_cameras_listWidget, cam_id, name)
            else:
                self._add_item(self.inactive_cameras_listWidget, cam_id, name)

    def _load_classes_by_id(self, config_id):
        active_classes = self.dbworker.fetch_classes_by_id(config_id)
        all_classes = self.dbworker.get_all_classes()
        active_ids = {cls[0] for cls in active_classes}
        self.active_classes_listWidget.clear()
        self.inactive_classes_listWidget.clear()
        self.active_models = set()
        for cls_id, name, model_id in all_classes:
            if cls_id in active_ids:
                self._add_item(self.active_classes_listWidget, cls_id, name)
            else:
                self._add_item(self.inactive_classes_listWidget, cls_id, name)

    def _add_item(self, list_widget, id, name):
        item = QListWidgetItem(name)
        item.setData(Qt.UserRole, id)
        list_widget.addItem(item)

    def _move_items(self, source, target):
        for item in source.selectedItems():
            source.takeItem(source.row(item))
            target.addItem(item)

    def _move_cameras_to_active(self):
        self._move_items(self.inactive_cameras_listWidget, self.active_cameras_listWidget)
    
    def _move_cameras_to_inactive(self):
        self._move_items(self.active_cameras_listWidget, self.inactive_cameras_listWidget)
    
    def _move_classes_to_active(self):
        self._move_items(self.inactive_classes_listWidget, self.active_classes_listWidget)
    
    def _move_classes_to_inactive(self):
        self._move_items(self.active_classes_listWidget, self.inactive_classes_listWidget)
    
    def _get_ids_from_list(self, list_widget):
        ids = []
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            ids.append(item.data(Qt.UserRole))
        return ids

    @Slot()
    def _close_window(self):
        self.close()
        