from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QMenu, QMessageBox, QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout
from PySide6.QtCore import Signal, Qt


class MyTable(QWidget):
    add_requested = Signal()
    edit_requested = Signal(int)
    delete_requested = Signal(int, str)
    run_videowall_requested = Signal(int)
    def __init__(self, show_videowall = False):
        super().__init__()
        self.show_videowall = show_videowall
        self.table = QTableWidget()
        self.initialize_table()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.layout().addWidget(self.table)
    
    def initialize_table(self):
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
    def show_context_menu(self, pos):
        menu = QMenu(self)

        add_action = menu.addAction("Добавить")
        edit_action = menu.addAction("Редактировать")
        delete_action = menu.addAction("Удалить")
        
        row = self.table.rowAt(pos.y())

        if row >= 0:
            self.table.selectRow(row)

        if row < 0:
            edit_action.setVisible(False)
            delete_action.setVisible(False)
        edit_action.setEnabled(row >= 0)
        delete_action.setEnabled(row >= 0)
        

        if self.show_videowall:
            run_action = menu.addAction("Запустить видеостену")
            run_action.setEnabled(row >= 0)
        else:
            run_action = None
        action = menu.exec(self.table.mapToGlobal(pos))
        if action == add_action:
            self.add_requested.emit()

        elif action == edit_action and row >= 0:
            config_id = int(self.table.item(row, 0).text())
            
            self.edit_requested.emit(config_id)

        elif action == delete_action and row >= 0:
            config_id = int(self.table.item(row, 0).text())
            config_name = self.table.item(row, 1).text()
            self.delete_requested.emit(config_id, config_name)
        elif run_action is not None and action == run_action and row >= 0:
            config_id = int(self.table.item(row, 0).text())
            self.run_videowall_requested.emit(config_id)